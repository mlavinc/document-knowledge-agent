import { AxiosInstance } from "axios";

import { SearchResponseBody } from "./types";

export async function askQuestion(
  httpClient: AxiosInstance,
  question: string
): Promise<SearchResponseBody> {
  const response = await httpClient.post<SearchResponseBody>("/api/search", {
    question,
  });

  return response.data;
}
