/*
 * LUIN Dashboard — Main Application Logic
 */

let currentWorkspace = null;
let currentSection = 'overview';

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('luin_token');
  if (token) {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    _token = token;
    _clientId = localStorage.getItem('luin_client_id') || 'c3d4e5f6-a7b8-9012-cdef-123456789012';
    _clientName = localStorage.getItem('luin_client_name') || 'LUIN Agency';
    initDashboard();
  }
});

function initDashboard() {
  const avatar = document.getElementById('topbar-avatar');
  if (avatar) avatar.textContent = (_clientName || 'L')[0].toUpperCase();

  loadWorkspaces();
  loadAgentStatus();
  setDate();

  // Sidebar click handlers
  document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', () => {
      const section = link.dataset.section;
      if (section) navigateTo(section);
    });
  });

  // Chat toggle
  const chatToggle = document.getElementById('chat-toggle');
  if (chatToggle) {
    chatToggle.addEventListener('click', () => {
      document.getElementById('chat-drawer').classList.toggle('open');
    });
  }

  // Workspace selector
  const wsSelector = document.getElementById('workspace-selector');
  if (wsSelector) {
    wsSelector.addEventListener('change', (e) => {
      currentWorkspace = e.target.value;
      loadOverview();
    });
  }

  // Initial load
  loadOverview();
}

/* ── Navigation ── */
function navigateTo(section) {
  currentSection = section;

  // Update sidebar
  document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
  const active = document.querySelector(`.sidebar-link[data-section="${section}"]`);
  if (active) active.classList.add('active');

  // Show section
  document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
  const target = document.getElementById(`section-${section}`);
  if (target) target.classList.remove('hidden');

  // Load section data
  if (section === 'overview') loadOverview();
  else if (section === 'approval') loadApprovalQueue();
  else if (section === 'content') loadContentPanel();
  else if (section === 'studio') loadStudio();
  else if (section === 'campaign-studio') loadCampaignStudio();
  else if (section === 'leads') loadLeadsPanel();
  else if (section === 'reports') loadReportsPanel();
  else if (section === 'billing') loadBillingPanel();
  else if (section === 'settings') loadSettingsPanel();
}

