import type { MDXComponents } from 'mdx/types';
import { ContentRequired } from '@/components/content-required';
import { Workflow, DigitalEngineerWorkflow } from '@/components/workflow';
export function useMDXComponents(components: MDXComponents): MDXComponents {
  return { ContentRequired, Workflow, DigitalEngineerWorkflow, ...components };
}
