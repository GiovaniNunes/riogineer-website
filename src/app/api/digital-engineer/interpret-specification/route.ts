import { handleInterpretRequest } from '@/lib/digital-engineer/interpretation/service';
export const runtime = 'nodejs';
export async function POST(request: Request) {
  return handleInterpretRequest(request);
}
