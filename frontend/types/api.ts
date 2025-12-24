export type DocumentMeta = {
  filename: string
  path?: string
  chunks: number
}

export type DocumentsResponse = Record<string, DocumentMeta>

export type QueryHit = {
  id: string
  score?: number | null
  doc_id?: string | null
  filename?: string | null
  chunk_index?: number | null
  text: string
  metadata?: Record<string, unknown> | null
}

export type QueryResponse = {
  answer: string
  sources: string[]
  hits: QueryHit[]
}

export type UploadResponse = {
  doc_id: string
  chunks: number
}

export type AssistantFile = {
  path: string
  action: 'create' | 'modify'
  language: string
  content: string
}

export type AssistantResponse = {
  summary: string
  assumptions: string[]
  files: AssistantFile[]
}


