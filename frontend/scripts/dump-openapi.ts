import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const BACKEND_URL = process.env.VITE_API_URL || 'http://localhost:8000';

async function main() {
  const url = `${BACKEND_URL}/openapi.json`;
  console.log(`[dump-openapi] Fetching from: ${url}`);

  const response = await fetch(url);
  if (!response.ok) {
    console.error(`Failed to fetch OpenAPI spec: ${response.status}`);
    process.exit(1);
  }

  const spec = await response.json();
  const outPath = resolve(import.meta.dirname, '../openapi.json');
  writeFileSync(outPath, JSON.stringify(spec, null, 2), 'utf-8');
  console.log(`[dump-openapi] Written to: ${outPath}`);
}

main();
