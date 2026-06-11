import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = process.argv[2];
if (!htmlPath) {
  console.error('Usage: node extract-fintelli-css.mjs <path-to-html>');
  process.exit(1);
}
const html = fs.readFileSync(htmlPath, 'utf8');
const m = html.match(/<style>([\s\S]*?)<\/style>/i);
if (!m) {
  console.error('No <style> block found');
  process.exit(1);
}
const out = path.join(__dirname, '../styles/fintelli.css');
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, m[1].trim() + '\n');
console.log('Wrote', out, `(${m[1].length} chars)`);
