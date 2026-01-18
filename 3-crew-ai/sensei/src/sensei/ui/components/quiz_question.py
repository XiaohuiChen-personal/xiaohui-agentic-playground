"""Quiz question component for Sensei.

This module provides UI components for quiz display including:
- Question text display
- Multiple choice options
- True/False questions
- Answer submission
- Feedback display
- Results summary
"""

from typing import Any, Callable

import streamlit as st

from sensei.models.enums import QuestionType
from sensei.models.schemas import QuizQuestion, AnswerResult, QuizResult


def render_question(
    question: QuizQuestion | dict[str, Any],
    question_idx: int,
    total_questions: int,
    on_answer: Callable[[str, str], None] | None = None,
    show_feedback: bool = False,
    answer_result: AnswerResult | None = None,
    selected_answer: str | None = None,
) -> str | None:
    """Render a quiz question with answer options.
    
    Args:
        question: QuizQuestion object or dict with question data.
        question_idx: Current question index (0-based).
        total_questions: Total number of questions.
        on_answer: Callback when answer is submitted. Receives (question_id, answer).
        show_feedback: Whether to show feedback after answering.
        answer_result: The result of the answer if feedback is shown.
        selected_answer: Previously selected answer (if any).
    
    Returns:
        The selected answer if submitted, None otherwise.
    
    Example:
        ```python
        render_question(
            question=QuizQuestion(
                id="q1",
                question="What is 2+2?",
                options=["3", "4", "5"],
                correct_answer="4",
            ),
            question_idx=0,
            total_questions=5,
            on_answer=lambda qid, ans: handle_answer(qid, ans),
        )
        ```
    """
    # Handle both QuizQuestion objects and dicts
    if isinstance(question, QuizQuestion):
        q_id = question.id
        q_text = question.question
        q_options = question.options
        q_type = question.question_type
        q_explanation = question.explanation
    else:
        q_id = question.get("id", f"q_{question_idx}")
        q_text = question.get("question", "")
        q_options = question.get("options", [])
        q_type_str = question.get("question_type", "multiple_choice")
        q_type = QuestionType(q_type_str) if isinstance(q_type_str, str) else q_type_str
        q_explanation = question.get("explanation", "")
    
    # Progress indicator
    _render_progress(question_idx, total_questions)
    
    st.markdown("---")
    
    # Question text
    st.markdown(f"### Q{question_idx + 1}: {q_text}")
    
    # Answer options based on question type
    if q_type == QuestionType.TRUE_FALSE:
        answer = _render_true_false(q_id, selected_answer, show_feedback, answer_result)
    elif q_type == QuestionType.MULTIPLE_CHOICE:
        answer = _render_multiple_choice(q_id, q_options, selected_answer, show_feedback, answer_result)
    else:
        # Default to multiple choice
        answer = _render_multiple_choice(q_id, q_options, selected_answer, show_feedback, answer_result)
    
    # Feedback section
    if show_feedback and answer_result:
        _render_feedback(answer_result, q_explanation)
    
    # Submit button (only if not showing feedback)
    if not show_feedback:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "Submit Answer",
                key=f"submit_{q_id}",
                use_container_width=True,
                type="primary",
                disabled=answer is None,
            ):
                if answer and on_answer:
                    on_answer(q_id, answer)
                return answer
    
    return None


def render_quiz_progress(
    current_question: int,
    total_questions: int,
    correct_count: int | None = None,
) -> None:
    """Render quiz progress bar and stats.
    
    Args:
        current_question: Current question index (0-based).
        total_questions: Total number of questions.
        correct_count: Number of correct answers so far (optional).
    """
    # Progress bar
    progress = (current_question) / total_questions if total_questions > 0 else 0
    st.progress(progress)
    
    # Stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Question {current_question + 1} of {total_questions}**")
    
    with col2:
        if correct_count is not None:
            st.markdown(f"✓ {correct_count} correct")


