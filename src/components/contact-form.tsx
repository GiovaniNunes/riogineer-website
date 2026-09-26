'use client';
import { useState, useRef, type FormEvent } from 'react';
import { contactAvailability, contactLimits, interests } from '@/config/contact';
import type { ContactFieldErrors } from '@/lib/validation';
import styles from './contact-form.module.css';
export function ContactForm() {
  const [errors, setErrors] = useState<ContactFieldErrors>({});
  const [status, setStatus] = useState('');
  const [pending, setPending] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setErrors({});
    setStatus('');
    try {
      const body = Object.fromEntries(new FormData(event.currentTarget));
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const result = (await response.json()) as { errors?: ContactFieldErrors; message?: string };
      setErrors(result.errors || {});
      setStatus(result.message || 'Your message was not sent. Please try again later.');
      if (result.errors) {
        const field = Object.keys(result.errors)[0];
        formRef.current?.querySelector<HTMLElement>(`[name="${field}"]`)?.focus();
      }
    } catch {
      setStatus('Unable to connect. Your message was not sent or saved.');
    } finally {
      setPending(false);
    }
  }
  return (
    <form
      method="post"
      action="/api/contact"
      onSubmit={submit}
      ref={formRef}
      className={styles.form}
      aria-describedby="delivery-notice"
      aria-busy={pending}
    >
      <div id="delivery-notice" className={`notice ${styles.full}`}>
        <p>
          <strong>Delivery is currently disabled.</strong>
        </p>
        <p>{contactAvailability.message}</p>
        <p>Please do not enter confidential engineering information.</p>
      </div>
      <p className={`${styles.help} ${styles.full}`}>All fields are required.</p>
      {(
        [
          ['name', 'Name', 'text', 'name', contactLimits.name],
          ['company', 'Company', 'text', 'organization', contactLimits.company],
          ['email', 'Corporate email', 'email', 'email', contactLimits.email],
          ['country', 'Country', 'text', 'country-name', contactLimits.country],
        ] as const
      ).map(([name, label, type, autoComplete, maxLength]) => (
        <div className={styles.field} key={name}>
          <label htmlFor={`contact-${name}`}>{label}</label>
          <input
            id={`contact-${name}`}
            name={name}
            type={type}
            autoComplete={autoComplete}
            maxLength={maxLength}
            required
            aria-invalid={Boolean(errors[name])}
            aria-describedby={errors[name] ? `error-${name}` : undefined}
          />
          {errors[name] && (
            <p className={styles.error} id={`error-${name}`}>
              {errors[name]?.[0]}
            </p>
          )}
        </div>
      ))}
      <div className={`${styles.field} ${styles.full}`}>
        <label htmlFor="contact-interest">Area of interest</label>
        <select
          name="interest"
          id="contact-interest"
          required
          defaultValue=""
          aria-invalid={Boolean(errors.interest)}
          aria-describedby={errors.interest ? 'error-interest' : undefined}
        >
          <option value="" disabled>
            Select an area of interest
          </option>
          {interests.map((interest) => (
            <option key={interest}>{interest}</option>
          ))}
        </select>
        {errors.interest && (
          <p id="error-interest" className={styles.error}>
            {errors.interest[0]}
          </p>
        )}
      </div>
      <div className={`${styles.field} ${styles.full}`}>
        <label htmlFor="contact-message">Message</label>
        <textarea
          name="message"
          id="contact-message"
          required
          minLength={10}
          maxLength={contactLimits.message}
          aria-invalid={Boolean(errors.message)}
          aria-describedby={errors.message ? 'error-message' : 'message-help'}
        />
        <p id="message-help" className={styles.help}>
          10–5,000 characters. Describe your engineering application.
        </p>
        {errors.message && (
          <p id="error-message" className={styles.error}>
            {errors.message[0]}
          </p>
        )}
      </div>
      <div className={styles.honeypot} aria-hidden="true">
        <label htmlFor="contact-website">Leave this field empty</label>
        <input id="contact-website" name="website" tabIndex={-1} autoComplete="off" />
      </div>
      <div className={styles.full}>
        <button className="button primary" type="submit" disabled={pending}>
          {pending ? 'Checking entries…' : 'Request a demonstration'}{' '}
          <span aria-hidden="true">↗</span>
        </button>
      </div>
      <div className={styles.full} role="status" aria-live="polite">
        {status && <p className={styles.status}>{status}</p>}
      </div>
      <noscript>
        <p className={styles.help}>
          JavaScript is required to validate this form. Message delivery is currently disabled.
        </p>
      </noscript>
    </form>
  );
}
