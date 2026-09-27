import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { z } from 'zod';
import { InterpretationError } from './http';
export const MAX_PDF_BYTES = 5 * 1024 * 1024;
const extractedSchema = z.strictObject({
  pages: z
    .array(z.strictObject({ page: z.number().int().positive(), text: z.string().max(60000) }))
    .min(1)
    .max(40),
  empty_pages: z.array(z.number().int().positive()),
});
const errors: Record<string, string> = {
  PDF_NO_TEXT:
    'This PDF contains no usable machine-readable text. OCR is not supported. Paste the specification or upload a text-based PDF.',
  ENCRYPTED_PDF: 'Encrypted PDFs are unsupported. Upload an unencrypted text-based PDF.',
  PDF_PAGE_LIMIT: 'PDFs must contain 1–40 pages.',
  PDF_TEXT_LIMIT: 'PDF extracted text exceeds 60,000 characters. Provide a shorter specification.',
  PDF_NOT_CONFIGURED:
    'PDF extraction is not configured. Install the interpretation Python dependencies.',
  INVALID_PDF: 'The PDF could not be read. Upload a valid, unencrypted text-based PDF.',
};
export async function extractPdf(file: File) {
  if (file.size > MAX_PDF_BYTES)
    throw new InterpretationError('PDF_SIZE_LIMIT', 'PDF exceeds the 5 MiB upload limit.', 413);
  if (
    !file.name.toLowerCase().endsWith('.pdf') ||
    (file.type !== 'application/pdf' && file.type !== '')
  )
    throw new InterpretationError('PDF_TYPE', 'Only PDF documents are supported.', 415);
  const data = Buffer.from(await file.arrayBuffer());
  if (data.subarray(0, 5).toString('ascii') !== '%PDF-')
    throw new InterpretationError('INVALID_PDF', errors.INVALID_PDF);
  // Python is a runtime dependency, not an asset for Next.js to trace/bundle.
  const python = process.env.RIOGINEER_PDF_PYTHON || 'python3';
  return new Promise<z.infer<typeof extractedSchema>>((accept, reject) => {
    const child = spawn(
      /* turbopackIgnore: true */ python,
      ['-B', resolve('interpretation/extract_pdf.py')],
      {
        stdio: ['pipe', 'pipe', 'ignore'],
        env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
      },
    );
    let output = Buffer.alloc(0);
    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      reject(
        new InterpretationError(
          'PDF_TIMEOUT',
          'PDF extraction exceeded its processing limit. Try a smaller or simpler PDF.',
        ),
      );
    }, 15000);
    child.on('error', () => {
      clearTimeout(timer);
      reject(new InterpretationError('PDF_NOT_CONFIGURED', errors.PDF_NOT_CONFIGURED, 503));
    });
    child.stdin.on('error', () => {});
    child.stdout.on('data', (chunk: Buffer) => {
      output = Buffer.concat([output, chunk]);
      if (output.length > 524288) {
        child.kill('SIGKILL');
        reject(new InterpretationError('PDF_TEXT_LIMIT', errors.PDF_TEXT_LIMIT));
      }
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      try {
        if (code !== 0) throw new Error('Worker stopped');
        const value = JSON.parse(output.toString('utf8'));
        if (value.error)
          throw new InterpretationError(
            value.error,
            errors[value.error] || errors.INVALID_PDF,
            value.error === 'PDF_NOT_CONFIGURED' ? 503 : 422,
          );
        accept(extractedSchema.parse(value));
      } catch (e) {
        reject(
          e instanceof InterpretationError
            ? e
            : new InterpretationError('INVALID_PDF', errors.INVALID_PDF),
        );
      }
    });
    child.stdin.end(data);
  });
}
