const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 3000;
const BASE_DIR = __dirname;
const PUBLIC_DIR = path.join(BASE_DIR, 'public');
const ASSETS_DIR = path.join(BASE_DIR, 'assets');
const SUBMISSION_DIR = path.join(BASE_DIR, 'submission');

const PUBLIC_SAFE_ASSETS = new Set([
  'superr_crest.png',
  'superr_logo.png',
  'gandhi-kalasi.jpg',
]);

const PRIVATE_PATH_PREFIXES = [
  '/data/',
  '/outputs/',
  '/submission/',
  '/reports/',
  '/docs/',
  '/src/',
  '/notebooks/',
  '/tests/',
];

const REQUIRED_OUTPUT_FILES = [
  'top_10_batters.csv',
  'top_10_bowlers.csv',
  'top_10_overall.csv',
  'top_10_allrounders.csv',
  'eligible_player_universe.csv',
  'all_player_reliability_scores.csv',
  'data_quality_summary.json',
];

function isVercelEnvironment() {
  return Boolean(
    process.env.VERCEL || process.env.VERCEL_ENV || process.env.NOW_REGION
  );
}

function getOutputsDir() {
  if (isVercelEnvironment()) return path.join(BASE_DIR, 'outputs');
  return process.env.SUPERR_OUTPUTS_DIR || path.join(BASE_DIR, 'outputs');
}

function areReportDownloadsEnabled() {
  if (isVercelEnvironment()) return false;
  if (process.env.SUPERR_APP_MODE === 'public') return false;
  return true;
}

function findMissingSourceFiles() {
  const outDir = getOutputsDir();
  return REQUIRED_OUTPUT_FILES.filter(
    (name) => !fs.existsSync(path.join(outDir, name))
  );
}

function parseCSV(filePath) {
  if (!fs.existsSync(filePath)) return [];
  const raw = fs.readFileSync(filePath, 'utf8').trim();
  if (!raw) return [];
  const lines = raw.split(/\r?\n/);
  if (lines.length <= 1) return [];

  const headers = lines[0].split(',').map((h) => h.trim());
  const rows = [];
  const stringFields = new Set([
    'player_name',
    'primary_role',
    'role',
    'eligibility_status',
    'caveats',
    'rr_auction_rationale',
    'rr_strategic_value',
    'why_ranked',
    'pressure_evidence',
    'rr_role_recommendation',
    'squad_building_value',
    'risks_uncertainties',
    'bat_ci_95',
    'bowl_ci_95',
    'primary_ci_95',
  ]);

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;

    const values = [];
    let insideQuote = false;
    let current = '';

    for (let j = 0; j < line.length; j++) {
      const char = line[j];
      if (char === '"') {
        insideQuote = !insideQuote;
      } else if (char === ',' && !insideQuote) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());

    const obj = {};
    headers.forEach((h, idx) => {
      let val = values[idx] !== undefined ? values[idx] : '';
      if (val.startsWith('"') && val.endsWith('"')) {
        val = val.slice(1, -1);
      }
      const num = Number(val);
      obj[h] =
        !isNaN(num) &&
        val !== '' &&
        !val.includes(':') &&
        !val.includes('[') &&
        !stringFields.has(h)
          ? num
          : val;
    });
    rows.push(obj);
  }
  return rows;
}

function readJSON(filePath) {
  if (!fs.existsSync(filePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (e) {
    return null;
  }
}

function getMimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.pdf': 'application/pdf',
    '.pptx':
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  };
  return mimeTypes[ext] || 'application/octet-stream';
}

function firstExisting(paths) {
  for (const p of paths) {
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function loadCompetitionDatasetBundle() {
  const outDir = getOutputsDir();
  const missingFiles = findMissingSourceFiles();
  if (missingFiles.length > 0) {
    return {
      error: `Missing required competition dashboard file(s): ${missingFiles.join(', ')}. Substitute data generation is disabled.`,
      missingFiles,
    };
  }

  const dq = readJSON(path.join(outDir, 'data_quality_summary.json'));
  if (!dq) {
    return {
      error:
        'Invalid or unreadable data_quality_summary.json in outputs/. Substitute data generation is disabled.',
      missingFiles: ['data_quality_summary.json'],
    };
  }

  return {
    error: null,
    reportsDownloadEnabled: areReportDownloadsEnabled(),
    batters: parseCSV(path.join(outDir, 'top_10_batters.csv')),
    bowlers: parseCSV(path.join(outDir, 'top_10_bowlers.csv')),
    overall: parseCSV(path.join(outDir, 'top_10_overall.csv')),
    allrounders: parseCSV(path.join(outDir, 'top_10_allrounders.csv')),
    allPlayers: parseCSV(
      path.join(outDir, 'eligible_player_universe.csv')
    ),
    reliability: parseCSV(
      path.join(outDir, 'all_player_reliability_scores.csv')
    ),
    dataQuality: dq,
  };
}

function sendJSON(res, statusCode, payload, modeHeader) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'X-SupeRR-App-Mode': modeHeader,
  });
  return res.end(JSON.stringify(payload));
}

