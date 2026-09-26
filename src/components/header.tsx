'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Brand } from './brand';
import { navigation } from '@/config/navigation';
import styles from './layout.module.css';

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className={styles.header}>
      <a href="#main-content" className={styles.skip}>
        Skip to content
      </a>
      <div className={`container ${styles.headerInner}`}>
        <Brand />
        <button
          type="button"
          className={styles.menuButton}
          aria-expanded={open}
          aria-controls="primary-navigation"
          onClick={() => setOpen(!open)}
        >
          {open ? 'Close' : 'Menu'} <span aria-hidden="true">{open ? '−' : '+'}</span>
        </button>
        <nav
          id="primary-navigation"
          aria-label="Main navigation"
          className={styles.nav}
          data-open={open}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              setOpen(false);
              document
                .querySelector<HTMLButtonElement>('[aria-controls="primary-navigation"]')
                ?.focus();
            }
          }}
        >
          {navigation.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              aria-current={
                pathname === href || (href !== '/' && pathname.startsWith(`${href}/`))
                  ? 'page'
                  : undefined
              }
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
