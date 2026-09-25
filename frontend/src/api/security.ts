const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

export type Permission = { id: number; code: string; name: string; description?: string; is_active: boolean }
export type Role = { id: number; code: string; name: string; description?: string; is_active: boolean; is_system_protected?: boolean; permissions: Permission[] }
export type Menu = { id: number; code: string; label: string; path: string; position: number; module_code: string; module_label: string; is_active: boolean; is_system_protected?: boolean; permissions: Permission[] }
export type User = { id: number; email: string; full_name: string; is_active: boolean; is_system_protected?: boolean; roles: Role[] }
export type Session = { user: User; permissions: string[]; menus: Menu[] }
export type Parameter = { id: number; key: string; name: string; module_code: string; value_type: string; value: string; default_value: string; min_value?: number; max_value?: number; description?: string; is_active: boolean }
export type LlmConfiguration = { id: number; name: string; provider_kind: string; base_url: string; model_id: string; reasoning_level: 'automatic' | 'minimal' | 'low' | 'medium' | 'high'; credential_configured: boolean; is_active: boolean; last_test_status?: string; last_test_message?: string }
export type DataConnection = { id: number; name: string; connector_kind: 'sqlserver'; host: string; port: number; database_name: string; username: string; encrypt: boolean; trust_server_certificate: boolean; is_active: boolean; last_test_status?: string; last_test_message?: string; last_tested_at?: string }
export type MetadataSnapshot = { id: number; data_connection_id: number; connector_code: string; database_name: string; contract_version: number; content_hash: string; schema_count: number; table_count: number; column_count: number; relationship_count: number; captured_by_label: string; captured_at: string }
export type ActiveSource = { status: 'ready' | 'missing'; connection?: { id: number; name: string; connector_kind: string; database_name: string; last_test_status?: string; last_tested_at?: string }; latest_snapshot?: MetadataSnapshot }
export type SnapshotCapture = { created: boolean; message: string; snapshot: MetadataSnapshot }
export type MetadataTable = { schema_name: string; table_name: string; column_count: number; relationship_count: number }
export type MetadataTableDetail = { schema_name: string; table_name: string; columns: Array<{ name: string; ordinal: number; data_type: string; max_length: number; precision: number; scale: number; nullable: boolean; primary_key: boolean }>; foreign_keys: Array<{ name: string; columns: string[]; referenced_schema: string; referenced_table: string; referenced_columns: string[] }>; incoming_relationships: Array<{ name: string; source_schema: string; source_table: string; source_columns: string[]; referenced_columns: string[] }> }
export type AuditEvent = { id: number; actor_user_id?: number; actor_label?: string; action: string; resource_type: string; resource_id?: string; created_at: string }
export type ReadinessComponent = { ready: boolean; label: string; detail: string; path?: string }
export type CopilotReadiness = { ready: boolean; source: ReadinessComponent; metadata: ReadinessComponent; llm: ReadinessComponent }
export type CapabilityOption = { code: string; label: string; description: string; available: boolean; reason: string; evidence: string[] }
export type DomainCapability = { code: string; label: string; description: string; available: boolean; reason: string; questions: CapabilityOption[]; periodicities: CapabilityOption[] }
export type CopilotCatalog = { metadata_snapshot_id: number; domains: DomainCapability[] }
export type BusinessNeedInput = { metadata_snapshot_id: number; business_goal: string; business_questions: string[]; periodicity: string; domain_code: 'ventas' }
export type NeedFormulation = { original_goal: string; suggested_goal: string; rationale: string; improvements: string[]; provider_kind: string; model_id: string }
export type NeedViabilityRequirement = { code: string; label: string; request_text: string; components?: string[]; status: 'direct' | 'derivable' | 'ambiguous' | 'unavailable'; evidence: string[]; formula?: string; resolution: string }
export type NeedViability = { assessment_hash: string; requirements: NeedViabilityRequirement[]; counts: Record<string, number>; requires_acknowledgement: string[]; can_continue: boolean; summary: string }
export type AnalysisCatalogQuestion = { code: string; label: string; description: string; prompt_instruction: string; enabled: boolean }
export type AnalysisCatalogPeriodicity = { code: 'day' | 'week' | 'month' | 'quarter' | 'year'; label: string; description: string; enabled: boolean }
export type AnalysisCatalogConfiguration = { version: 2; domain_code: string; questions: AnalysisCatalogQuestion[]; periodicities: AnalysisCatalogPeriodicity[] }
export type AnalysisCatalogDomain = { code: string; label: string; description: string; enabled: boolean; implementation_status: 'implemented' }
export type SemanticEvidenceCheck = { code: string; passed: boolean; label: string; detail: string }
export type SemanticCandidate = {
  business_concept: string
  business_name_es: string
  description_es: string
  technical_refs: string[]
  confidence: 'high' | 'medium' | 'low'
  reason: string
  references_validated: boolean
  selected?: boolean
  selection_source?: 'automatic' | 'analyst'
  evidence?: {
    status: 'confirmed' | 'structurally_supported' | 'review_required' | 'decision_required'
    recommended_action: 'include' | 'exclude' | 'review'
    guidance: string
    checks: SemanticEvidenceCheck[]
  }
}
export type ValidationIssue = { code: string; level: 'error' | 'warning'; path: string; message: string }
export type BiProposal = {
  id: number
  source_proposal_id?: number
  metadata_snapshot_id: number
  business_goal: string
  business_questions: string[]
  requested_dimensions: string[]
  periodicity: string
  domain_code: string
  scope_document: { origin?: string; tables?: Array<{ ref: string; columns?: Array<{ name: string; type: string; pk?: boolean; nullable?: boolean }> }> }
  semantic_map_document: { candidates?: SemanticCandidate[]; rejected_references?: Array<{ code: string; message: string }>; excluded_by_analyst?: string[]; excluded_by_system?: string[] }
  status: 'generating' | 'provider_failed' | 'validation_failed' | 'ready_for_review' | 'approved' | 'rejected' | 'invalidated' | 'discarded'
  input_hash: string
  prompt_version: string
  contract_version: number
  provider_kind: string
  model_id: string
  proposal_document: Record<string, unknown>
  validation_document: { valid: boolean; errors: number; warnings: number; issues: ValidationIssue[] }
  review_comment?: string
  warnings_confirmed: boolean
  created_by_label: string
  reviewed_by_label?: string
  created_at: string
  reviewed_at?: string
}
export type ProposalVerification = {
  proposal_id: number
  verified: boolean
  approval_safe: boolean
  compatibility_warning: boolean
  approval_invalidated: boolean
  checks: Array<{ code: string; label: string; passed: boolean; detail: string }>
  snapshot_hash: string
  proposal_hash: string
  replay_hash: string
  validated_reference_count: number
  rejected_reference_count: number
  validation_errors: number
  validation_warnings: number
  pending_validations: string[]
}
export type ControlledRelationOption = { option_id: string; left_table: string; right_table: string; left_columns: string[]; right_columns: string[]; left_types: string[]; right_types: string[]; cardinality: 'many_to_one' | 'one_to_many' | 'one_to_one' | 'unknown'; target_unique: boolean; nullable_source: boolean; duplication_risk: boolean; eligible: boolean; guidance: string }
export type ControlledRelationCatalog = { proposal_id: number; dimension_names: string[]; options: ControlledRelationOption[] }
export type SemanticPreview = {
  proposal_id: number
  all_passed: boolean
  message: string
  dimensions: Array<{
    dimension: string
    source_table: string
    label_column: string
    total_entities: number
    descriptive_entities: number
    fallback_entities: number
    coverage: number
    minimum_coverage: number
    passed: boolean
    samples: Array<{ business_key: string; display_label: string; entity_type: string }>
  }>
}
export type SemanticAdvice = {
  id: number
  proposal_id: number
  concept_code: string
  question: string
  response_document: {
    conclusion: 'include' | 'exclude' | 'define_business'
    answer_es: string
    evidence: Array<{ technical_ref: string; detail_es: string }>
    risk_es: string
    include_consequence_es: string
    exclude_consequence_es: string
    recommended_action_es: string
    confidence: 'high' | 'medium' | 'low'
    selection_changed: boolean
  }
  provider_kind: string
  model_id: string
  created_by_label: string
  created_at: string
}
export type Page<T> = { items: T[]; total: number; limit: number; offset: number }
export type ControlledMeasureCalculation = { operation: 'multiply' | 'add' | 'subtract' | 'divide'; inputs: string[] }
export type ProposalRevision = { summary: string; grain_description: string; dimension_names: string[]; measure_names: string[]; kpi_codes: string[]; kpi_measure_names: Record<string, string>; measure_aggregations: Record<string, 'sum' | 'count' | 'count_distinct' | 'average' | 'min' | 'max'>; measure_calculations: Record<string, ControlledMeasureCalculation>; comment: string }
export type EtlKpiRecipe = {
  code: string
  name: string
  description: string
  kind: 'aggregate' | 'ratio' | 'share'
  unit: string
  declared_unit?: string
  adjustments?: string[]
  periodicity: string
  definition_version: string
  inputs: string[]
  recipe: Record<string, unknown>
}
export type EtlTransformation = {
  order: number
  code: string
  stage: 'extract' | 'clean' | 'transform' | 'load' | 'validate'
  label: string
  detail: string
  severity: 'required' | 'optional'
  definition_version: string
}
export type EtlProposalCandidate = {
  proposal_id: number
  metadata_snapshot_id: number
  business_goal: string
  periodicity: string
  provider_kind: string
  model_id: string
  created_at: string
  reviewed_at?: string
  reviewed_by_label?: string
  review_comment?: string
  proposal_hash: string
  snapshot_hash: string
  summary: string
  grain: string
  fact_name: string
  dimensions: string[]
  measures: string[]
  kpi_count: number
  kpi_recipes: EtlKpiRecipe[]
  transformation_plan: EtlTransformation[]
  warnings: string[]
  eligible: boolean
  blocking_reasons: string[]
  recommended: boolean
  latest_execution_id?: number
  latest_execution_status?: EtlExecution['status']
  latest_execution_at?: string
  latest_execution_kpi_codes: string[]
}
export type EtlProposalCatalog = { items: EtlProposalCandidate[]; blocked_items: EtlProposalCandidate[]; recommended_proposal_id?: number; guidance: string[] }
export type EtlExecution = {
  id: number
  proposal_id: number
  metadata_snapshot_id: number
  status: 'prepared' | 'running' | 'succeeded' | 'validation_warning' | 'failed'
  domain_code: string
  builder_version: string
  proposal_hash: string
  snapshot_hash: string
  selection_document: Record<string, unknown>
  plan_document: Record<string, unknown>
  validation_document: Record<string, unknown>
  metrics_document: Record<string, unknown>
  created_by_label: string
  created_at: string
  started_at?: string
  finished_at?: string
}
export type AnalyticsOption = { value: string; label: string }
export type AnalyticsMetric = {
  code: string
  name: string
  value?: number
  unit: string
  status: 'reconciled' | 'not_calculable'
}
export type AnalyticsPoint = { key: string; label: string; value: number; share?: number }
export type AnalyticsVisual = {
  code: string
  title: string
  subtitle: string
  kind: 'line' | 'bar' | 'donut'
  dimension: string
  points: AnalyticsPoint[]
}
export type AnalyticsInsight = {
  code: string
  title: string
  statement: string
  evidence: string
  tone: 'positive' | 'neutral' | 'attention'
}
export type AnalyticsDashboard = {
  execution_id: number
  proposal_id: number
  title: string
  description: string
  grain: string
  refreshed_at: string
  currency_code: string
  currency_status: string
  reconciliation_passed: boolean
  period_label: string
  metric_code: string
  available_metrics: AnalyticsOption[]
  filters: {
    years: AnalyticsOption[]
    territories: AnalyticsOption[]
    selected_year?: number
    selected_territory?: string
  }
  kpis: AnalyticsMetric[]
  visuals: AnalyticsVisual[]
  insights: AnalyticsInsight[]
  quality: {
    source_rows: number
    datamart_rows: number
    difference_rows: number
    reconciliation_passed: boolean
    tables_loaded: number
  }
  guidance: string[]
}
export type AnalyticsChatTurn = { role: 'user' | 'assistant'; content: string }
export type AnalyticsCopilotAnswer = {
  answer: string
  evidence: string[]
  suggested_questions: string[]
  caveat: string
  provider_kind: string
  model_id: string
}

