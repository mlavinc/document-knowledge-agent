import { httpClient } from "./http";
import {
  SearchResponseBody,
  WarmupResponseBody,
} from "../types/rag.types";

export async function askQuestion(
  question: string
): Promise<SearchResponseBody> {
  const response = await httpClient.post<SearchResponseBody>("/api/search", {
    question,
  });

  return response.data;
}

export async function startAgentWarmup(): Promise<WarmupResponseBody> {
  const response = await httpClient.post<WarmupResponseBody>("/api/warmup");
  return response.data;
}

export async function getAgentWarmupStatus(): Promise<WarmupResponseBody> {
  const response = await httpClient.get<WarmupResponseBody>("/api/warmup");
  return response.data;
}