/* ── Workspaces ── */
async function loadWorkspaces() {
  const selector = document.getElementById('workspace-selector');
  if (!selector) return;

  try {
    const data = await getWorkspaces();
    selector.innerHTML = '';
    (data.workspaces || []).forEach(ws => {
      const opt = document.createElement('option');
      opt.value = ws.id;
      opt.textContent = ws.name;
      if (ws.id === currentWorkspace) opt.selected = true;
      selector.appendChild(opt);
    });
  } catch (e) {
    // Fallback to seed data
    const seeds = [
      { id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', name: '1095 Apparel' },
      { id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901', name: 'United Planet' },
      { id: 'c3d4e5f6-a7b8-9012-cdef-123456789012', name: 'LUIN Agency' },
    ];
    seeds.forEach(ws => {
      const opt = document.createElement('option');
      opt.value = ws.id; opt.textContent = ws.name;
      if (!currentWorkspace) currentWorkspace = ws.id;
      selector.appendChild(opt);
    });
  }
}

/* ── Overview ── */
async function loadOverview() {
  const clientId = currentWorkspace || _clientId;
  if (!clientId) return;

  const statsGrid = document.getElementById('stats-grid');
  if (!statsGrid) return;

  try {
    const stats = await getCampaignStats(clientId);
    const profile = await getClientProfile(clientId);

    const total = stats.total || 0;
    const pending = stats.by_status?.pending || 0;
    const approved = stats.by_status?.approved || 0;
    const published = stats.by_status?.published || 0;

    statsGrid.innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Total Campaigns</div>
        <div class="stat-value accent">${total}</div>
        <div class="stat-change">All platforms</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Pending Review</div>
        <div class="stat-value amber">${pending}</div>
        <div class="stat-change">Awaiting approval</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Approved</div>
        <div class="stat-value green">${approved}</div>
        <div class="stat-change">Ready to publish</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Published</div>
        <div class="stat-value">${published}</div>
        <div class="stat-change">This period</div>
      </div>
    `;
  } catch {
    // Seed data fallback
    statsGrid.innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Total Campaigns</div>
        <div class="stat-value accent">24</div>
        <div class="stat-change">All platforms</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Pending Review</div>
        <div class="stat-value amber">5</div>
        <div class="stat-change">Awaiting approval</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Approved</div>
        <div class="stat-value green">12</div>
        <div class="stat-change">Ready to publish</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Published</div>
        <div class="stat-value">7</div>
        <div class="stat-change">This period</div>
      </div>
    `;
  }

  // Workspace name
  const wsName = document.getElementById('ws-name');
  if (wsName) {
    try {
      const profile = await getWorkspaceClients(currentWorkspace);
      wsName.textContent = profile.name;
    } catch {
      wsName.textContent = 'LUIN Agency';
    }
  }
}

/* ── Approval Queue ── */
async function loadApprovalQueue() {
  const clientId = currentWorkspace || _clientId;
  const container = document.getElementById('approval-kanban');
  if (!container) return;

  try {
    const campaigns = await listCampaigns(clientId, { limit: 50 });

    const pending = campaigns.filter(c => c.status === 'pending' || c.status === 'draft');
    const approved = campaigns.filter(c => c.status === 'approved');
    const published = campaigns.filter(c => c.status === 'published');
    const rejected = campaigns.filter(c => c.status === 'rejected');

    container.innerHTML = `
      ${renderKanbanCol('Pending', pending, 'text-amber', (c) => approveCampaign(c.id))}
      ${renderKanbanCol('Approved', approved, 'text-green', (c) => publishCampaign(c.id))}
      ${renderKanbanCol('Published', published, 'text-muted', (c) => {})}
      ${renderKanbanCol('Rejected', rejected, 'text-red', (c) => editCampaign(c.id))}
    `;
  } catch {
    // Seed data
    container.innerHTML = `
      ${renderKanbanCol('Pending', [
        { id: '1', platform: 'linkedin', content_type: 'text', draft_text: 'Excited to announce our new product line for Q1 2026...', scheduled_at: '2026-07-25' },
        { id: '2', platform: 'twitter', content_type: 'text', draft_text: 'Just wrapped up our annual strategy review. Key takeaway: AI-first marketing is no longer optional.', scheduled_at: '2026-07-26' },
      ], 'text-amber', (id) => approveCampaign(id))}
      ${renderKanbanCol('Approved', [
        { id: '3', platform: 'instagram', content_type: 'image', draft_text: 'Product launch campaign visuals', scheduled_at: '2026-07-27' },
      ], 'text-green', (id) => publishCampaign(id))}
      ${renderKanbanCol('Published', [
        { id: '4', platform: 'linkedin', content_type: 'text', draft_text: 'Industry insights on digital transformation', scheduled_at: '2026-07-20' },
      ], 'text-muted', () => {})}
      ${renderKanbanCol('Rejected', [], 'text-red', () => {})}
    `;
  }
}

function renderKanbanCol(title, items, colorClass, actionFn) {
  return `
    <div class="kanban-col">
      <div class="kanban-col-header">
        <span class="kanban-col-title ${colorClass}">${title}</span>
        <span class="kanban-count">${items.length}</span>
      </div>
      ${items.map(c => `
        <div class="kanban-card" onclick="viewCampaign('${c.id}')">
          <div class="kanban-card-platform">${formatPlatform(c.platform)}</div>
          <div class="kanban-card-text">${escHtml(c.draft_text || 'No draft text')}</div>
          <div class="kanban-card-meta">
            <span>${c.scheduled_at ? timeAgo(c.scheduled_at) : ''}</span>
            <span>${formatPlatform(c.content_type)}</span>
          </div>
          ${actionFn ? `<div style="margin-top:8px;display:flex;gap:6px;">
            <button class="btn btn-sm btn-outline" onclick="event.stopPropagation();(${actionFn.toString()})('${c.id}')">Action</button>
          </div>` : ''}
        </div>
      `).join('')}
    </div>
  `;
}

async function approveCampaign(id) {
  try { await updateCampaignStatus(id, 'approved'); loadApprovalQueue(); } catch {}
}
async function publishCampaign(id) {
  try { await updateCampaignStatus(id, 'published'); loadApprovalQueue(); } catch {}
}
async function editCampaign(id) {
  navigateTo('studio');
}
async function viewCampaign(id) {
  navigateTo('studio');
}

/* ── Content Panel ── */
function loadContentPanel() {
  const cal = document.getElementById('content-calendar');
  if (!cal) return;

  const events = [
    { day: 3, platform: 'linkedin', text: 'Industry report' },
    { day: 5, platform: 'twitter', text: 'Thread: AI trends' },
    { day: 8, platform: 'instagram', text: 'Product showcase' },
    { day: 10, platform: 'blog', text: 'White paper' },
    { day: 12, platform: 'linkedin', text: 'Case study' },
    { day: 15, platform: 'tiktok', text: 'Behind the scenes' },
    { day: 18, platform: 'twitter', text: 'Poll: Marketing tools' },
    { day: 20, platform: 'facebook', text: 'Event announcement' },
    { day: 22, platform: 'linkedin', text: 'Thought leadership' },
    { day: 25, platform: 'instagram', text: 'Team spotlight' },
    { day: 28, platform: 'blog', text: 'Quarterly review' },
  ];

  let html = '<div class="calendar-grid">';
  ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].forEach(d => {
    html += `<div class="calendar-day-header">${d}</div>`;
  });

  for (let i = 1; i <= 31; i++) {
    const isToday = i === new Date().getDate();
    html += `<div class="calendar-day${isToday ? ' today' : ''}">
      <div style="font-size:0.7rem;color:var(--text-dim);margin-bottom:4px">${i}</div>
      ${events.filter(e => e.day === i).map(e =>
        `<div class="calendar-event ${e.platform}">${escHtml(e.text)}</div>`
      ).join('')}
    </div>`;
  }
  html += '</div>';
  cal.innerHTML = html;
}

/* ── Studio ── */
function loadStudio() {
  const clientId = currentWorkspace || _clientId;
  if (!clientId) return;

  const resultDiv = document.getElementById('gen-result');
  if (!resultDiv) return;

  window._genResult = resultDiv;
  window._genClientId = clientId;
}

async function handleGeneration(type, prompt) {
  const clientId = window._genClientId || _clientId;
  const resultDiv = window._genResult;
  const btn = document.getElementById('gen-submit-btn');

  btn.disabled = true;
  btn.textContent = 'Generating...';
  resultDiv.innerHTML = `
    <div style="display:flex;align-items:center;gap:12px;padding:20px;">
      <div style="width:20px;height:20px;border:3px solid var(--accent-mid);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite;"></div>
      <span class="text-muted">Generating ${type}...</span>
    </div>
  `;

  try {
    const result = await generate(type, prompt, currentWorkspace);
    if (result.status === 'success') {
      if (result.copy) {
        resultDiv.innerHTML = `
          <div class="generation-result">
            <div class="result-icon">✍️</div>
            <h4>Copy Generated</h4>
            <pre style="text-align:left;background:var(--bg);padding:16px;border-radius:var(--radius-sm);font-size:0.85rem;color:var(--text-muted);max-height:300px;overflow:auto;white-space:pre-wrap;">${escHtml(result.copy)}</pre>
            <div style="margin-top:12px;display:flex;gap:8px;justify-content:center;">
              <button class="btn btn-sm btn-outline" onclick="navigator.clipboard.writeText(${JSON.stringify(result.copy)});this.textContent='Copied!';">Copy</button>
              <button class="btn btn-sm btn-green" onclick="submitToQueue(${JSON.stringify(result.copy)})">Submit to Queue</button>
            </div>
          </div>`;
      } else if (result.palette) {
        resultDiv.innerHTML = `
          <div class="generation-result">
            <div class="result-icon">🎨</div>
            <h4>Palette Extracted</h4>
            <div style="display:flex;gap:12px;justify-content:center;margin:16px 0;">
              ${Object.entries(result.palette).map(([k,v]) => `
                <div style="text-align:center;">
                  <div style="width:48px;height:48px;border-radius:8px;background:${v};margin:0 auto 6px;border:1px solid var(--border);"></div>
                  <span style="font-size:0.72rem;color:var(--text-dim);">${k}</span>
                  <span style="font-size:0.68rem;color:var(--text-dim);display:block;">${v}</span>
                </div>
              `).join('')}
            </div>
          </div>`;
      } else {
        resultDiv.innerHTML = `
          <div class="generation-result">
            <div class="result-icon">⏳</div>
            <h4>Generation Queued</h4>
            <p>Result ID: ${escHtml(result.prompt_id || 'N/A')}</p>
            <p class="text-muted" style="font-size:0.82rem;">Poll /prompt/{id} for results</p>
          </div>`;
      }
    } else {
      resultDiv.innerHTML = `<div class="generation-result"><div class="result-icon">⚠️</div><h4>Generation Failed</h4><p class="text-red">${escHtml(result.message || 'Unknown error')}</p></div>`;
    }
  } catch (e) {
    resultDiv.innerHTML = `<div class="generation-result"><div class="result-icon">⚠️</div><h4>Error</h4><p class="text-red">${escHtml(e.message)}</p></div>`;
  }

  btn.disabled = false;
  btn.textContent = 'Generate';
}

async function submitToQueue(copy) {
  const clientId = window._genClientId || _clientId;
  try {
    await createCampaign({ client_id: clientId, platform: 'linkedin', content_type: 'text', draft_text: copy });
    alert('Submitted to queue!');
  } catch {}
}

/* ── Leads Panel ── */
function loadLeadsPanel() {
  const container = document.getElementById('leads-container');
  if (!container) return;

  const leads = [
    { name: 'Sarah Chen', title: 'CMO', company: 'TechForward Inc.', industry: 'SaaS', score: 92 },
    { name: 'Marcus Webb', title: 'VP Marketing', company: 'Atlas Ventures', industry: 'Finance', score: 87 },
    { name: 'Priya Sharma', title: 'Head of Growth', company: 'NovaHealth', industry: 'Healthcare', score: 84 },
    { name: 'James Liu', title: 'Director', company: 'GreenPath Energy', industry: 'Energy', score: 79 },
    { name: 'Elena Rodriguez', title: 'CEO', company: 'Meridian Labs', industry: 'Biotech', score: 76 },
    { name: 'Tom Andersen', title: 'VP Sales', company: 'Nordic Systems', industry: 'Enterprise', score: 73 },
  ];

  container.innerHTML = `
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="border-bottom:1px solid var(--border);text-align:left;">
            <th style="padding:12px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Name</th>
            <th style="padding:12px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Title</th>
            <th style="padding:12px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Company</th>
            <th style="padding:12px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Industry</th>
            <th style="padding:12px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Lead Score</th>
            <th style="padding:12px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${leads.map(l => `
            <tr style="border-bottom:1px solid var(--border);">
              <td style="padding:12px 16px;font-size:0.88rem;">${escHtml(l.name)}</td>
              <td style="padding:12px 16px;font-size:0.82rem;color:var(--text-muted);">${escHtml(l.title)}</td>
              <td style="padding:12px 16px;font-size:0.82rem;color:var(--text-muted);">${escHtml(l.company)}</td>
              <td style="padding:12px 16px;"><span style="font-size:0.75rem;background:var(--surface-3);padding:3px 10px;border-radius:100px;color:var(--text-muted);">${escHtml(l.industry)}</span></td>
              <td style="padding:12px 16px;">
                <span style="font-size:0.85rem;font-weight:600;color:${l.score >= 85 ? 'var(--green)' : l.score >= 70 ? 'var(--amber)' : 'var(--text-muted)'};">${l.score}</span>
              </td>
              <td style="padding:12px 16px;">
                <button class="btn btn-sm btn-outline" onclick="alert('Outreach sequence started for ${escHtml(l.name)}')">Reach Out</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

/* ── Reports Panel ── */
function loadReportsPanel() {
  const container = document.getElementById('reports-container');
  if (!container) return;

  container.innerHTML = `
    <div class="report-section">
      <h4>📊 Weekly Performance Summary</h4>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-label">Engagement Rate</div><div class="stat-value green">4.2%</div><div class="stat-change">↑ 12% from last week</div></div>
        <div class="stat-card"><div class="stat-label">Total Reach</div><div class="stat-value accent">28.4K</div><div class="stat-change">↑ 8% from last week</div></div>
        <div class="stat-card"><div class="stat-label">Click-Through Rate</div><div class="stat-value">2.1%</div><div class="stat-change">↓ 3% from last week</div></div>
        <div class="stat-card"><div class="stat-label">New Followers</div><div class="stat-value green">347</div><div class="stat-change">↑ 24% from last week</div></div>
      </div>
    </div>
    <div class="report-section">
      <h4>📝 Key Insights & Recommendations</h4>
      <div class="report-metric">
        <div class="metric-content">LinkedIn posts with data visualizations received 3x more engagement than text-only posts this week.</div>
        <div class="metric-meta"><span class="confidence" style="color:var(--green)">Confidence: 92%</span><span>Source: Platform Analytics</span></div>
      </div>
      <div class="report-metric">
        <div class="metric-content">Twitter thread published on Tuesday showed highest click-through rate (4.8%) of the week. Consider scheduling key content on early weekday mornings.</div>
        <div class="metric-meta"><span class="confidence" style="color:var(--green)">Confidence: 87%</span><span>Source: Engagement Data</span></div>
      </div>
      <div class="report-metric">
        <div class="metric-content">Instagram Reels engagement dropped 15% — recommend reviewing content format and posting time adjustments.</div>
        <div class="metric-meta"><span class="confidence" style="color:var(--amber)">Confidence: 74%</span><span>Source: Platform Analytics</span></div>
      </div>
    </div>
    <div class="report-section">
      <h4>📅 Upcoming Scheduled Content</h4>
      <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="border-bottom:1px solid var(--border);text-align:left;">
              <th style="padding:10px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;">Date</th>
              <th style="padding:10px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;">Platform</th>
              <th style="padding:10px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;">Type</th>
              <th style="padding:10px 16px;font-size:0.78rem;font-weight:600;color:var(--text-dim);text-transform:uppercase;">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid var(--border);">
              <td style="padding:10px 16px;font-size:0.85rem;">Jul 25</td>
              <td style="padding:10px 16px;font-size:0.82rem;color:var(--text-muted);">LinkedIn</td>
              <td style="padding:10px 16px;font-size:0.82rem;color:var(--text-muted);">Text Post</td>
              <td style="padding:10px 16px;"><span style="font-size:0.75rem;background:var(--amber-soft);color:var(--amber);padding:2px 8px;border-radius:100px;">Pending</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border);">
              <td style="padding:10px 16px;font-size:0.85rem;">Jul 26</td>
              <td style="padding:10px 16px;font-size:0.82rem;color:var(--text-muted);">Twitter/X</td>
              <td style="padding:10px 16px;font-size:0.82rem;color:var(--text-muted);">Thread</td>
              <td style="padding:10px 16px;"><span style="font-size:0.75rem;background:var(--accent-soft);color:var(--accent);padding:2px 8px;border-radius:100px;">Draft</span></td>
            </tr>
            <tr>
              <td style="padding:10px 16px;font-size:0.85rem;">Jul 27</td>
              <td style="padding:10px 16px;font-size:0.82rem;color:var(--text-muted);">Instagram</td>
              <td style="padding:10px 16px;font-size:0.82rem;color:var(--text-muted);">Image + Caption</td>
              <td style="padding:10px 16px;"><span style="font-size:0.75rem;background:var(--green-soft);color:var(--green);padding:2px 8px;border-radius:100px;">Approved</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
}

/* ── Billing Panel ── */
function loadBillingPanel() {
  const container = document.getElementById('billing-container');
  if (!container) return;

  container.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;">
      <div class="plan-card">
        <h3>Starter</h3>
        <div class="price">$997<span>/mo</span></div>
        <ul class="features">
          <li>1 Workspace</li>
          <li>15 posts/month</li>
          <li>2 Platforms</li>
          <li>Basic analytics</li>
          <li>Email support</li>
        </ul>
        <button class="btn w-full" onclick="alert('Upgrade flow — integrate Stripe')">Select</button>
      </div>
      <div class="plan-card featured">
        <div style="font-size:0.72rem;font-weight:600;color:var(--accent);letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">Most Popular</div>
        <h3>Growth</h3>
        <div class="price">$2,497<span>/mo</span></div>
        <ul class="features">
          <li>3 Workspaces</li>
          <li>60 posts/month</li>
          <li>5 Platforms</li>
          <li>Advanced analytics</li>
          <li>AI Concierge</li>
          <li>Priority support</li>
        </ul>
        <button class="btn w-full" onclick="alert('Upgrade flow — integrate Stripe')">Select</button>
      </div>
      <div class="plan-card">
        <h3>Enterprise</h3>
        <div class="price">Custom</div>
        <ul class="features">
          <li>Unlimited Workspaces</li>
          <li>Unlimited posts</li>
          <li>All Platforms</li>
          <li>Custom integrations</li>
          <li>Dedicated account manager</li>
          <li>SLA guarantee</li>
        </ul>
        <button class="btn btn-outline w-full" onclick="alert('Contact sales')">Contact Sales</button>
      </div>
    </div>
  `;
}

/* ── Settings Panel ── */
function loadSettingsPanel() {
  const container = document.getElementById('settings-container');
  if (!container) return;

  container.innerHTML = `
    <div class="settings-section">
      <h4>Account</h4>
      <div class="setting-row">
        <div class="setting-info"><div class="name">Email</div><div class="desc">${escHtml(localStorage.getItem('luin_email') || 'Not set')}</div></div>
        <button class="btn btn-sm btn-outline">Change</button>
      </div>
      <div class="setting-row">
        <div class="setting-info"><div class="name">Workspace</div><div class="desc">${escHtml(currentWorkspace || 'Not set')}</div></div>
        <button class="btn btn-sm btn-outline">Switch</button>
      </div>
    </div>
    <div class="settings-section">
      <h4>Notifications</h4>
      <div class="setting-row">
        <div class="setting-info"><div class="name">Email notifications</div><div class="desc">Receive email alerts for campaign approvals</div></div>
        <div class="toggle on" onclick="this.classList.toggle('on')"></div>
      </div>
      <div class="setting-row">
        <div class="setting-info"><div class="name">Campaign reminders</div><div class="desc">Daily digest of pending campaigns</div></div>
        <div class="toggle on" onclick="this.classList.toggle('on')"></div>
      </div>
      <div class="setting-row">
        <div class="setting-info"><div class="name">Agent status alerts</div><div class="desc">Alerts when agents complete tasks</div></div>
        <div class="toggle" onclick="this.classList.toggle('on')"></div>
      </div>
    </div>
    <div class="settings-section">
      <h4>API & Integrations</h4>
      <div class="setting-row">
        <div class="setting-info"><div class="name">Groq AI</div><div class="desc">${settings?.GROQ_API_KEY ? 'Configured' : 'Not configured'}</div></div>
        <span class="text-green">✓</span>
      </div>
      <div class="setting-row">
        <div class="setting-info"><div class="name">ComfyUI</div><div class="desc">${settings?.COMFYUI_URL || 'Not configured'}</div></div>
        <span class="text-green">✓</span>
      </div>
      <div class="setting-row">
        <div class="setting-info"><div class="name">Stripe</div><div class="desc">${settings?.STRIPE_SECRET_KEY ? 'Connected' : 'Not configured'}</div></div>
        <span class="${settings?.STRIPE_SECRET_KEY ? 'text-green' : 'text-amber'}">${settings?.STRIPE_SECRET_KEY ? '✓' : '○'}</span>
      </div>
    </div>
    <div class="settings-section">
      <h4>Danger Zone</h4>
      <button class="btn btn-outline" style="border-color:var(--red);color:var(--red);" onclick="if(confirm('Clear all local data?')){localStorage.clear();location.reload();}">Clear Local Data</button>
    </div>
  `;
}

/* ── Agent Status ── */
function loadAgentStatus() {
  const container = document.getElementById('agent-status-list');
  if (!container) return;

  const agents = [
    { name: 'JAMIE™', status: 'live', desc: 'Lead Hunter' },
    { name: 'Writer', status: 'live', desc: 'Copy Engine' },
    { name: 'CREA™', status: 'live', desc: 'Image Gen' },
    { name: 'LinkedIn', status: 'live', desc: 'Post Scheduler' },
    { name: 'Research', status: 'live', desc: 'Signal Harvest' },
    { name: 'Reporting', status: 'inactive', desc: 'Weekly Reports' },
    { name: 'Scheduler', status: 'inactive', desc: 'Content Queue' },
    { name: 'Qualifier', status: 'inactive', desc: 'Lead Scoring' },
  ];

  container.innerHTML = agents.map(a => `
    <div class="sidebar-agent">
      <span class="agent-dot ${a.status}"></span>
      <span>${a.name}</span>
      <span class="text-dim" style="margin-left:auto;font-size:0.72rem;">${a.desc}</span>
    </div>
  `).join('');
}

/* ── Helpers ── */
function setDate() {
  const el = document.getElementById('current-date');
  if (el) el.textContent = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
}

/* ── Campaign Studio ── */
let _campaignKeyMessages = [];

function loadCampaignStudio() {
  const clientId = currentWorkspace || _clientId;
  if (!clientId) return;
  loadCampaignsList(clientId);
}

async function submitCampaign() {
  const clientId = currentWorkspace || _clientId;
  const campaignName = document.getElementById('campaign-name').value.trim();
  const campaignDescription = document.getElementById('campaign-description').value.trim();
  const platforms = Array.from(document.getElementById('campaign-platforms').selectedOptions).map(o => o.value);
  const mediaTypes = Array.from(document.getElementById('campaign-media-types').selectedOptions).map(o => o.value);
  const postingTime = document.getElementById('campaign-posting-time').value;
  const frequency = document.getElementById('campaign-frequency').value;
  const brandVoice = document.getElementById('campaign-brand-voice').value.trim();

  if (!campaignName || !campaignDescription) {
    alert('Please fill in campaign name and description.');
    return;
  }

  // Submit campaign to backend
  try {
    const response = await fetch(`${API_BASE}/campaign-studio/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${_token}` },
      body: JSON.stringify({
        client_id: clientId,
        campaign_name: campaignName,
        campaign_description: campaignDescription,
        target_platforms: platforms,
        key_messages: _campaignKeyMessages,
        media_types: mediaTypes,
        brand_voice: brandVoice,
        posting_schedule: [{ day: 'mon', time: postingTime, platform: platforms[0] || 'linkedin' }],
        content_frequency: frequency,
        target_audience: {},
      }),
    });

    if (!response.ok) throw new Error('Campaign submission failed');
    const data = await response.json();

    // Sync dynamic client control to n8n
    await syncClientControl(clientId, postingTime, frequency, brandVoice, _campaignKeyMessages);

    alert(`Campaign "${campaignName}" submitted! Media generation triggered.`);
    loadCampaignsList(clientId);
  } catch (e) {
    alert(`Error: ${e.message}`);
  }
}