def render_quiz_results(
    result: QuizResult | dict[str, Any],
    pass_threshold: float = 0.8,
    on_continue: Callable[[], None] | None = None,
    on_review: Callable[[], None] | None = None,
    on_retake: Callable[[], None] | None = None,
) -> None:
    """Render quiz results summary.
    
    Args:
        result: QuizResult object or dict with score and feedback.
        pass_threshold: Minimum score to pass (0-1).
        on_continue: Callback when Continue button is clicked.
        on_review: Callback when Review button is clicked.
        on_retake: Callback when Retake button is clicked.
    """
    # Handle both QuizResult objects and dicts
    if isinstance(result, QuizResult):
        score = result.score
        correct = result.correct_count
        total = result.total_questions
        weak_concepts = result.weak_concepts
        feedback = result.feedback
    else:
        score = result.get("score", 0)
        correct = result.get("correct_count", 0)
        total = result.get("total_questions", 0)
        weak_concepts = result.get("weak_concepts", [])
        feedback = result.get("feedback", "")
    
    passed = score >= pass_threshold
    
    # Results card
    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 2rem;
            background: {'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)' if passed else 'linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)'};
            border-radius: 15px;
            margin: 2rem 0;
        ">
            <span style="font-size: 4rem;">{'🎉' if passed else '📚'}</span>
            <h1 style="margin: 1rem 0;">Quiz Complete!</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Score display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Score", f"{score * 100:.0f}%")
    
    with col2:
        st.metric("Correct", f"{correct}/{total}")
    
    with col3:
        if passed:
            st.success("✅ PASSED!")
        else:
            st.error("❌ Needs Review")
    
    # Pass/Fail message
    if passed:
        st.success(f"Great job! You scored {score * 100:.0f}% and can proceed to the next module.")
    else:
        st.warning(f"You scored {score * 100:.0f}%. A score of {pass_threshold * 100:.0f}% is needed to pass. Consider reviewing the weak areas below.")
    
    # Feedback
    if feedback:
        st.markdown("### 📝 Feedback")
        st.markdown(feedback)
    
    # Weak concepts
    if weak_concepts:
        st.markdown("### 📌 Areas to Review")
        for concept in weak_concepts:
            st.markdown(f"- {concept}")
    
    # Action buttons
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📖 Review Answers", key="review_answers", use_container_width=True):
            if on_review:
                on_review()
    
    with col2:
        if not passed:
            if st.button("🔄 Retake Quiz", key="retake_quiz", use_container_width=True):
                if on_retake:
                    on_retake()
    
    with col3:
        if passed:
            if st.button("▶ Continue", key="continue_learning", use_container_width=True, type="primary"):
                if on_continue:
                    on_continue()


def render_question_review(
    question: QuizQuestion | dict[str, Any],
    user_answer: str,
    is_correct: bool,
) -> None:
    """Render a question in review mode showing correct/incorrect.
    
    Args:
        question: The question data.
        user_answer: User's submitted answer.
        is_correct: Whether the answer was correct.
    """
    if isinstance(question, QuizQuestion):
        q_text = question.question
        q_options = question.options
        correct_answer = question.correct_answer
        explanation = question.explanation
    else:
        q_text = question.get("question", "")
        q_options = question.get("options", [])
        correct_answer = question.get("correct_answer", "")
        explanation = question.get("explanation", "")
    
    # Question with status indicator
    status_icon = "✅" if is_correct else "❌"
    status_color = "#28a745" if is_correct else "#dc3545"
    
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {status_color};
            padding: 1rem;
            margin: 1rem 0;
            background: #f8f9fa;
            border-radius: 0 8px 8px 0;
        ">
            <strong>{status_icon} {q_text}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Show options with highlighting
    for option in q_options:
        if option == correct_answer:
            st.markdown(f"✓ **{option}** (Correct)")
        elif option == user_answer and not is_correct:
            st.markdown(f"✗ ~~{option}~~ (Your answer)")
        else:
            st.markdown(f"○ {option}")
    
    # Explanation
    if explanation:
        st.info(f"💡 {explanation}")


def _render_progress(current: int, total: int) -> None:
    """Render progress dots for quiz questions.
    
    Args:
        current: Current question index (0-based).
        total: Total questions.
    """
    dots = []
    for i in range(total):
        if i < current:
            dots.append("●")  # Answered
        elif i == current:
            dots.append("◉")  # Current
        else:
            dots.append("○")  # Not answered
    
    st.markdown(
        f"<p style='text-align: center; letter-spacing: 0.3rem;'>{''.join(dots)}</p>",
        unsafe_allow_html=True,
    )


