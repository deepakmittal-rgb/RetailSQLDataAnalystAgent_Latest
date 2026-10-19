import express from 'express';
import path from 'path';
import fs from 'fs';
import { execFile } from 'child_process';
import { createServer as createViteServer } from 'vite';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = parseInt(process.env.PORT || '3000', 10);
const HOST = '0.0.0.0';

app.use(express.json());

// Helper to invoke Python bridge safely
function invokePythonBridge(payload: Record<string, unknown>): Promise<any> {
  return new Promise((resolve, reject) => {
    const pythonBin = process.platform === 'win32' ? 'python' : 'python3';
    const scriptPath = path.resolve(process.cwd(), 'src/bridge.py');

    const child = execFile(
      pythonBin,
      [scriptPath],
      { cwd: process.cwd(), maxBuffer: 10 * 1024 * 1024, timeout: 30000 },
      (error, stdout, stderr) => {
        if (error) {
          console.error('[PythonBridge Error]:', stderr || error.message);
          return reject(new Error(stderr || error.message));
        }
        try {
          // Look for JSON output in stdout
          const trimmed = stdout.trim();
          const firstBrace = trimmed.indexOf('{');
          if (firstBrace === -1) {
            return reject(new Error('No JSON output from Python bridge: ' + trimmed));
          }
          const jsonStr = trimmed.slice(firstBrace);
          const parsed = JSON.parse(jsonStr);
          resolve(parsed);
        } catch (err: any) {
          console.error('[PythonBridge Parse Error]:', err, stdout);
          reject(new Error(`Failed to parse bridge output: ${err.message}`));
        }
      }
    );

    child.stdin?.write(JSON.stringify(payload));
    child.stdin?.end();
  });
}

// 1. Analyst Query Endpoint
app.post('/api/analyst/query', async (req, res) => {
  try {
    const { question, reset } = req.body;
    if (!question || typeof question !== 'string') {
      return res.status(400).json({ error: 'Valid question parameter is required.' });
    }
    const result = await invokePythonBridge({ action: 'query', question, reset: !!reset });
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message || 'Internal agent error' });
  }
});

// 2. Reset Context Memory Endpoint
app.post('/api/analyst/reset', async (_req, res) => {
  try {
    const result = await invokePythonBridge({ action: 'reset' });
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 3. Schema Exploration Endpoint
app.get('/api/database/schema', async (_req, res) => {
  try {
    const result = await invokePythonBridge({ action: 'schema' });
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 4. SQL Safety Validator Endpoint
app.post('/api/analyst/validate-sql', async (req, res) => {
  try {
    const { sql } = req.body;
    const result = await invokePythonBridge({ action: 'validate_sql', sql });
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 5. Test Suite Runner Endpoint
app.post('/api/analyst/run-tests', async (_req, res) => {
  const pythonBin = process.platform === 'win32' ? 'python' : 'python3';
  const testScript = path.resolve(process.cwd(), 'tests/run_all_tests.py');

  execFile(
    pythonBin,
    [testScript],
    { cwd: process.cwd(), maxBuffer: 5 * 1024 * 1024, timeout: 30000 },
    (_error, stdout, stderr) => {
      let evidence = '';
      const evidencePath = path.resolve(process.cwd(), 'evidence/test_execution_log.txt');
      if (fs.existsSync(evidencePath)) {
        evidence = fs.readFileSync(evidencePath, 'utf-8');
      }

      res.json({
        output: (stdout + '\n' + stderr).trim(),
        evidence,
        timestamp: new Date().toISOString()
      });
    }
  );
});

// 6. Evidence and Project Files Inspector
app.get('/api/analyst/evidence', (_req, res) => {
  try {
    const evidenceDir = path.resolve(process.cwd(), 'evidence');
    const files = fs.existsSync(evidenceDir) ? fs.readdirSync(evidenceDir) : [];
    const contents: Record<string, string> = {};

    for (const f of files) {
      const fullPath = path.join(evidenceDir, f);
      if (fs.statSync(fullPath).isFile()) {
        contents[f] = fs.readFileSync(fullPath, 'utf-8');
      }
    }
    res.json({ files, contents });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Start server with Vite middleware in dev
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static('dist'));
    app.get('*', (_req, res) => {
      res.sendFile(path.resolve(process.cwd(), 'dist/index.html'));
    });
  }

  app.listen(PORT, HOST, () => {
    console.log(`[Retail SQL Analyst Server] Running on http://${HOST}:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error('[Server Start Error]:', err);
  process.exit(1);
});
