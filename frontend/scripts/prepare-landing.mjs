import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const src = process.argv[2] || path.join(process.env.HOME, 'Downloads/fintelliAI-premium_1.html');
const html = fs.readFileSync(src, 'utf8');
const start = html.indexOf('<div class="view active" id="view-landing">');
const end = html.indexOf('</div><!-- /landing -->');
if (start < 0 || end < 0) {
  console.error('Landing block not found');
  process.exit(1);
}
let chunk = html.slice(start, end + 6);
chunk = chunk
  .replace(/onclick="showView\('view-login'\)"/g, 'data-nav="/login"')
  .replace(/onclick="showView\('view-dashboard'\)"/g, 'data-nav="/dashboard"')
  .replace(/\s+onclick="[^"]*"/g, '');
const out = path.join(__dirname, '../components/fintelli/landing-html.ts');
fs.writeFileSync(
  out,
  `/** Auto-generated from Fintelli design HTML — do not edit by hand */\nexport const LANDING_HTML = ${JSON.stringify(chunk)};\n`
);
console.log('Wrote', out);