def _render_multiple_choice(
    question_id: str,
    options: list[str],
    selected: str | None = None,
    show_feedback: bool = False,
    answer_result: AnswerResult | None = None,
) -> str | None:
    """Render multiple choice options.
    
    Args:
        question_id: Unique question identifier.
        options: List of answer options.
        selected: Previously selected option.
        show_feedback: Whether feedback is being shown.
        answer_result: Answer result for feedback display.
    
    Returns:
        Selected option if any.
    """
    # Determine which options to highlight
    correct_answer = None
    if show_feedback and answer_result:
        correct_answer = answer_result.correct_answer
    
    # Generate option labels (A, B, C, D, ...)
    labels = [chr(65 + i) for i in range(len(options))]  # A, B, C, D...
    
    # Find index of selected option
    selected_index = None
    if selected:
        try:
            selected_index = options.index(selected)
        except ValueError:
            pass
    
    # Render as radio buttons
    choice = st.radio(
        "Select your answer:",
        options=list(range(len(options))),
        format_func=lambda i: f"{labels[i]}) {options[i]}",
        index=selected_index,
        key=f"mc_{question_id}",
        label_visibility="collapsed",
        disabled=show_feedback,
    )
    
    # Highlight correct/incorrect if showing feedback
    if show_feedback and answer_result and correct_answer:
        for i, option in enumerate(options):
            if option == correct_answer:
                st.success(f"✓ {labels[i]}) {option}")
            elif selected and option == selected and not answer_result.is_correct:
                st.error(f"✗ {labels[i]}) {option}")
    
    return options[choice] if choice is not None else None


def _render_true_false(
    question_id: str,
    selected: str | None = None,
    show_feedback: bool = False,
    answer_result: AnswerResult | None = None,
) -> str | None:
    """Render True/False options.
    
    Args:
        question_id: Unique question identifier.
        selected: Previously selected option.
        show_feedback: Whether feedback is being shown.
        answer_result: Answer result for feedback.
    
    Returns:
        Selected option ("True" or "False") if any.
    """
    options = ["True", "False"]
    return _render_multiple_choice(question_id, options, selected, show_feedback, answer_result)


def _render_feedback(
    answer_result: AnswerResult,
    explanation: str = "",
) -> None:
    """Render feedback after answer submission.
    
    Args:
        answer_result: The answer result with correctness info.
        explanation: Optional explanation text.
    """
    st.markdown("---")
    
    if answer_result.is_correct:
        st.success("✅ Correct! Well done!")
    else:
        st.error(f"❌ Incorrect. The correct answer is: **{answer_result.correct_answer}**")
    
    # Show explanation
    if explanation:
        st.info(f"💡 **Explanation:** {explanation}")
    elif answer_result.explanation:
        st.info(f"💡 **Explanation:** {answer_result.explanation}")


def render_quiz_header(
    module_title: str,
    question_count: int,
) -> None:
    """Render quiz page header.
    
    Args:
        module_title: The module being quizzed.
        question_count: Number of questions in the quiz.
    """
    st.markdown(f"# 📝 Quiz: {module_title}")
    st.markdown(f"*{question_count} questions • Test your understanding*")
    st.markdown("---")


def render_quiz_intro(
    module_title: str,
    question_count: int,
    estimated_time: int = 5,
    on_start: Callable[[], None] | None = None,
) -> None:
    """Render quiz introduction screen before starting.
    
    Args:
        module_title: Module name.
        question_count: Number of questions.
        estimated_time: Estimated completion time in minutes.
        on_start: Callback when Start Quiz button is clicked.
    """
    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #e8f4fd 0%, #f0f7ff 100%);
            border-radius: 15px;
            margin: 2rem 0;
        ">
            <span style="font-size: 3rem;">📝</span>
            <h2>Quiz: {module_title}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Questions", question_count)
    
    with col2:
        st.metric("Est. Time", f"~{estimated_time} min")
    
    st.markdown("### Instructions")
    st.markdown("""
    - Read each question carefully
    - Select the best answer from the options provided
    - You need **80%** to pass and proceed to the next module
    - Don't worry if you don't pass - you can review and try again!
    """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Quiz", key="start_quiz", use_container_width=True, type="primary"):
            if on_start:
                on_start()
