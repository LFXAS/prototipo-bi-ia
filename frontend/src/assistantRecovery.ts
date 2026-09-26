export const assistantDraftKey = 'bi_ia_assistant_draft_v1'

export type AssistantDraft = {
  version: 1
  domainCode: string
  step: number
  goal: string
  questions: string[]
  periodicity: string
  proposalId?: number
}

export function readAssistantDraft(): AssistantDraft | null {
  try {
    const parsed = JSON.parse(localStorage.getItem(assistantDraftKey) ?? 'null') as Partial<AssistantDraft> | null
    if (!parsed || parsed.version !== 1 || typeof parsed.domainCode !== 'string') return null
    return {
      version: 1,
      domainCode: parsed.domainCode,
      step: Math.max(1, Math.min(Number(parsed.step) || 1, 5)),
      goal: typeof parsed.goal === 'string' ? parsed.goal.slice(0, 2000) : '',
      questions: Array.isArray(parsed.questions) ? parsed.questions.filter((item): item is string => typeof item === 'string') : [],
      periodicity: typeof parsed.periodicity === 'string' ? parsed.periodicity : 'month',
      proposalId: Number.isInteger(parsed.proposalId) && Number(parsed.proposalId) > 0 ? Number(parsed.proposalId) : undefined,
    }
  } catch {
    return null
  }
}
