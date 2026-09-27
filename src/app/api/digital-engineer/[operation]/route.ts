import { handleEngineeringRequest } from '@/lib/digital-engineer/api';
export const runtime = 'nodejs';
export async function POST(request: Request, context: { params: Promise<{ operation: string }> }) {
  return handleEngineeringRequest(request, (await context.params).operation);
}
