import { afterAll, describe, expect, it, vi } from 'vitest';
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { extractPdf, MAX_PDF_BYTES } from '../src/lib/digital-engineer/interpretation/pdf';
import { handleInterpretRequest } from '../src/lib/digital-engineer/interpretation/service';
const python =
  process.env.RIOGINEER_PDF_PYTHON ||
  process.env.ENGINE_PYTHON ||
  (existsSync('engine/.venv/bin/python') ? resolve('engine/.venv/bin/python') : 'python3');
vi.stubEnv('RIOGINEER_PDF_PYTHON', python);
afterAll(() => vi.unstubAllEnvs());
// Minimal generated fixture using pypdf itself, never a user document or retained upload.
function pdf(text = '', encrypted = false, count = 1) {
  return execFileSync(python, [
    '-B',
    '-c',
    `import sys,io; from pypdf import PdfWriter; from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject\nw=PdfWriter()\nfor _ in range(${count}):\n p=w.add_blank_page(width=600,height=800)\n font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})\n p[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):w._add_object(font)})})\n s=DecodedStreamObject(); s.set_data(${JSON.stringify('BT /F1 12 Tf 50 700 Td (' + text + ') Tj ET')}.encode()); p[NameObject('/Contents')]=w._add_object(s)\n${encrypted ? "w.encrypt('secret')" : ''}\nb=io.BytesIO(); w.write(b); sys.stdout.buffer.write(b.getvalue())`,
  ]);
}
const file = (bytes: Buffer, name = 'spec.pdf', type = 'application/pdf') =>
  new File([new Uint8Array(bytes)], name, { type });
describe('bounded text-only PDF extraction', () => {
  it('extracts machine-readable text with page provenance', async () => {
    const result = await extractPdf(file(pdf('Separator pressure = 20 bar abs')));
    expect(result.pages).toHaveLength(1);
    expect(result.pages[0].page).toBe(1);
    expect(result.pages[0].text).toContain('20 bar abs');
  });
  it('rejects files without usable text instead of inferring content', async () => {
    await expect(extractPdf(file(pdf()))).rejects.toThrow('no usable machine-readable text');
  });
  it('rejects non-PDF, malformed, encrypted and excessive page-count PDFs', async () => {
    await expect(extractPdf(file(Buffer.from('text'), 'spec.txt', 'text/plain'))).rejects.toThrow(
      'Only PDF',
    );
    await expect(extractPdf(file(Buffer.from('pretend pdf')))).rejects.toThrow('could not be read');
    await expect(extractPdf(file(Buffer.from('%PDF-invalid')))).rejects.toThrow(
      'could not be read',
    );
    await expect(extractPdf(file(pdf('content', true)))).rejects.toThrow('Encrypted');
    await expect(extractPdf(file(pdf('content', false, 41)))).rejects.toThrow('1–40 pages');
  });
  it('rejects oversized uploads before extraction/provider calls', async () => {
    const upload = file(Buffer.alloc(MAX_PDF_BYTES + 1));
    await expect(extractPdf(upload)).rejects.toThrow('5 MiB');
    const form = new FormData();
    form.set('document', upload);
    const response = await handleInterpretRequest(
      new Request('http://localhost/api/digital-engineer/interpret-specification', {
        method: 'POST',
        headers: { Origin: 'http://localhost' },
        body: form,
      }),
    );
    expect(response.status).toBe(413);
  });
  it('combines PDF and instructions without merging their source identities', async () => {
    const form = new FormData();
    form.set('document', file(pdf('Separator pressure = 20 bar abs')));
    form.set('instructions', 'Use separator pressure = 15 bar abs');
    const ids: string[] = [];
    const response = await handleInterpretRequest(
      new Request('http://localhost/api/digital-engineer/interpret-specification', {
        method: 'POST',
        headers: { Origin: 'http://localhost' },
        body: form,
      }),
      {
        name: 'test-only',
        interpret_specification: async (source) => {
          ids.push(source.id);
          return { facts: [], issues: [] };
        },
      },
    );
    expect(response.status).toBe(200);
    expect(ids).toEqual(['document', 'instructions']);
    expect((await response.json()).draft.sources.map((s: { type: string }) => s.type)).toEqual([
      'uploaded_document',
      'user_text',
    ]);
  });
});
