import { z } from 'zod';
import { contactLimits, interests } from '@/config/contact';
const singleLine = (max: number) =>
  z
    .string()
    .trim()
    .min(1, 'This field is required.')
    .max(max, `Use no more than ${max} characters.`)
    .refine((value) => !/[\r\n\u0000]/.test(value), 'Use a single line of text.');
export const contactSchema = z.strictObject({
  name: singleLine(contactLimits.name),
  company: singleLine(contactLimits.company),
  email: z.string().trim().max(contactLimits.email).pipe(z.email('Enter a valid email address.')),
  country: singleLine(contactLimits.country),
  interest: z.enum(interests, { error: 'Select an area of interest.' }),
  message: z
    .string()
    .trim()
    .min(10, 'Enter at least 10 characters.')
    .max(contactLimits.message, `Use no more than ${contactLimits.message} characters.`)
    .refine((value) => !value.includes('\u0000'), 'Remove invalid characters.'),
  website: z.string().max(200).optional().default(''),
});
export type ContactSubmission = z.infer<typeof contactSchema>;
export type ContactFieldErrors = Partial<Record<keyof ContactSubmission, string[]>>;
