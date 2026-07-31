import { ragCoreClient } from "../clients/rag-core.client";
import { SearchResponseBody } from "../types/search.types";
import { COLLECTION_DEFAULT } from "../utils/collection";

async function search(
  question: string,
  collection: string = COLLECTION_DEFAULT
): Promise<SearchResponseBody> {
  return ragCoreClient.search(question, collection);
}

export const ragService = {
  search,
};
