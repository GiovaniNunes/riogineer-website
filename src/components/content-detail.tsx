import Image from 'next/image';
import Link from 'next/link';
import { PageIntro } from './page-intro';
import { ContentRequired } from './content-required';
import { Workflow } from './workflow';
import { Video } from './video';
import { getContentEntry, type ContentEntry } from '@/lib/content';
import { jsonLd } from '@/lib/metadata';
import { site } from '@/config/site';

export function ContentDetail({ entry }: { entry: ContentEntry }) {
  const data = entry.metadata;
  const isDemo = entry.collection === 'demonstrations';
  const label = isDemo ? 'Demonstrations' : 'Articles';
  const videoSchema =
    data.youtubeId &&
    data.videoTitle &&
    data.videoDescription &&
    data.videoThumbnail &&
    data.videoUploadDate
      ? {
          '@context': 'https://schema.org',
          '@type': 'VideoObject',
          name: data.videoTitle,
          description: data.videoDescription,
          thumbnailUrl: new URL(data.videoThumbnail, site.url).toString(),
          uploadDate: data.videoUploadDate,
          embedUrl: `https://www.youtube-nocookie.com/embed/${data.youtubeId}`,
        }
      : null;
  return (
    <>
      <PageIntro
        eyebrow={`${isDemo ? 'Demonstration' : 'Technical article'} / ${data.status === 'published' ? 'Published' : 'Content in preparation'}`}
        title={data.title}
        description={data.subtitle}
        crumbs={[
          { label, href: `/${entry.collection}` },
          { label: data.title, href: entry.href },
        ]}
      />
      <section className="section">
        <div className="container">
          {data.youtubeId ? (
            <>
              <Video id={data.youtubeId} title={data.videoTitle!} />
              <p className="muted">{data.videoDescription}</p>
            </>
          ) : isDemo ? (
            <ContentRequired media>
              Video and approved demonstration imagery have not yet been supplied. This page
              currently presents an outline, not a completed engineering demonstration.
            </ContentRequired>
          ) : null}
          {videoSchema && (
            <script
              type="application/ld+json"
              dangerouslySetInnerHTML={{ __html: jsonLd(videoSchema) }}
            />
          )}
        </div>
      </section>
      {data.workflow.length > 0 && (
        <section className="section">
          <div className="container">
            <Workflow steps={data.workflow} title={data.title} />
          </div>
        </section>
      )}
      <section className="section">
        <div className="container detailGrid">
          <article className="prose">
            <entry.Content />
            {(data.images.length > 0 || data.diagrams.length > 0) && (
              <>
                <h2>Images and diagrams</h2>
                {[...data.images, ...data.diagrams].map((item) => (
                  <figure key={item.src}>
                    <Image
                      src={item.src}
                      alt={item.alt}
                      width={1200}
                      height={800}
                      style={{ width: '100%', height: 'auto' }}
                    />
                    <figcaption>{item.caption}</figcaption>
                  </figure>
                ))}
              </>
            )}
          </article>
          <aside className="aside">
            <h2>Study information</h2>
            <p>
              <strong>Status</strong>
              <br />
              {data.status === 'published' ? 'Published' : '[CONTENT REQUIRED]'}
            </p>
            <p>
              <strong>Publication date</strong>
              <br />
              {data.date ? <time dateTime={data.date}>{data.date}</time> : '[CONTENT REQUIRED]'}
            </p>
            {data.relatedApplications.length > 0 && (
              <>
                <h2>Related applications</h2>
                <ul>
                  {data.relatedApplications.map((slug) => {
                    const application = getContentEntry('applications', slug)!;
                    return (
                      <li key={slug}>
                        <Link href={application.href}>{application.metadata.title}</Link>
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
            <Link className="textLink" href="/contact">
              Request a demonstration ↗
            </Link>
            <p className="muted">
              This page is the permanent technical reference for the study and its video.
            </p>
          </aside>
        </div>
      </section>
      {data.status === 'published' && data.date && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: jsonLd({
              '@context': 'https://schema.org',
              '@type': 'Article',
              headline: data.title,
              description: data.description,
              datePublished: data.date,
              mainEntityOfPage: new URL(entry.href, site.url).toString(),
            }),
          }}
        />
      )}
    </>
  );
}
