export interface SearchSource {
  document_id: string;
  title: string;
  chunk_index: number;
  score: number;
}

export interface SearchResponseBody {
  answer: string;
  sources: SearchSource[];
}

export interface DocumentIngestResponseBody {
  filename: string;
  chunks?: number;
  status: string;
  document_id?: string;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: SearchSource[];
  createdAt: string;
}

export interface IngestedDocument {
  filename: string;
  chunks?: number;
  status: string;
  ingestedAt: string;
}
