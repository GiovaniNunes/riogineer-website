import Image from 'next/image';
import Link from 'next/link';
import type { ContentEntry } from '@/lib/content';
import styles from './cards.module.css';
export function ContentCards({
  entries,
  kind,
}: {
  entries: ContentEntry[];
  kind: 'application' | 'demonstration' | 'article';
}) {
  return (
    <div className={styles.grid}>
      {entries.map((entry, index) => (
        <article key={entry.slug} className={styles.card}>
          <div className={styles.topline}>
            <span>
              {kind.toUpperCase()} / {String(index + 1).padStart(2, '0')}
            </span>
            {entry.metadata.status === 'awaiting-content' && (
              <span className={styles.status}>[CONTENT REQUIRED]</span>
            )}
          </div>
          <h3>
            <Link href={entry.href}>{entry.metadata.title}</Link>
          </h3>
          <p>{entry.metadata.summary}</p>
          {kind === 'application' && entry.metadata.cardIllustration && (
            <figure className={styles.illustration}>
              <div className={styles.illustrationFrame}>
                <Image
                  src={entry.metadata.cardIllustration.src}
                  alt={entry.metadata.cardIllustration.alt}
                  fill
                  sizes="(max-width: 650px) 90vw, 45vw"
                  className={styles.illustrationImage}
                />
              </div>
              {entry.metadata.cardIllustration.caption && (
                <figcaption>{entry.metadata.cardIllustration.caption}</figcaption>
              )}
            </figure>
          )}
          <Link href={entry.href} className="textLink">
            {kind === 'application'
              ? 'Explore application'
              : kind === 'article'
                ? 'Read article'
                : 'Explore demonstration'}{' '}
            <span aria-hidden="true">↗</span>
          </Link>
        </article>
      ))}
    </div>
  );
}
