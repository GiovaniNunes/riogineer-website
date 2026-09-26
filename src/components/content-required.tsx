import styles from './placeholder.module.css';
export function ContentRequired({
  children,
  media = false,
}: {
  children: React.ReactNode;
  media?: boolean;
}) {
  return (
    <div className={`${styles.placeholder} ${media ? styles.media : ''}`}>
      {media && (
        <span className={styles.mediaIcon} aria-hidden="true">
          [ / ]
        </span>
      )}
      <span className={styles.label}>[CONTENT REQUIRED]</span>
      <p>{children}</p>
    </div>
  );
}
