export interface AssistantFile {
  path: string;
  action: 'create' | 'modify';
  language: string;
  content: string;
}

export interface AssistantResponse {
  summary: string;
  assumptions: string[];
  files: AssistantFile[];
}

export interface AssistantRequest {
  instruction: string;
}
