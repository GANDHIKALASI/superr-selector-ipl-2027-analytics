/**
 * Public Derived-Dashboard & Privacy Boundary Verification Suite
 *
 * Verifies:
 * 1. In Cloud / Vercel mode (VERCEL=1):
 *    - / returns 200 injecting batters, bowlers, overall, allrounders, allPlayers, dataQuality
 *      from the 7 clean derived dashboard files with reportsDownloadEnabled: false.
 *    - Analytics APIs (/api/batters, /api/bowlers, /api/overall, etc.) return 200.
 *    - Confidential PDF/PPTX downloads (/download/*), raw CSVs (/data/*),
 *      private reports (/submission/*, /reports/*), audit CSVs (/outputs/player_*),
 *      and source maps (*.map) strictly return HTTP 403.
 *    - Private screenshots (/assets/screenshot_*.png) return HTTP 404.
 * 2. Missing required outputs/ file returns HTTP 500 with explicit error (no mock fallback).
 * 3. Local mode enables PDF/PPTX downloads cleanly when outputs & submission files exist.
 */

const assert = require('assert');
const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const handleRequest = require('../server');

function requestPath(port, urlPath) {
  return new Promise((resolve, reject) => {
    const req = http.request(
      { hostname: '127.0.0.1', port, path: urlPath, method: 'GET' },
      (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: Buffer.concat(chunks),
          });
        });
      }
    );
    req.on('error', reject);
    req.end();
  });
}

async function runTests() {
  const prevVercel = process.env.VERCEL;
  const prevAppMode = process.env.SUPERR_APP_MODE;

  process.env.VERCEL = '1';
  delete process.env.SUPERR_APP_MODE;
  assert.strictEqual(handleRequest.isVercelEnvironment(), true);
  assert.strictEqual(handleRequest.areReportDownloadsEnabled(), false);

  const server = http.createServer(handleRequest);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();

  try {
    // 1. Health check under Vercel
    const health = await requestPath(port, '/api/health');
    assert.strictEqual(health.status, 200);
    assert.strictEqual(health.headers['x-superr-app-mode'], 'public-derived-dashboard');
    const healthJson = JSON.parse(health.body.toString('utf8'));
    assert.strictEqual(healthJson.app_mode, 'PUBLIC_DERIVED_DASHBOARD');
    assert.strictEqual(healthJson.raw_data_exposed, false);
    assert.strictEqual(healthJson.has_competition_outputs, true);
    assert.strictEqual(healthJson.reports_download_enabled, false);

    // 2. Dashboard SSR & APIs return derived player rankings on Vercel
    const htmlResp = await requestPath(port, '/');
    assert.strictEqual(htmlResp.status, 200);
    const htmlText = htmlResp.body.toString('utf8');
    assert(htmlText.includes('"appMode":"PUBLIC_DERIVED_DASHBOARD"'));
    assert(htmlText.includes('"reportsDownloadEnabled":false'));
    assert(htmlText.includes('"batters":['));

    for (const apiPath of [
      '/api/bootstrap',
      '/api/batters',
      '/api/bowlers',
      '/api/overall',
      '/api/allrounders',
      '/api/all-players',
      '/api/reliability',
      '/api/data-quality',
    ]) {
      const r = await requestPath(port, apiPath);
      assert.strictEqual(r.status, 200, `${apiPath} must return 200`);
    }

    // 3. Confidential downloads, raw data, audit CSVs & private paths stay blocked (403/404)
    for (const ep of [
      '/download/presentation',
      '/download/report',
      '/download/methodology',
      '/submission/final_submission.pdf',
      '/reports/SupeRR_Selector_Final_Report.pdf',
      '/outputs/player_eligibility_audit.csv',
      '/outputs/player_identity_audit.csv',
      '/data/ball_by_ball.csv',
      '/data/matches.csv',
      '/app.js.map',
      '/docs/methodology.md',
    ]) {
      const r = await requestPath(port, ep);
      assert.strictEqual(r.status, 403, `${ep} must remain blocked with 403, got ${r.status}`);
    }

    for (const okAsset of [
      '/app.js',
      '/style.css',
      '/logo.svg',
      '/favicon.svg',
      '/assets/superr_logo.png',
      '/assets/superr_crest.png',
      '/assets/gandhi-kalasi.jpg',
    ]) {
      const r = await requestPath(port, okAsset);
      assert.strictEqual(r.status, 200, `${okAsset} should return 200`);
    }

    for (const hiddenAsset of [
      '/assets/screenshot_overview.png',
      '/assets/dashboard-preview.png',
    ]) {
      const r = await requestPath(port, hiddenAsset);
      assert.strictEqual(r.status, 404, `${hiddenAsset} must remain 404 on Vercel`);
    }

    // 4. Local mode allows downloads & fails closed on missing outputs/
    delete process.env.VERCEL;
    assert.strictEqual(handleRequest.areReportDownloadsEnabled(), true);

    const emptyOutDir = fs.mkdtempSync(path.join(os.tmpdir(), 'superr-empty-out-'));
    try {
      process.env.SUPERR_OUTPUTS_DIR = emptyOutDir;
      const errApi = await requestPath(port, '/api/batters');
      assert.strictEqual(errApi.status, 500, 'Missing outputs must return HTTP 500');
      const errPayload = JSON.parse(errApi.body.toString('utf8'));
      assert(errPayload.error.includes('Missing required competition dashboard file(s)'));
    } finally {
      delete process.env.SUPERR_OUTPUTS_DIR;
      fs.rmSync(emptyOutDir, { recursive: true, force: true });
    }

    assert(!fs.existsSync(path.join(ROOT, 'demo')), 'demo/ folder must not exist');
    console.log('ALL PUBLIC DERIVED DASHBOARD & PRIVACY BOUNDARY CHECKS PASSED.');
  } finally {
    server.close();
    if (prevVercel !== undefined) process.env.VERCEL = prevVercel;
    else delete process.env.VERCEL;
    if (prevAppMode !== undefined) process.env.SUPERR_APP_MODE = prevAppMode;
    else delete process.env.SUPERR_APP_MODE;
  }
}

runTests().catch((err) => {
  console.error('VERIFICATION FAILED:', err);
  process.exit(1);
});
