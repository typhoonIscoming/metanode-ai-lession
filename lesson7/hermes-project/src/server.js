import { createApp } from './app.js';
import { TokenStore } from './token-service.js';

const port = Number(process.env.PORT ?? 3000);
const refreshMs = Number(process.env.REFRESH_MS ?? 60_000);
const limit = Number(process.env.TOKEN_LIMIT ?? 100);

const tokenStore = new TokenStore({ refreshMs, limit });
tokenStore.start();

const app = createApp({ tokenStore });
const server = app.listen(port, '0.0.0.0', () => {
  console.log(`Binance token heatmap running at http://localhost:${port}`);
  console.log(`Refreshing Binance data every ${Math.round(refreshMs / 1000)}s, limit=${limit}`);
});

function shutdown() {
  tokenStore.stop();
  server.close(() => process.exit(0));
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
