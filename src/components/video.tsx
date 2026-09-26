'use client';
import { useState } from 'react';
import styles from './video.module.css';
export function Video({ id, title }: { id: string; title: string }) {
  const [loaded, setLoaded] = useState(false);
  return (
    <div className={styles.frame}>
      {loaded ? (
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${id}`}
          title={title}
          allow="encrypted-media; picture-in-picture; fullscreen"
          allowFullScreen
          referrerPolicy="strict-origin-when-cross-origin"
        />
      ) : (
        <div className={styles.prompt}>
          <p>{title}</p>
          <p className="muted">Loading this video connects to YouTube.</p>
          <button className="button primary" type="button" onClick={() => setLoaded(true)}>
            Load video <span aria-hidden="true">↗</span>
          </button>
        </div>
      )}
    </div>
  );
}
