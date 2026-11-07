import fitz


class PDFParserService:
    """
    Extracts text content from PDF documents
    while preserving page information.
    """

    def extract_text(self, file_path: str) -> dict:

        document = fitz.open(file_path)
        metadata = dict(document.metadata or {})

        pages = []

        for index, page in enumerate(document):

            # PostgreSQL rejects NUL (0x00) in UTF-8 text columns.
            text = page.get_text().replace("\x00", "")
            pages.append(
                {
                    "page_number": index + 1,
                    "text": text,
                }
            )

        document.close()

        return {
            "pages": pages,
            "page_count": len(pages),
            "metadata": metadata,
        }


pdf_parser_service = PDFParserService()
