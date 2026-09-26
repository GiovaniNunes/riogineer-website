import { handleContactRequest } from '@/lib/contact';
export const runtime = 'nodejs';
export async function POST(request: Request) {
  return handleContactRequest(request);
}