type ApiValidationIssue = { loc?: (string | number)[]; msg?: string }
type ErrorBody = { detail?: string | ApiValidationIssue[] }

function readableError(detail: ErrorBody['detail']) {
  if (typeof detail === 'string') return detail
  if (!Array.isArray(detail)) return 'No fue posible completar la solicitud.'

  const labels: Record<string, string> = {
    email: 'Correo',
    full_name: 'Nombre completo',
    password: 'Contraseña',
    name: 'Nombre',
    provider_kind: 'Proveedor',
    host: 'Servidor',
    database_name: 'Base de datos',
    username: 'Usuario',
  }
  return detail.map((issue) => {
    const field = String(issue.loc?.at(-1) ?? '')
    if (field === 'email') return 'Correo: escriba una dirección válida, por ejemplo operador@empresa.com.'
    if (field === 'password') return 'Contraseña: debe contener al menos 12 caracteres.'
    return `${labels[field] ?? 'Dato'}: ${issue.msg ?? 'revise el valor ingresado.'}`
  }).join(' ')
}

async function request<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init?.headers },
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorBody
    throw new Error(readableError(body.detail))
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

async function requestFile(path: string, token: string) {
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorBody
    throw new Error(readableError(body.detail))
  }
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const filename = disposition.match(/filename="([^"]+)"/)?.[1] ?? 'reporte-analitico'
  return { blob: await response.blob(), filename }
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string }>('/auth/login', undefined, { method: 'POST', body: JSON.stringify({ email, password }) }),
  session: (token: string) => request<Session>('/auth/me', token),
  users: (token: string, limit: number, offset: number) => request<Page<User>>(`/users?limit=${limit}&offset=${offset}`, token),
  roles: (token: string, limit: number, offset: number) => request<Page<Role>>(`/roles?limit=${limit}&offset=${offset}`, token),
  permissions: (token: string, limit: number, offset: number) => request<Page<Permission>>(`/permissions?limit=${limit}&offset=${offset}`, token),
  menus: (token: string, limit: number, offset: number) => request<Page<Menu>>(`/menus?limit=${limit}&offset=${offset}`, token),
  parameters: (token: string, limit: number, offset: number) => request<Page<Parameter>>(`/parameters?limit=${limit}&offset=${offset}`, token),
  llm: (token: string, limit: number, offset: number) => request<Page<LlmConfiguration>>(`/llm-configurations?limit=${limit}&offset=${offset}`, token),
  connections: (token: string, limit: number, offset: number) => request<Page<DataConnection>>(`/connections?limit=${limit}&offset=${offset}`, token),
  activeSource: (token: string) => request<ActiveSource>('/sources/active', token),
  metadataSnapshots: (token: string, limit: number, offset: number) => request<Page<MetadataSnapshot>>(`/metadata/snapshots?limit=${limit}&offset=${offset}`, token),
  captureMetadata: (token: string) => request<SnapshotCapture>('/metadata/snapshots', token, { method: 'POST' }),
  metadataTables: (token: string, snapshotId: number, search = '', schemaName = '', limit = 10, offset = 0) => request<Page<MetadataTable>>(`/metadata/snapshots/${snapshotId}/tables?search=${encodeURIComponent(search)}&schema_name=${encodeURIComponent(schemaName)}&limit=${limit}&offset=${offset}`, token),
  metadataTable: (token: string, snapshotId: number, schemaName: string, tableName: string) => request<MetadataTableDetail>(`/metadata/snapshots/${snapshotId}/tables/${encodeURIComponent(schemaName)}/${encodeURIComponent(tableName)}`, token),
  copilotReadiness: (token: string) => request<CopilotReadiness>('/copilot/readiness', token),
  copilotCatalog: (token: string, snapshotId: number) => request<CopilotCatalog>(`/copilot/catalog?metadata_snapshot_id=${snapshotId}`, token),
  formulateNeed: (token: string, body: BusinessNeedInput) => request<NeedFormulation>('/copilot/needs/formulate', token, { method: 'POST', body: JSON.stringify(body) }),
  validateNeed: (token: string, body: BusinessNeedInput) => request<NeedViability>('/copilot/needs/viability', token, { method: 'POST', body: JSON.stringify(body) }),
  analysisCatalogDomains: (token: string) => request<AnalysisCatalogDomain[]>('/analysis-catalog/domains', token),
  analysisCatalog: (token: string, domainCode: string) => request<AnalysisCatalogConfiguration>(`/analysis-catalog/domains/${encodeURIComponent(domainCode)}`, token),
  saveAnalysisCatalog: (token: string, domainCode: string, body: AnalysisCatalogConfiguration) => request<AnalysisCatalogConfiguration>(`/analysis-catalog/domains/${encodeURIComponent(domainCode)}`, token, { method: 'PUT', body: JSON.stringify(body) }),
  resetAnalysisCatalog: (token: string, domainCode: string) => request<AnalysisCatalogConfiguration>(`/analysis-catalog/domains/${encodeURIComponent(domainCode)}/reset`, token, { method: 'POST' }),
  proposals: (token: string, limit = 10, offset = 0, statuses: string[] = [], domainCode?: string) => {
    const query = new URLSearchParams({ limit: String(limit), offset: String(offset) })
    statuses.forEach((status) => query.append('status', status))
    if (domainCode) query.set('domain_code', domainCode)
    return request<Page<BiProposal>>(`/copilot/proposals?${query.toString()}`, token)
  },
  createProposal: (token: string, body: object) => request<BiProposal>('/copilot/proposals', token, { method: 'POST', body: JSON.stringify(body) }),
  reviseProposal: (token: string, id: number, body: ProposalRevision) => request<BiProposal>(`/copilot/proposals/${id}/revisions`, token, { method: 'POST', body: JSON.stringify(body) }),
  relationOptions: (token: string, id: number) => request<ControlledRelationCatalog>(`/copilot/proposals/${id}/relation-options`, token),
  reviseRelation: (token: string, id: number, body: { dimension_name: string; option_id: string; comment: string }) => request<BiProposal>(`/copilot/proposals/${id}/relation-revisions`, token, { method: 'POST', body: JSON.stringify(body) }),
  approveProposal: (token: string, id: number, body: { comment?: string; warnings_confirmed: boolean }) => request<BiProposal>(`/copilot/proposals/${id}/approve`, token, { method: 'POST', body: JSON.stringify(body) }),
  rejectProposal: (token: string, id: number, comment: string) => request<BiProposal>(`/copilot/proposals/${id}/reject`, token, { method: 'POST', body: JSON.stringify({ comment }) }),
  invalidateProposal: (token: string, id: number, comment: string) => request<BiProposal>(`/copilot/proposals/${id}/invalidate`, token, { method: 'POST', body: JSON.stringify({ comment }) }),
  restoreProposalApproval: (token: string, id: number, body: { comment?: string; warnings_confirmed: boolean }) => request<BiProposal>(`/copilot/proposals/${id}/restore-approval`, token, { method: 'POST', body: JSON.stringify(body) }),
  discardProposal: (token: string, id: number, comment: string) => request<BiProposal>(`/copilot/proposals/${id}/discard`, token, { method: 'POST', body: JSON.stringify({ comment }) }),
  verifyProposal: (token: string, id: number) => request<ProposalVerification>(`/copilot/proposals/${id}/verify`, token, { method: 'POST' }),
  semanticPreview: (token: string, id: number) => request<SemanticPreview>(`/copilot/proposals/${id}/semantic-preview`, token),
  semanticAdvice: (token: string, id: number, conceptCode: string) => request<SemanticAdvice[]>(`/copilot/proposals/${id}/semantic-advice?concept_code=${encodeURIComponent(conceptCode)}`, token),
  askSemanticAdvice: (token: string, id: number, body: { concept_code: string; question: string }) => request<SemanticAdvice>(`/copilot/proposals/${id}/semantic-advice`, token, { method: 'POST', body: JSON.stringify(body) }),
  etlProposals: (token: string) => request<EtlProposalCatalog>('/etl/proposals', token),
  prepareEtlExecution: (token: string, body: { proposal_id: number; selected_kpi_codes: string[]; confirmation: boolean; analyst_comment: string }) => request<EtlExecution>('/etl/executions', token, { method: 'POST', body: JSON.stringify(body) }),
  runEtlExecution: (token: string, id: number) => request<EtlExecution>(`/etl/executions/${id}/run`, token, { method: 'POST' }),
  etlExecution: (token: string, id: number) => request<EtlExecution>(`/etl/executions/${id}`, token),
  verifyEtlCurrency: (token: string, id: number) => request<EtlExecution>(`/etl/executions/${id}/verify-currency`, token, { method: 'POST' }),
  retryEtlSpanishInterpretation: (token: string, id: number) => request<EtlExecution>(`/etl/executions/${id}/interpret-spanish`, token, { method: 'POST' }),
  applyEtlSpanishInterpretation: (token: string, id: number, body: { confirmation: boolean; analyst_comment: string; groups: Array<{ dimension: string; target_column: string; mappings: Array<{ original: string; label_es: string }> }> }) => request<EtlExecution>(`/etl/executions/${id}/interpret-spanish/apply`, token, { method: 'POST', body: JSON.stringify(body) }),
  etlExecutions: (token: string, limit = 10, offset = 0) => request<Page<EtlExecution>>(`/etl/executions?limit=${limit}&offset=${offset}`, token),
  analyticsDashboard: (token: string, filters: { metricCode?: string; year?: string; territory?: string } = {}) => {
    const query = new URLSearchParams()
    if (filters.metricCode) query.set('metric_code', filters.metricCode)
    if (filters.year) query.set('year', filters.year)
    if (filters.territory) query.set('territory', filters.territory)
    const suffix = query.size ? `?${query.toString()}` : ''
    return request<AnalyticsDashboard>(`/analytics/dashboard${suffix}`, token)
  },
  analyticsReport: (token: string, format: 'pdf' | 'xlsx', filters: { metricCode?: string; year?: string; territory?: string; view: 'executive' | 'analyst' }) => {
    const query = new URLSearchParams({ view: filters.view })
    if (filters.metricCode) query.set('metric_code', filters.metricCode)
    if (filters.year) query.set('year', filters.year)
    if (filters.territory) query.set('territory', filters.territory)
    return requestFile(`/analytics/reports/${format}?${query.toString()}`, token)
  },
  askAnalyticsCopilot: (token: string, body: { question: string; history: AnalyticsChatTurn[]; view: 'executive' | 'analyst'; execution_id: number; metric_code: string; year?: number; territory?: string }) => request<AnalyticsCopilotAnswer>('/analytics/copilot', token, { method: 'POST', body: JSON.stringify(body) }),
  audit: (token: string, limit: number, offset: number) => request<Page<AuditEvent>>(`/audit-events?limit=${limit}&offset=${offset}`, token),
  testLlm: (token: string, id: number) => request<{ ok: boolean; message: string }>(`/llm-configurations/${id}/test`, token, { method: 'POST' }),
  saveLlmCredential: (token: string, id: number, apiKey: string) => request<{ credential_configured: boolean; message: string }>(`/llm-configurations/${id}/secret`, token, { method: 'PUT', body: JSON.stringify({ api_key: apiKey }) }),
  testConnection: (token: string, id: number) => request<{ ok: boolean; message: string }>(`/connections/${id}/test`, token, { method: 'POST' }),
  activateConnection: (token: string, id: number) => request<DataConnection>(`/connections/${id}/activate`, token, { method: 'POST' }),
  deactivateConnection: (token: string, id: number) => request<DataConnection>(`/connections/${id}/deactivate`, token, { method: 'POST' }),
  resetParameter: (token: string, key: string) => request<Parameter>(`/parameters/${key}/reset`, token, { method: 'POST' }),
  create: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'POST', body: JSON.stringify(body) }),
  update: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'PATCH', body: JSON.stringify(body) }),
  upsert: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'PUT', body: JSON.stringify(body) }),
  remove: (path: string, token: string) => request<void>(path, token, { method: 'DELETE' }),
}
