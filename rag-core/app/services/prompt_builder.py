class PromptBuilder:
    """
    Builds prompts for the LLM using retrieved context.
    """

    def build(self, question: str, context: list[dict]) -> str:
        context_parts = []

        for i, chunk in enumerate(context):
            metadata = chunk.get("metadata", {})

            title = metadata.get(
                "title",
                "Unknown document",
            )

            source = metadata.get(
                "source",
                "Unknown source",
            )

            chunk_index = metadata.get(
                "chunk_index",
                i,
            )

            context_parts.append(
                f"""Document:
{title}

Source:
{source}

Chunk:
{chunk_index}

Content:
{chunk['document']}
"""
            )

        context_text = "\n\n---\n\n".join(context_parts)

        return f"""You are a helpful assistant that answers using ONLY the provided context.

Rules:
- Do not use external knowledge.
- The document title and metadata identify the source, but answers must be based on the content sections.
- Treat accented and unaccented name variants as the same person when the context clearly refers to them (for example, "Martín Lavín" and "Martin Lavin", or "Martín Lavín Carvajal" and "Martin Lavin Carvajal").
- If the context does not contain enough information, clearly say so.
- Prefer information supported by multiple context sections when available.
- Do not invent details.

Context:

{context_text}

Question:
{question}

Answer:
"""


prompt_builder = PromptBuilder()