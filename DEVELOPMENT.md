# Development architecture

## Rendering and routes

Next.js App Router and React Server Components render indexable HTML for corporate and technical pages. Client components are limited to navigation state, contact submission and optional click-to-load YouTube playback. Conceptual diagrams are semantic HTML/CSS with a text equivalent; no engineering calculation or simulator runs in the website.

`src/app` contains page routes, metadata routes and the contact POST handler. `src/components` contains shared layout, cards, diagrams, placeholders and content rendering. `content/applications`, `content/demonstrations` and `content/articles` hold repository-authored MDX.

`npm run content:generate` discovers MDX filenames and generates static imports in `src/generated/content-registry.ts`. It runs before development, build and type checking. The MDX compiler exposes YAML frontmatter as `frontmatter`. Zod checks that metadata in `src/lib/content.ts`, including related-application references, before rendering. Invalid content fails the build rather than silently publishing incomplete metadata. Unknown detail routes return 404.

Editing existing MDX works with hot reload. After adding, renaming or removing a file, run `npm run content:generate` or restart the development server. No application-code changes are needed to publish a new MDX record. Only trusted repository-authored MDX is compiled: MDX can execute code, so never accept it from public forms or remote URLs.

The article template supports future technical publications. Future dedicated root routes such as `/digital-engineer` and `/reservoir-proxy-models` can reuse the existing page intro, MDX renderer, diagrams and metadata helper when approved content is available. No empty SEO landing pages are generated for these future topics.

## Centralized visual identity

| Source                         | Responsibility                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `src/styles/tokens.css`        | Colors, typography, spacing, type scale, content widths, radii, motion, diagram dimensions and social-card metrics |
| `src/config/brand.ts`          | Company names, descriptor and optional official logo reference                                                     |
| `src/config/navigation.ts`     | Main navigation                                                                                                    |
| `src/config/pages.ts`          | Static sitemap entries and social-card copy                                                                        |
| `src/app/globals.css`          | Reset, shared semantic styles, buttons, containers, prose and reduced-motion behavior                              |
| Component `*.module.css` files | Local layout using shared tokens                                                                                   |

The current RIOGINEER wordmark is live text, not a final official logo. To replace it, add the authorized asset under `public/brand/` and set `brand.logo` to `{ src, width, height, alt }`. The same Brand component serves header and footer. Never scatter logo paths or brand colors across components.

`content:generate` also reads the CSS tokens into `src/generated/design-tokens.ts`, consumed by the social-card renderer. The generated files are ignored; **edit the source tokens, not the generated files**. Run the generator after changing tokens to refresh social cards. Ordinary CSS hot reload updates the website immediately.

Social cards are 1200×630 PNGs rendered through Next.js ImageResponse at `/og/...`. Each card uses the current page/record's actual title and subtitle. Incomplete demonstration cards display `[CONTENT REQUIRED]`. They are typography-only assets, not engineering output. Set a record's `socialImage` to use an approved local image instead. The server image renderer uses its bundled sans-serif font, controlled by the shared image font token; adding an exact custom font requires supplying a licensed font file to ImageResponse.

## Development origin, metadata and indexing

`src/config/site.ts` reads server-side `SITE_URL` and `SITE_INDEXABLE`.

- Default `SITE_URL`: `http://localhost:3000` (development only).
- Default `SITE_INDEXABLE`: false, including a production-mode build.
- No official domain is assumed; there are no guessed domains or contact addresses.
- Configuration rejects URL credentials, paths, queries, fragments and unsupported schemes.
- Indexing cannot be enabled for a loopback origin or plain HTTP origin.
- Canonical URLs, social URLs and structured-data URLs use the configured origin.
- Public HTTPS origin and indexing values require a rebuild because pages are statically generated.

`pageMetadata` provides titles, descriptions, canonical URLs, OpenGraph and social cards. `robots.ts` intentionally blocks local/preview indexing; enabling production indexing switches to an allow-public-content policy. `sitemap.ts` excludes unpublished demonstrations/articles and invents no modification dates.

Organization, founder Person and BreadcrumbList data use supplied facts. VideoObject requires an actual video ID, title, description, thumbnail and upload timestamp. Article data requires published status and an actual publication date. No unsupported SoftwareApplication ownership, license, rating, price or version data is emitted.

## Contact form

Public field choices and size limits live in `src/config/contact.ts`; the Zod schema lives in `src/lib/validation.ts`. `POST /api/contact` delegates to `handleContactRequest`.

The handler:

1. Requires an Origin matching configured `SITE_URL` (and local loopback aliases only in local configuration).
2. Applies a small process-wide request ceiling, without retaining IP addresses or form data.
3. Requires JSON and enforces a 24 KiB body limit while streaming, even without Content-Length.
4. Validates field types, required values, lengths, email syntax and the interest enum; rejects extra properties.
5. Rejects a populated honeypot.
6. Returns **503 / DELIVERY_DISABLED** for valid requests. It never claims success or calls an email provider.

