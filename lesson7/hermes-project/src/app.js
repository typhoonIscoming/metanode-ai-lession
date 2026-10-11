import express from 'express';
import cors from 'cors';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = join(__dirname, '..', 'public');

export function createApp({ tokenStore }) {
  const app = express();
  app.use(cors());
  app.use(express.json());
  app.use(express.static(publicDir));

  app.get('/api/health', (_req, res) => {
    res.json({ ok: true, updatedAt: tokenStore.getSnapshot()?.updatedAt ?? null, lastError: tokenStore.getLastError?.() ?? null });
  });

  app.get('/api/tokens', async (req, res) => {
    try {
      let snapshot = tokenStore.getSnapshot();
      if (!snapshot) snapshot = await tokenStore.refreshNow();
      res.json(snapshot);
    } catch (error) {
      res.status(503).json({
        error: 'Token data is temporarily unavailable',
        detail: error.message,
        lastError: tokenStore.getLastError?.() ?? null
      });
    }
  });

  app.post('/api/refresh', async (_req, res) => {
    try {
      const snapshot = await tokenStore.refreshNow();
      res.json(snapshot);
    } catch (error) {
      res.status(503).json({ error: 'Refresh failed', detail: error.message });
    }
  });

  return app;
}
