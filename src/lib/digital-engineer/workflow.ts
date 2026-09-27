import type { Flowsheet, Results } from './contracts';
export type WorkflowState = {
  draft: string;
  revision: number;
  validated: boolean;
  flowsheet: Flowsheet | null;
  results: Results | null;
  busy: boolean;
  error: string | null;
};
export type Action =
  | { type: 'invalidate' }
  | { type: 'approved'; draft: string }
  | { type: 'edit'; draft: string }
  | { type: 'layout' }
  | { type: 'start'; revision: number }
  | { type: 'validated'; revision: number }
  | { type: 'built'; revision: number; flowsheet: Flowsheet }
  | { type: 'calculated'; revision: number; results: Results }
  | { type: 'error'; revision: number; error: string };
export function initialWorkflow(draft: string): WorkflowState {
  return {
    draft,
    revision: 0,
    validated: false,
    flowsheet: null,
    results: null,
    busy: false,
    error: null,
  };
}
function canonical(text: string) {
  try {
    const sort = (v: unknown): unknown =>
      Array.isArray(v)
        ? v.map(sort)
        : v && typeof v === 'object'
          ? Object.fromEntries(
              Object.entries(v)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([k, v]) => [k, sort(v)]),
            )
          : v;
    return JSON.stringify(sort(JSON.parse(text)));
  } catch {
    return text;
  }
}
export function workflowReducer(state: WorkflowState, action: Action): WorkflowState {
  if (action.type === 'invalidate')
    return {
      ...state,
      revision: state.revision + 1,
      validated: false,
      flowsheet: null,
      busy: false,
      error: null,
    };
  if (action.type === 'approved')
    return {
      ...state,
      draft: action.draft,
      revision: state.revision + 1,
      validated: true,
      flowsheet: null,
      busy: false,
      error: null,
    };
  if (action.type === 'edit') {
    if (canonical(action.draft) === canonical(state.draft))
      return { ...state, draft: action.draft };
    return {
      ...state,
      draft: action.draft,
      revision: state.revision + 1,
      validated: false,
      flowsheet: null,
      busy: false,
      error: null,
    };
  }
  if (action.type === 'layout')
    return state.flowsheet
      ? {
          ...state,
          flowsheet: {
            ...state.flowsheet,
            presentation: {
              layout: state.flowsheet.presentation.layout === 'wide' ? 'compact' : 'wide',
            },
          },
        }
      : state;
  if (action.revision !== state.revision) return state;
  if (action.type === 'start') return { ...state, busy: true, error: null };
  if (action.type === 'validated') return { ...state, busy: false, validated: true };
  if (action.type === 'built') return { ...state, busy: false, flowsheet: action.flowsheet };
  if (action.type === 'calculated') {
    if (
      !state.flowsheet ||
      action.results.input_sha256 !== state.flowsheet.calculation.input_sha256
    )
      return {
        ...state,
        busy: false,
        validated: false,
        error:
          'The result belongs to a different engine version or input model. Validate and generate the PFD again before recalculating.',
      };
    return {
      ...state,
      busy: false,
      results: action.results,
      flowsheet: {
        ...state.flowsheet,
        calculation: { status: 'current', input_sha256: action.results.input_sha256 },
      },
    };
  }
  return {
    ...state,
    busy: false,
    error: action.error,
    validated: false,
    flowsheet: state.flowsheet
      ? { ...state.flowsheet, calculation: { ...state.flowsheet.calculation, status: 'failed' } }
      : null,
  };
}
export function resultsAreCurrent(state: WorkflowState) {
  return (
    !!state.results &&
    state.validated &&
    state.flowsheet?.calculation.status === 'current' &&
    state.flowsheet.calculation.input_sha256 === state.results.input_sha256
  );
}
