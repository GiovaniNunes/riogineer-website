import Link from 'next/link';
import { Brand } from './brand';
import { brand } from '@/config/brand';
import { navigation } from '@/config/navigation';
import styles from './layout.module.css';
export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className="container">
        <div className={styles.footerTop}>
          <div>
            <Brand />
            <p>Engineering knowledge, physical models and artificial intelligence. Connected.</p>
          </div>
          <nav className={styles.footerLinks} aria-label="Footer navigation">
            {navigation
              .filter((item) => item.href !== '/')
              .map((item) => (
                <Link key={item.href} href={item.href}>
                  {item.label}
                </Link>
              ))}
          </nav>
        </div>
        <div className={styles.footerBottom}>
          <span>
            © {new Date().getFullYear()} {brand.legalName}
          </span>
          <span>Engineering Intelligence. Built on Physics. Powered by AI.</span>
        </div>
      </div>
    </footer>
  );
}