function handleRequest(req, res) {
  const parsedUrl = new URL(
    req.url || '/',
    `http://${req.headers.host || `localhost:${PORT}`}`
  );
  const pathname = parsedUrl.pathname;
  const downloadsEnabled = areReportDownloadsEnabled();
  const isCloud = !downloadsEnabled;
  const modeHeader = isCloud ? 'public-derived-dashboard' : 'private-local';
  const lowerPath = pathname.toLowerCase();

  // Block direct filesystem traversal to raw data, reports, audits, source maps
  if (
    lowerPath.endsWith('.map') ||
    PRIVATE_PATH_PREFIXES.some((prefix) => lowerPath.startsWith(prefix))
  ) {
    return sendJSON(
      res,
      403,
      {
        error: 'Access denied: private files and source maps are not exposed.',
        app_mode: modeHeader,
      },
      modeHeader
    );
  }

  // Health Check
  if (pathname === '/api/health') {
    const missing = findMissingSourceFiles();
    return sendJSON(
      res,
      200,
      {
        status: missing.length === 0 ? 'ok' : 'error',
        app_mode: isCloud ? 'PUBLIC_DERIVED_DASHBOARD' : 'PRIVATE_LOCAL',
        raw_data_exposed: false,
        has_competition_outputs: missing.length === 0,
        reports_download_enabled: downloadsEnabled,
      },
      modeHeader
    );
  }

  // Dashboard Analytics Endpoints (official derived outputs only; fail with 500 if missing)
  const isAnalyticsApi = [
    '/api/bootstrap',
    '/api/batters',
    '/api/bowlers',
    '/api/overall',
    '/api/allrounders',
    '/api/all-players',
    '/api/reliability',
    '/api/data-quality',
  ].includes(pathname);

  if (isAnalyticsApi) {
    const bundle = loadCompetitionDatasetBundle();
    if (bundle.error) {
      return sendJSON(
        res,
        500,
        {
          error: bundle.error,
          missingFiles: bundle.missingFiles,
        },
        modeHeader
      );
    }

    if (pathname === '/api/bootstrap') {
      return sendJSON(res, 200, bundle, modeHeader);
    }
    if (pathname === '/api/batters') {
      return sendJSON(res, 200, bundle.batters, modeHeader);
    }
    if (pathname === '/api/bowlers') {
      return sendJSON(res, 200, bundle.bowlers, modeHeader);
    }
    if (pathname === '/api/overall') {
      return sendJSON(res, 200, bundle.overall, modeHeader);
    }
    if (pathname === '/api/allrounders') {
      return sendJSON(res, 200, bundle.allrounders, modeHeader);
    }
    if (pathname === '/api/all-players') {
      return sendJSON(res, 200, bundle.allPlayers, modeHeader);
    }
    if (pathname === '/api/reliability') {
      return sendJSON(res, 200, bundle.reliability, modeHeader);
    }
    if (pathname === '/api/data-quality') {
      return sendJSON(res, 200, bundle.dataQuality, modeHeader);
    }
  }

  // Report / Presentation Downloads — disabled on Vercel / public cloud
  const isDownloadRequest =
    pathname.startsWith('/download/') ||
    lowerPath.endsWith('.pptx') ||
    lowerPath.endsWith('.pdf') ||
    lowerPath.endsWith('.zip');

  if (isDownloadRequest) {
    if (!downloadsEnabled) {
      return sendJSON(
        res,
        403,
        {
          error:
            'Confidential competition deliverables (.pdf / .pptx) are restricted to the local workspace.',
          app_mode: modeHeader,
        },
        modeHeader
      );
    }

    if (pathname === '/download/presentation' || lowerPath.includes('.pptx')) {
      const pptxPath = firstExisting([
        path.join(SUBMISSION_DIR, 'final_presentation.pptx'),
        path.join(BASE_DIR, 'reports', 'SupeRR_Selector_Auction_Strategy.pptx'),
        path.join(BASE_DIR, 'reports', 'SupeRR_Selector_Presentation.pptx'),
      ]);
      if (pptxPath) {
        res.writeHead(200, {
          'Content-Type':
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
          'Content-Disposition':
            'attachment; filename="SupeRR_Selector_Final_Presentation.pptx"',
          'X-SupeRR-App-Mode': modeHeader,
        });
        return fs.createReadStream(pptxPath).pipe(res);
      }
    }

    if (pathname === '/download/methodology') {
      const methPath = firstExisting([
        path.join(SUBMISSION_DIR, 'methodology.pdf'),
        path.join(BASE_DIR, 'reports', 'SupeRR_Selector_Research_Report.pdf'),
      ]);
      if (methPath) {
        res.writeHead(200, {
          'Content-Type': 'application/pdf',
          'Content-Disposition':
            'attachment; filename="SupeRR_Selector_Methodology.pdf"',
          'X-SupeRR-App-Mode': modeHeader,
        });
        return fs.createReadStream(methPath).pipe(res);
      }
    }

    if (pathname === '/download/report' || lowerPath.includes('.pdf')) {
      const pdfPath = firstExisting([
        path.join(SUBMISSION_DIR, 'final_submission.pdf'),
        path.join(BASE_DIR, 'reports', 'SupeRR_Selector_Research_Report.pdf'),
        path.join(BASE_DIR, 'reports', 'SupeRR_Selector_Final_Report.pdf'),
      ]);
      if (pdfPath) {
        res.writeHead(200, {
          'Content-Type': 'application/pdf',
          'Content-Disposition':
            'attachment; filename="SupeRR_Selector_Final_Submission.pdf"',
          'X-SupeRR-App-Mode': modeHeader,
        });
        return fs.createReadStream(pdfPath).pipe(res);
      }
    }

    return sendJSON(
      res,
      404,
      { error: 'Requested local deliverable not found.' },
      modeHeader
    );
  }

  // Static Assets Route — allowlisted on cloud deployments
  if (pathname.startsWith('/assets/')) {
    const relPath = pathname.replace('/assets/', '');
    if (isCloud && !PUBLIC_SAFE_ASSETS.has(relPath)) {
      return sendJSON(
        res,
        404,
        { error: 'Asset not exposed in public deployment.' },
        modeHeader
      );
    }
    const safePath = path.normalize(path.join(ASSETS_DIR, relPath));
    if (
      safePath.startsWith(ASSETS_DIR + path.sep) &&
      fs.existsSync(safePath) &&
      fs.statSync(safePath).isFile()
    ) {
      res.writeHead(200, {
        'Content-Type': getMimeType(safePath),
        'X-Content-Type-Options': 'nosniff',
        'X-SupeRR-App-Mode': modeHeader,
      });
      return fs.createReadStream(safePath).pipe(res);
    }
    return sendJSON(res, 404, { error: 'Asset not found.' }, modeHeader);
  }

  // Root / Index Route
  if (pathname === '/' || pathname === '/index.html') {
    const htmlPath = path.join(PUBLIC_DIR, 'index.html');
    if (!fs.existsSync(htmlPath)) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      return res.end('Dashboard index.html not found.');
    }

    let html = fs.readFileSync(htmlPath, 'utf8');
    const bundle = loadCompetitionDatasetBundle();
    const initialPayload = bundle.error
      ? {
          appMode: 'PRIVATE_LOCAL',
          reportsDownloadEnabled: downloadsEnabled,
          error: bundle.error,
          missingFiles: bundle.missingFiles,
        }
      : {
          appMode: isCloud ? 'PUBLIC_DERIVED_DASHBOARD' : 'PRIVATE_LOCAL',
          reportsDownloadEnabled: downloadsEnabled,
          error: null,
          batters: bundle.batters,
          bowlers: bundle.bowlers,
          overall: bundle.overall,
          allrounders: bundle.allrounders,
          allPlayers: bundle.allPlayers,
          dataQuality: bundle.dataQuality,
        };

    const injection = `<script>
      window.INITIAL_DATA = ${JSON.stringify(initialPayload)};
    </script>`;

    html = html.replace('<!-- INITIAL_DATA -->', injection);
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'X-Content-Type-Options': 'nosniff',
      'X-SupeRR-App-Mode': modeHeader,
    });
    return res.end(html);
  }

  // General Static Files in public/
  const cleanRel = pathname.replace(/^\/+/, '');
  const safePublicPath = path.normalize(path.join(PUBLIC_DIR, cleanRel));
  if (
    safePublicPath.startsWith(PUBLIC_DIR + path.sep) &&
    fs.existsSync(safePublicPath) &&
    fs.statSync(safePublicPath).isFile()
  ) {
    res.writeHead(200, {
      'Content-Type': getMimeType(safePublicPath),
      'X-Content-Type-Options': 'nosniff',
      'X-SupeRR-App-Mode': modeHeader,
    });
    return fs.createReadStream(safePublicPath).pipe(res);
  }

  res.writeHead(404, {
    'Content-Type': 'text/plain; charset=utf-8',
    'X-SupeRR-App-Mode': modeHeader,
  });
  res.end('404 Not Found');
}

module.exports = handleRequest;
module.exports.isVercelEnvironment = isVercelEnvironment;
module.exports.areReportDownloadsEnabled = areReportDownloadsEnabled;
module.exports.loadCompetitionDatasetBundle = loadCompetitionDatasetBundle;

if (require.main === module) {
  const server = http.createServer(handleRequest);
  server.listen(PORT, () => {
    const modeLabel = areReportDownloadsEnabled()
      ? 'LOCAL COMPETITION WORKSPACE (Full Data + Reports)'
      : 'PUBLIC DERIVED DASHBOARD MODE (Reports & Raw CSVs Blocked)';
    console.log(
      `SupeRR Selector Dashboard active on http://localhost:${PORT} [${modeLabel}]`
    );
  });
}
