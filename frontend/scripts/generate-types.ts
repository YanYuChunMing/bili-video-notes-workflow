import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import openapiTS, { astToString } from 'openapi-typescript';

const OUTPUT_FILE = resolve(import.meta.dirname, '../src/types/api.generated.ts');
const STATIC_SPEC = resolve(import.meta.dirname, '../openapi.json');
const BACKEND_URL = process.env.VITE_API_URL || 'http://localhost:8000';

async function main() {
  let spec: Record<string, unknown>;

  if (existsSync(STATIC_SPEC)) {
    console.log(`[generate-types] Using static spec: ${STATIC_SPEC}`);
    spec = JSON.parse(readFileSync(STATIC_SPEC, 'utf-8'));
  } else {
    const url = `${BACKEND_URL}/openapi.json`;
    console.log(`[generate-types] Fetching spec from: ${url}`);
    const response = await fetch(url);
    if (!response.ok) {
      console.error(`Failed to fetch OpenAPI spec: ${response.status}`);
      process.exit(1);
    }
    spec = (await response.json()) as Record<string, unknown>;
  }

  const ast = await openapiTS(spec as any, {
    defaultNonNullable: true,
  });

  const output = ast.map(node => astToString(node)).join('\n\n');

  console.log(`[generate-types] Generated ${output.length} chars`);

  const dir = resolve(OUTPUT_FILE, '..');
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  writeFileSync(OUTPUT_FILE, output, 'utf-8');
  console.log(`[generate-types] Written to: ${OUTPUT_FILE}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
