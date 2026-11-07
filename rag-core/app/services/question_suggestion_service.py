import re
from pathlib import Path


GENERIC_NAMES = {"sample", "document", "paper", "upload"}
BOILERPLATE_PREFIXES = (
    "doi",
    "published",
    "received",
    "revised",
    "accepted",
    "copyright",
    "citation",
    "open access",
)


def _clean(value: str) -> str:
    return " ".join((value or "").replace("\x00", "").split()).strip()


def _shorten(value: str, limit: int = 88) -> str:
    cleaned = _clean(value).rstrip(".?!")
    if len(cleaned) <= limit:
        return cleaned
    clipped = cleaned[:limit].rsplit(" ", 1)[0]
    return clipped or cleaned[:limit]


def _document_subject(document_id: str, metadata: dict | None = None) -> str:
    title = _clean(str((metadata or {}).get("title", "")))
    if title:
        return _shorten(title, 110)

    filename = _clean(re.sub(r"[_-]+", " ", Path(document_id).stem))
    if filename and filename.lower() not in GENERIC_NAMES:
        return _shorten(filename)
    return "this document"


def _heading_candidates(pages: list[dict], subject: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    subject_lower = subject.lower()
    body_started = False

    for page in pages[:8]:
        lines = str(page.get("text", "")).splitlines()
        for index, raw_line in enumerate(lines):
            line = _clean(raw_line)
            if not 8 <= len(line) <= 100:
                continue

            lower = line.lower().rstrip(":")
            if lower == subject_lower or lower.startswith(BOILERPLATE_PREFIXES):
                continue

            numbered = re.match(
                r"^(?:\d+(?:\.\d+)*[.)]?|[ivx]+[.)])\s+(.+)$",
                line,
                re.I,
            )
            if numbered:
                line = _clean(numbered.group(1))
                body_started = True
                if index + 1 < len(lines):
                    continuation = _clean(lines[index + 1])
                    if (
                        continuation
                        and len(continuation) <= 40
                        and continuation[0].islower()
                        and not continuation.endswith((".", "?", "!"))
                    ):
                        line = f"{line} {continuation}"
            elif not body_started or not (
                line.isupper()
                or line.istitle()
                or lower
                in {
                    "abstract",
                    "introduction",
                    "discussion",
                    "conclusion",
                    "conclusions",
                }
            ):
                continue

            line = _shorten(line, 72)
            key = line.lower()
            if line and key not in seen:
                seen.add(key)
                candidates.append(line)
            if len(candidates) == 4:
                return candidates

    return candidates


def _fallback_questions(document_id: str) -> list[str]:
    subject = _document_subject(document_id)
    if subject == "this document":
        return [
            "What is this document mainly about?",
            "What are the document's key ideas?",
            "What conclusions does the document present?",
        ]
    return [
        f"What is {subject} about?",
        f"What are the key ideas in {subject}?",
        f"What conclusions does {subject} present?",
    ]


class QuestionSuggestionService:
    """Build document-aware starter questions without an extra model call."""

    def generate(
        self,
        document_id: str,
        pages: list[dict],
        metadata: dict | None = None,
    ) -> list[str]:
        subject = _document_subject(document_id, metadata)
        headings = _heading_candidates(pages, subject)

        questions = [f"What are the main findings of {subject}?"]
        if headings:
            questions.append(f"How does the document explain {headings[0]}?")
        else:
            questions.append(f"What evidence does {subject} present?")

        if len(headings) > 1:
            questions.append(
                f"What does the document conclude about {headings[1]}?"
            )
        else:
            questions.append(
                f"What conclusions or implications does {subject} present?"
            )

        return [_shorten(question, 139) + "?" for question in questions]


question_suggestion_service = QuestionSuggestionService()
