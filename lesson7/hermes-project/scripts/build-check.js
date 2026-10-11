import { stat } from 'node:fs/promises';

const required = ['src/server.js', 'src/app.js', 'src/token-service.js', 'public/index.html', 'public/styles.css', 'public/app.js'];
await Promise.all(required.map(async (file) => {
  const info = await stat(new URL(`../${file}`, import.meta.url));
  if (!info.isFile()) throw new Error(`${file} is not a file`);
}));
console.log(`Build check passed: ${required.length} files present`);
