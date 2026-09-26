import Link from 'next/link';
export default function NotFound() {
  return (
    <section className="section">
      <div className="container prose">
        <span className="eyebrow">404 / Page not found</span>
        <h1>This page is not available.</h1>
        <p>The requested address does not match a published page.</p>
        <div className="buttonGroup">
          <Link href="/" className="button primary">
            Return home →
          </Link>
          <Link href="/demonstrations" className="button secondary">
            Explore demonstrations ↗
          </Link>
        </div>
      </div>
    </section>
  );
}
