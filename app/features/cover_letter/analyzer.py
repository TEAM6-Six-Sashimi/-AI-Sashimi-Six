import re

from app.features.cover_letter.schemas import CoverLetterQuestionReview


def calculate_average_sentence_length(
        contents: list[str],
) -> int:
    sentences: list[str] = []

    for content in contents:
        sentences.extend(
            sentence.strip()
            for sentence in re.split(r"[.!?。！？\n]+", content)
            if sentence.strip()
        )

    if not sentences:
        return 0

    total_length = sum(
        len(sentence.replace(" ", ""))
        for sentence in sentences
    )

    return round(total_length / len(sentences))


def calculate_repeated_expression_count(
        questions: list[CoverLetterQuestionReview],
) -> int:
    expressions = {
        repeated.expression.strip()
        for question in questions
        for repeated in question.repeated_expressions
        if repeated.expression.strip()
    }

    return len(expressions)