import Image from 'next/image';
import Link from 'next/link';
import { brand } from '@/config/brand';
import styles from './layout.module.css';

export function Brand() {
  return (
    <Link href="/" className={styles.brand} aria-label={`${brand.name} home`}>
      {brand.logo ? (
        <Image {...brand.logo} alt={brand.logo.alt} />
      ) : (
        <span className={styles.wordmark}>{brand.name}</span>
      )}
      <span className={styles.descriptor}>{brand.descriptor}</span>
    </Link>
  );
}