Missing/foreign origin returns 403; rate ceiling 429; wrong media type 415; oversized body 413; malformed JSON/honeypot 400; field errors 422. Responses are `no-store`. The browser retains form values after failure and displays the server result accessibly. Without JavaScript, the form uses POST and cannot leak submitted fields into the URL.

The process-wide ceiling is a basic development safeguard, **not a shared serverless rate limiter**. Before enabling delivery, implement provider-backed or shared abuse protection, select a delivery provider, configure verified sender/recipient details with server-only environment variables, add approved privacy wording and test failure/retry behavior. Never trust arbitrary forwarded host/IP headers for security decisions. Avoid logging submission bodies. There is intentionally no `EMAIL_ENABLED` flag or placeholder provider that could accidentally activate delivery.

The website does not currently persist submissions. External hosting infrastructure may have its own access logs; configure those as part of the eventual deployment review.

## Secrets and external integrations

`.env.local`, other real env files, npm's local cache, build output and hosting metadata are ignored. `.env.example` contains only documented non-secret configuration. Never store credentials in MDX, JavaScript bundles, committed config, test fixtures or documentation. Public identifiers and secret credentials are distinct; neither analytics nor verification IDs are configured yet.

There is no Google Analytics script or consent mechanism in Version 1. Future analytics should be implemented behind server-read environment configuration and an approved privacy/consent decision. Search verification can later be added through Next.js metadata using environment variables; do not invent identifiers.

Security headers disable framing and unnecessary device permissions, prevent MIME sniffing and set a referrer policy. A production CSP should be adapted to the actual deployment and any approved third-party integrations rather than weakening it with speculative provider allowlists.

## Toolchain and validation

Dependencies are pinned in `package.json` and `package-lock.json`. Use `npm ci` for repeatable installs. ESLint 9 is retained because the React/import/accessibility plugins bundled with the selected Next.js lint configuration declare ESLint 9 peer support; ESLint 10 is not forced past those constraints. Reassess together when upgrading the framework/tooling.

Tests cover disabled-delivery behavior, validation errors, origin checks, malformed and oversized requests, honeypot handling, rate limiting, content metadata requirements and domain/indexing safety. Production build additionally compiles all MDX and prerenders routes/social cards. CI runs tests, lint, TypeScript and build.

The implementation uses no external fonts, stock imagery, AI image generator, runtime content service, database or CMS. Browser visual testing has not been automated in this version; responsive CSS, reduced-motion rules, semantic markup and accessibility lint are implemented. HTTP smoke checks can be run against a started server with `npm run smoke`.

## Approved design refinements

Homepage internal sections use `--home-section-space` and `--home-section-heading-gap` at 82% of their original spacing. The final contact CTA uses `--home-cta-section-space` at 65% of the original section padding, retaining its heading size and button. These scoped settings do not alter the hero, header, palette, typography, other pages or dark demonstration section.

Both general Digital Engineer diagrams consume the seven steps from `src/config/workflow.ts`. Domain-specific application/study sequences remain separate. `cardIllustration` is an optional application metadata field rendered by the shared card component; see `CONTENT_GUIDE.md`.

## Homepage video visual evaluation

`HeroVideo` replaces the right-hand hero workflow panel. The full `public/videos/digital-twin-oil-field.mp4` file is used unchanged: approximately 34.3 seconds, 848×436, 60 fps and 8.17 MB. It has not been trimmed, re-encoded or optimized. `src/config/hero-video.ts` holds the source, poster, intrinsic dimensions and accessible video label. No caption is displayed. The JPEG poster is extracted from its first frame; it is a still-image fallback, not an edited video. The original source outside this repository is untouched.

The desktop hero allocates 45% of its column space to text and 55% to video, with a reduced gap; the existing mobile breakpoint stacks the video after the text and CTAs. The full image is shown without cropping, with intrinsic dimensions reserving its space. Frame styling uses existing palette tokens and `--hero-video-frame-padding`.

The client checks `prefers-reduced-motion` before assigning the video source. Normal playback uses autoplay, muted, loop and playsInline. Reduced-motion visitors receive the poster without automatically downloading the MP4 and may explicitly choose Play. A change to reduced motion pauses playback. The native button is keyboard accessible, tracks actual play/pause events, and supports manual playback when autoplay is blocked. There are no conventional player controls or unmute control. The seven-step Digital Engineer workflow remains in the following Meet section.

The full source is intentionally retained for visual review; its current size and visible loop transition are not production optimization decisions. Any later edit or encoding requires the user's next selection. No claims of live data, validated simulation results or model authorship are attached to this footage.
