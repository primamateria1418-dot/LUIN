/*
 * LUIN API Client — Fetch wrapper for all backend endpoints
 */

const API_BASE = window.LUIN_API_URL || 'http://localhost:8000/api/v1';

let _token = localStorage.getItem('luin_token');
let _clientId = localStorage.getItem('luin_client_id');
let _clientName = localStorage.getItem('luin_client_name');
let _clientPlan = localStorage.getItem('luin_client_plan') || 'Growth';

function getToken() { return _token; }
function getClientId() { return _clientId; }

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (_token) headers['Authorization'] = `Bearer ${_token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) { logout(); throw new Error('Auth expired'); }
  return res.json();
}

/* ── Auth ── */
async function requestMagicLink(email) {
  return api('/auth/magic-link', { method: 'POST', body: JSON.stringify({ email }) });
}

async function exchangeToken(code) {
  const data = new URLSearchParams();
  data.append('code', code);
  data.append('code_verifier', localStorage.getItem('luin_verifier') || '');
  const res = await fetch(`${API_BASE}/auth/token`, { method: 'POST', body: data });
  return res.json();
}

async function getUserProfile() { return api('/auth/me'); }

async function logout() {
  localStorage.removeItem('luin_token');
  localStorage.removeItem('luin_client_id');
  localStorage.removeItem('luin_client_name');
  localStorage.removeItem('luin_client_plan');
  _token = null; _clientId = null; _clientName = null;
}

/* ── Workspaces ── */
async function getWorkspaces() { return api('/workspaces'); }

async function getWorkspaceClients(id) { return api(`/workspaces/${id}/clients`); }

async function getWorkspaceCampaigns(id, params = {}) {
  const qs = new URLSearchParams(params).toString();
  return api(`/workspaces/${id}/campaigns?${qs}`);
}

async function getWorkspaceCRMLogs(id, params = {}) {
  const qs = new URLSearchParams(params).toString();
  return api(`/workspaces/${id}/crm-logs?${qs}`);
}

/* ── Campaigns ── */
async function listCampaigns(clientId, params = {}) {
  const qs = new URLSearchParams(params).toString();
  return api(`/campaigns?client_id=${clientId}&${qs}`);
}

async function createCampaign(campaign) {
  return api('/campaigns', { method: 'POST', body: JSON.stringify(campaign) });
}

async function submitFeedback(campaignId, feedback) {
  return api(`/campaigns/${campaignId}/feedback`, { method: 'POST', body: JSON.stringify(feedback) });
}

async function updateCampaignStatus(campaignId, status) {
  return api(`/campaigns/${campaignId}/status?status=${status}`, { method: 'PUT' });
}

async function getCampaignStats(clientId) { return api(`/campaigns/stats/${clientId}`); }

/* ── CRM ── */
async function appendCRMLog(log) {
  return api('/crm/log', { method: 'POST', body: JSON.stringify(log) });
}

async function getClientProfile(clientId) { return api(`/crm/client/${clientId}`); }

/* ── Concierge Chat ── */
async function* streamChat(clientId, message) {
  const res = await fetch(`${API_BASE}/assistant/groq`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${_token}` },
    body: JSON.stringify({ client_id: clientId, message }),
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') break;
        try { yield JSON.parse(data); } catch {}
      }
    }
  }
}

async function syncChat(clientId, message) {
  return api('/assistant/groq/sync', { method: 'POST', body: JSON.stringify({ client_id: clientId, message }) });
}

/* ── Generation ── */
async function generate(type, prompt, workspaceId, files = []) {
  const fd = new FormData();
  fd.append('generation_type', type);
  fd.append('prompt', prompt);
  if (workspaceId) fd.append('workspace_id', workspaceId);
  for (const f of files) fd.append('files', f);
  const res = await fetch(`${API_BASE}/generate`, { method: 'POST', body: fd });
  return res.json();
}

/* ── Brand Pack ── */
async function extractPalette(file) {
  const fd = new FormData(); fd.append('file', file);
  return api('/brand/palette', { method: 'POST', body: fd });
}

async function vectorizeImage(file) {
  const fd = new FormData(); fd.append('file', file);
  return api('/brand/vectorize', { method: 'POST', body: fd });
}

/* ── Billing ── */
async function createCheckout(clientId, priceId) {
  return api('/billing/create-checkout-session', { method: 'POST', body: JSON.stringify({ client_id: clientId, price_id: priceId }) });
}

/* ── Helpers ── */
function escHtml(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const d = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
  if (d === 0) return 'today';
  if (d === 1) return '1d ago';
  return `${d}d ago`;
}

function formatPlatform(p) { return p.charAt(0).toUpperCase() + p.slice(1); }
