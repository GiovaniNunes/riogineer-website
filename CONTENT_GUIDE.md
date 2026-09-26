# Content guide

Write every page, caption, title, transcript and metadata field in English. Start from approved engineering information. Never invent clients, customer projects, commercial agreements, ownership, measured performance or engineering results. Use the exact marker **[CONTENT REQUIRED]** whenever factual information is missing.

## Add a demonstration

1. Copy an existing `.mdx` file in `content/demonstrations/`.
2. Choose a lowercase, hyphenated filename such as `approved-study.mdx`. Its URL is `/demonstrations/approved-study`.
3. Edit YAML frontmatter and the Markdown sections using the structure below.
4. Add authorized images under `public/images/` or diagrams under `public/diagrams/`.
5. Run `npm run content:generate` (or restart `npm run dev`) to discover the file.
6. Run `npm run typecheck` and `npm run build` before publication.

Use Markdown for ordinary content; the supplied MDX components provide professional placeholders and conceptual workflows without needing application code changes.

```mdx
---
title: '[CONTENT REQUIRED]'
subtitle: '[CONTENT REQUIRED]'
summary: '[CONTENT REQUIRED]'
description: '[CONTENT REQUIRED]'
order: 5
status: awaiting-content
relatedApplications:
  - process-engineering
workflow: []
images: []
diagrams: []
---

## Engineering problem

<ContentRequired>Approved problem statement and scope.</ContentRequired>

## Input information

<ContentRequired>Authorized inputs, units and boundary conditions.</ContentRequired>

## Digital Engineer actions and workflow

<ContentRequired>Verified action sequence.</ContentRequired>

## Engineering models used

<ContentRequired>Models, assumptions, simulator details and validation.</ContentRequired>

## Results

<ContentRequired>Verified engineering results and supporting checks.</ContentRequired>

## Technical discussion

<ContentRequired>Technical explanation, applicability and limitations.</ContentRequired>

## Technical summary or transcript

<ContentRequired>Approved summary or video transcript.</ContentRequired>
```

Do not place `[CONTENT REQUIRED]` inside machine-readable date, URL or YouTube ID fields. Omit these optional fields when unknown; templates render placeholders for missing demonstration media/date. Quote YAML strings containing brackets or colons.

## Frontmatter fields

| Field                            | Meaning                                                                             |
| -------------------------------- | ----------------------------------------------------------------------------------- |
| `title`, `subtitle`              | Page identity; title is also used in cards and metadata                             |
| `summary`                        | Short library/application card description                                          |
| `description`                    | Unique SEO and social description                                                   |
| `order`                          | Optional numeric order in the library                                               |
| `status`                         | `conceptual`, `awaiting-content`, or `published`                                    |
| `date`                           | Actual publication date, quoted as `YYYY-MM-DD`; required for `published`           |
| `workflow`                       | Ordered list of labels; rendered as a **conceptual** workflow                       |
| `relatedApplications`            | Existing application filename slugs                                                 |
| `images`, `diagrams`             | Lists of `{ src, alt, caption }` using local `/images/...` or `/diagrams/...` paths |
| `socialImage`                    | Optional approved local image overriding the typography-only social card            |
| `youtubeId`                      | Actual 11-character YouTube video ID; omit until available                          |
| `videoTitle`, `videoDescription` | Required when a video ID is provided                                                |
| `videoThumbnail`                 | Approved local video thumbnail; needed for VideoObject                              |
| `videoUploadDate`                | Actual ISO timestamp with timezone; needed for VideoObject                          |

The page renderer provides video, workflow, technical text, figures, related applications and publication metadata. It never creates VideoObject data for a placeholder. Loading YouTube is opt-in through a “Load video” button; no YouTube request occurs before that click.

Use `status: published` only after technical review, replacing missing sections and supplying a real publication date. The status is an editorial assertion; the schema can check formatting but cannot verify technical truth. Keep an incomplete demonstration `awaiting-content`; it remains visible as an outline but is `noindex` and excluded from the production sitemap.

## Add applications and articles

- Application files belong in `content/applications/`; URLs are `/applications/<filename>`.
- Article files belong in `content/articles/`; URLs are `/articles/<filename>`.
- Use the same frontmatter conventions and the content generator. The article library is available at `/articles`, outside the seven-item main navigation.
- Application and technical article text should explain what the concept is, the problem it addresses, how it works, inputs, models, outputs, limitations and relevant industries.
- New dedicated top-level technical URLs can reuse these templates when substantive approved content is available; coordinate those route additions with a developer.

## Editorial rules

- Describe conceptual workflows as conceptual. Never use fabricated numerical examples as evidence of engineering results.
- Keep calculations associated with physical/mathematical models and appropriate computational tools. Do not imply an LLM independently performs deterministic engineering calculations.
- RIOGINEER LTDA and Rio Petróleo are separate companies. Field Design is a distinct calculation, conceptual design and optimization platform. No ownership or licensing arrangement should be inferred.
- Keep private repositories, internal documents, customer information, proprietary datasets, credentials and unpublished confidential studies out of the public content tree.
- Do not import scripts, remote MDX or arbitrary components. MDX is executable code and needs repository review.
- Main page titles are supplied by the template. Start body sections at `##`, then `###` for subsections. Do not add a second H1.
- Supply descriptive alternative text and captions for every figure. Important explanations must also exist as HTML text.
- Do not insert credentials or analytics identifiers into content. Ask the developer to configure approved integrations through environment variables.

## Replacing the temporary brand

Global visual changes belong in `src/styles/tokens.css`. Company wording and logo references belong in `src/config/brand.ts`. Add the official logo only after it is supplied and authorized. You do not need to edit individual page components to change brand colors, typography or spacing.

## Application card illustrations

Application cards accept an optional `cardIllustration` frontmatter object with `src` (an approved local `/diagrams/` or `/images/` asset), required descriptive `alt`, and optional `caption`. Add it only when a verified illustration is available. No illustration is currently supplied or implied.

The shared card component renders it in a responsive 16:9 frame using `object-fit: contain` so technical labels are not cropped. The aspect ratio is centralized in `--application-illustration-ratio`. Cards without media retain the existing text layout, with no blank media placeholder. No component changes are required to add a later illustration.

For the general Digital Engineer process, use `<DigitalEngineerWorkflow />` in MDX. It shares the canonical seven-step sequence in `src/config/workflow.ts` with the homepage hero. Keep domain-specific engineering study workflows distinct and as approved.