async function syncClientControl(clientId, postingTime, frequency, brandVoice, keyMessages) {
  try {
    await fetch(`${API_BASE}/client-control/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${_token}` },
      body: JSON.stringify({
        client_id: clientId,
        posting_schedule: [{ day: 'mon', time: postingTime, platform: 'linkedin' }],
        content_frequency: frequency,
        brand_voice: brandVoice,
        key_messages: keyMessages,
      }),
    });
  } catch (e) {
    console.error('Client control sync failed:', e);
  }
}

async function loadCampaignsList(clientId) {
  const container = document.getElementById('campaigns-list');
  if (!container) return;

  try {
    const response = await fetch(`${API_BASE}/campaign-studio/${clientId}`, {
      headers: { 'Authorization': `Bearer ${_token}` },
    });
    const campaigns = await response.json();

    if (campaigns.length === 0) {
      container.innerHTML = '<p style="color:var(--text-dim);">No campaigns yet. Submit your first campaign above.</p>';
      return;
    }

    container.innerHTML = campaigns.map(c => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border);">
        <div>
          <div style="font-weight:600;">${escHtml(c.name)}</div>
          <div style="font-size:0.82rem;color:var(--text-muted);">${escHtml(c.description)}</div>
          <div style="font-size:0.78rem;color:var(--text-dim);margin-top:4px;">Status: <span style="color:${c.status === 'approved' ? 'var(--green)' : c.status === 'pending' ? 'var(--amber)' : 'var(--text-muted)'};">${c.status}</span></div>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-sm btn-outline" onclick="generateMediaForCampaign('${c.id}')">🎨 Generate Media</button>
          <button class="btn btn-sm btn-outline" onclick="alert('Edit campaign ${c.id}')">✏️ Edit</button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = '<p style="color:var(--text-red);">Error loading campaigns.</p>';
  }
}

