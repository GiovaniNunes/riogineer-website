'use client';

import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { heroVideo } from '@/config/hero-video';
import styles from './hero-video.module.css';

const motionQuery = '(prefers-reduced-motion: reduce)';
function subscribeToMotion(callback: () => void) {
  const media = window.matchMedia(motionQuery);
  media.addEventListener('change', callback);
  return () => media.removeEventListener('change', callback);
}
function getMotionPreference() {
  return window.matchMedia(motionQuery).matches;
}
// The server renders a poster with no video source, so reduced-motion visitors
// never download or autoplay the MP4 before their preference has been checked.
function getServerMotionPreference() {
  return true;
}

async function play(video: HTMLVideoElement) {
  if (!video.getAttribute('src')) video.src = heroVideo.src;
  video.muted = true;
  try {
    await video.play();
  } catch {
    /* Autoplay may be blocked. Keep the poster and explicit play control. */
  }
}

export function HeroVideo() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const userPaused = useRef(false);
  const [playing, setPlaying] = useState(false);
  const [failed, setFailed] = useState(false);
  const reducedMotion = useSyncExternalStore(
    subscribeToMotion,
    getMotionPreference,
    getServerMotionPreference,
  );

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (reducedMotion) video.pause();
    else if (!userPaused.current) void play(video);
    return () => video.pause();
  }, [reducedMotion]);

  function togglePlayback() {
    const video = videoRef.current;
    if (!video) return;
    if (!video.paused) {
      userPaused.current = true;
      video.pause();
    } else {
      userPaused.current = false;
      void play(video);
    }
  }

  return (
    <figure className={styles.frame}>
      <div className={styles.media}>
        <video
          id="hero-oil-field-video"
          ref={videoRef}
          width={heroVideo.width}
          height={heroVideo.height}
          poster={heroVideo.poster}
          autoPlay={!reducedMotion}
          muted
          loop
          playsInline
          preload="none"
          aria-label={heroVideo.caption}
          aria-describedby="hero-video-description"
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onError={() => {
            setFailed(true);
            setPlaying(false);
          }}
        />
      </div>
      <div className={styles.controls}>
        <button
          type="button"
          className={styles.control}
          aria-controls="hero-oil-field-video"
          aria-label={playing ? 'Pause oil-field visualization' : 'Play oil-field visualization'}
          onClick={togglePlayback}
          disabled={failed}
        >
          <span aria-hidden="true">{playing ? 'Ⅱ' : '▷'}</span>
          {failed ? 'Unavailable' : playing ? 'Pause' : 'Play'}
        </button>
      </div>
      <p id="hero-video-description" className="srOnly">
        A 3D view of a vessel, connecting lines, a seabed surface and a colored subsurface mesh.
        Playback is silent.
      </p>
      {failed && (
        <p className={styles.message} role="status">
          Video unavailable. The still image remains available.
        </p>
      )}
      <noscript>
        <p className={styles.message}>
          Static preview. Enable JavaScript to play the visualization.
        </p>
      </noscript>
    </figure>
  );
}
