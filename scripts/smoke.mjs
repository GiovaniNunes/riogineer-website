import assert from 'node:assert/strict';

const origin = process.env.SMOKE_URL || 'http://127.0.0.1:3000';
const paths = [
  '/',
  '/technology',
  '/applications',
  '/applications/process-engineering',
  '/applications/offshore-field-development',
  '/applications/reservoir-engineering',
  '/applications/engineering-knowledge',
  '/field-design',
  '/demonstrations',
  '/demonstrations/three-phase-separator',
  '/demonstrations/process-recycles',
  '/demonstrations/automatic-pfd-generation',
  '/demonstrations/offshore-field-development',
  '/about',
  '/contact',
  '/articles',
];
const titles = new Set();
const imagePaths = new Set();
const links = new Set();
for (const path of paths) {
  const response = await fetch(new URL(path, origin));
  assert.equal(response.status, 200, `${path} must respond with 200`);
  const html = await response.text();
  assert.match(html, /<html[^>]+lang="en"/, `${path} must be in English`);
  assert.equal((html.match(/<h1(?:\s|>)/g) || []).length, 1, `${path} must have exactly one H1`);
  const title = html.match(/<title>([^<]+)<\/title>/)?.[1];
  assert.ok(title, `${path} needs a title`);
  assert.ok(!titles.has(title), `${path} must have a unique title`);
  titles.add(title);
  for (const tag of ['description', 'twitter:title', 'twitter:description', 'twitter:image']) {
    assert.match(html, new RegExp(`<meta name="${tag}" content="[^"]+"`), `${path} needs ${tag}`);
  }
  for (const tag of ['og:title', 'og:description', 'og:image']) {
    assert.match(
      html,
      new RegExp(`<meta property="${tag}" content="[^"]+"`),
      `${path} needs ${tag}`,
    );
  }
  assert.match(html, /<link rel="canonical" href="http/, `${path} needs a canonical URL`);
  assert.match(
    html,
    /<meta name="robots" content="noindex/,
    `${path} must remain noindex in development`,
  );
  assert.ok(!html.includes('googletagmanager.com'), 'Analytics must remain unconfigured');
  assert.ok(!html.includes('<iframe'), 'No unsupplied video may be embedded');
  if (path.startsWith('/demonstrations/')) {
    assert.ok(html.includes('[CONTENT REQUIRED]'), 'Unfinished demonstrations need placeholders');
    assert.ok(!html.includes('"@type":"VideoObject"'), 'No VideoObject for unavailable videos');
    assert.ok(!html.includes('"@type":"Article"'), 'No published Article schema for an outline');
  }
  for (const match of html.matchAll(/<a[^>]+href="(\/[^"?#]*)/g)) links.add(match[1]);
  const image = html.match(/<meta property="og:image" content="([^"]+)"/)?.[1];
  imagePaths.add(new URL(image).pathname);
}
for (const path of links)
  assert.ok(paths.includes(path), `Internal link has no known content page: ${path}`);
for (const path of imagePaths) {
  const response = await fetch(new URL(path, origin));
  assert.equal(response.status, 200, `Share card ${path} must render`);
  assert.match(response.headers.get('content-type'), /image\/png/);
  const bytes = new Uint8Array(await response.arrayBuffer());
  assert.deepEqual(
    [...bytes.slice(0, 8)],
    [137, 80, 78, 71, 13, 10, 26, 10],
    'Share card must be a real PNG',
  );
}
assert.equal((await fetch(new URL('/applications/not-a-real-application', origin))).status, 404);
assert.equal((await fetch(new URL('/demonstrations/not-a-real-study', origin))).status, 404);
const robots = await (await fetch(new URL('/robots.txt', origin))).text();
assert.match(robots, /Disallow: \//);
const sitemap = await (await fetch(new URL('/sitemap.xml', origin))).text();
assert.ok(!sitemap.includes('<loc>'), 'Development sitemap must not advertise URLs');
const contact = await fetch(new URL('/api/contact', origin), {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Origin: origin },
  body: JSON.stringify({
    name: 'Test Engineer',
    company: 'Example Organization',
    email: 'engineer@example.com',
    country: 'Brazil',
    interest: 'Process Engineering',
    message: 'Validation check only; no message delivery.',
    website: '',
  }),
});
assert.equal(contact.status, 503);
assert.equal((await contact.json()).code, 'DELIVERY_DISABLED');
console.log(
  `Passed: ${paths.length} pages, ${imagePaths.size} PNG social cards, internal links, 404s, preview indexing, and disabled contact delivery.`,
);