async function generateMediaForCampaign(campaignId) {
  try {
    const response = await fetch(`${API_BASE}/campaign-studio/${campaignId}/generate-media`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${_token}` },
    });
    const data = await response.json();
    alert(`Media generation triggered for campaign ${campaignId}. Status: ${data.status}`);
  } catch (e) {
    alert(`Error: ${e.message}`);
  }
}

// Key messages tag input
document.addEventListener('DOMContentLoaded', () => {
  const keyMsgInput = document.getElementById('campaign-key-messages');
  if (keyMsgInput) {
    keyMsgInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ',') {
        e.preventDefault();
        const val = e.target.value.replace(/,/g, '').trim();
        if (val && !_campaignKeyMessages.includes(val)) {
          _campaignKeyMessages.push(val);
          renderKeyMessagesTags();
        }
        e.target.value = '';
      }
    });
  }
});

function renderKeyMessagesTags() {
  const container = document.getElementById('campaign-key-messages-tags');
  if (!container) return;
  container.innerHTML = _campaignKeyMessages.map((msg, i) => `
    <span class="tag">${escHtml(msg)}<span class="tag-remove" onclick="removeKeyMessage(${i})">✕</span></span>
  `).join('');
}

function removeKeyMessage(idx) {
  _campaignKeyMessages.splice(idx, 1);
  renderKeyMessagesTags();
}
