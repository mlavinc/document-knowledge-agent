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

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: SearchSource[];
  createdAt: string;
}
