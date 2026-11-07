from app.services.question_suggestion_service import (
    _fallback_questions,
    question_suggestion_service,
)


def test_suggestions_use_pdf_title_and_headings():
    result = question_suggestion_service.generate(
        "sample.pdf",
        [
            {
                "text": (
                    "EDITED BY\nAndrea Fusco,\nUniversity of Example\n"
                    "1 Introduction\nBody text"
                )
            },
            {"text": "2 Methods\n4 Physical health benefits\nBody text"},
        ],
        {"title": "Benefits of Outdoor Hiking"},
    )

    assert result == [
        "What are the main findings of Benefits of Outdoor Hiking?",
        "How does the document explain Introduction?",
        "What does the document conclude about Methods?",
    ]


def test_fallback_uses_meaningful_filename():
    questions = _fallback_questions("Attention_Is_All_You_Need.pdf")

    assert len(questions) == 3
    assert all("Attention Is All You Need" in item for item in questions)


def test_fallback_avoids_sample_as_a_subject():
    questions = _fallback_questions("sample.pdf")

    assert questions[0] == "What is this document mainly about?"
