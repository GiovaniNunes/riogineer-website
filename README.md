# RIOGINEER corporate website

English-only corporate website for RIOGINEER LTDA, built with Next.js App Router, React, TypeScript and MDX. It presents the Digital Engineer concept, technology, applications, Field Design, demonstrations, founders and contact form.

The implementation follows `WEBSITE_SPECIFICATION.md` and the subsequent approved instructions. Section 26's incomplete sentence is superseded by: **never expose credentials in client-side code or commit secrets; use server-side environment variables when external credentials are needed.** The original specification is preserved.

## Local development

Use Node.js 22 LTS or a compatible newer version (`.nvmrc` selects 22), and npm.

```bash
npm ci --cache .local/npm-cache
npm run dev
```

Open **http://127.0.0.1:3000**. The server binds to loopback only. If port 3000 is occupied, use the exact URL printed by Next.js and update `SITE_URL` to match the selected port.

No environment file is required for local development. The default metadata origin is **http://localhost:3000**, a development placeholder, **not an official RIOGINEER domain**. Both `localhost:3000` and `127.0.0.1:3000` are accepted as local contact origins.

To override configuration, copy `.env.example` to `.env.local` and edit its values. `.env.local` is ignored by Git. Never put secrets in variables beginning with `NEXT_PUBLIC_`, application source, content files or documentation. The development origin contains no external credentials.

## Commands

```bash
npm test               # Contact security, content validation, metadata configuration
npm run lint           # Next.js, React, TypeScript and accessibility lint rules
npm run typecheck      # Next.js route generation and TypeScript checks
npm run build          # Production build; generates MDX registry and social-card tokens
npm start              # Serve the built production website locally
npm run content:generate  # Discover new/renamed MDX files and refresh shared image tokens
```

Stop the development server before running `npm start` on the same port. Development and production build output are separated by Next.js.

## Version 1 behavior

- Seven navigation entries, four application pages and four demonstration detail pages.
- Reusable MDX articles and demonstration architecture; no CMS or database.
- Centralized colors, fonts, spacing and brand references.
- Accessible conceptual HTML/CSS diagrams and reduced-motion support.
- `[CONTENT REQUIRED]` for missing media, implementation details and verified results.
- Typography-only social cards containing page titles, not invented software screenshots.
- Contact validation runs server-side. **Delivery is disabled.** Valid submissions receive HTTP 503 with `DELIVERY_DISABLED`; no email is sent, no message is stored, and submission bodies are not logged by application code.
- No analytics scripts, search-verification IDs or real email provider are configured.
- The local/preview site deliberately uses `noindex`, a disallow-all robots file and an empty sitemap. This is temporary development configuration.

## Deployment preparation: GitHub and Vercel

No remote repository, Vercel project, account connection or deployment has been created by this implementation.

1. Place this repository in the approved GitHub repository without committing secrets.
2. Import it into Vercel, using the repository root and the Next.js preset.
3. Use `npm ci` for installation and `npm run build` for the build. Select Node.js 22.
4. For preview deployments, configure `SITE_URL` as the actual preview origin and keep `SITE_INDEXABLE=false`.
5. Once the official domain is selected, set `SITE_URL` to that approved HTTPS origin. Rebuild to regenerate canonical URLs, metadata and social links.
6. After content review, set `SITE_INDEXABLE=true` for production only. The production robots policy allows public crawlers and excludes `/api/`; the sitemap includes static corporate pages, application pages, and published demonstration/article records. Unfinished demonstrations remain `noindex` and outside the sitemap.
7. Keep email delivery disabled until the provider, credentials, contact recipient, data-handling wording and shared abuse controls have been implemented and tested. Setting an environment variable alone cannot enable delivery.

GitHub Actions runs dependency installation, tests, lint, type checks and the production build. No deployment credentials are required for CI.

## Documentation

The **Digital Engineer specification and review** workspace is available at
`/digital-engineer`. It requires the separate local Python service. See
[engine/README.md](engine/README.md) for exact setup commands, API endpoints,
reference comparisons, model limitations and tests, and
[contracts/README.md](contracts/README.md) for the versioned data contracts.
See [MILESTONE_2.md](MILESTONE_2.md) for PDF/text interpretation, provider configuration,
mandatory review/approval, provenance, limits and exact local commands. Interpretation
requires server-side provider configuration; no simulated interpretation is used.
Existing corporate pages remain independent of the engine.

- `DEVELOPMENT.md`: architecture, configuration, visual identity, contact security and validation.
- `CONTENT_GUIDE.md`: authoring applications, demonstrations and articles.
- `CONTENT_REQUIRED.md`: outstanding information and release configuration.

All project work belongs inside this repository. RIOGINEER, Rio Petróleo and Field Design remain explicitly distinguished.
