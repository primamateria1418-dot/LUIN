/*
 * LUIN Runtime Config — sets the backend URL depending on where the
 * frontend is being served from.
 *
 * - Running locally (localhost / 127.0.0.1, e.g. `python -m http.server`)
 *   -> talks to your local backend on port 8000
 * - Running on the live site (luin.cc, Netlify, etc.)
 *   -> talks to the production Render backend
 */
(function () {
  const isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
  window.LUIN_API_URL = isLocal
    ? 'http://localhost:8000/api/v1'
    : 'https://aria-agents.onrender.com/api/v1';
})();
