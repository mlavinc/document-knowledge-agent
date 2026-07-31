import { SearchResponseBody } from "../types/chat.types";
import { httpClient } from "./http";

export async function askQuestion(
  question: string
): Promise<SearchResponseBody> {
  const response = await httpClient.post<SearchResponseBody>("/api/search", {
    question,
  });

  return response.data;
}
