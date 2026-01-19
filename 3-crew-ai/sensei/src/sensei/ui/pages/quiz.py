"""Quiz page for Sensei.

This module provides the quiz assessment interface with:
- Quiz header with title and progress
- Question display with options
- Answer submission
- Feedback after each answer
- Results display with pass/fail messaging
- Continue/Review options
"""

from typing import Any, Callable

import streamlit as st

from sensei.models.schemas import AnswerResult, Quiz, QuizQuestion, QuizResult
from sensei.ui.components import (
    render_loading_state,
    render_quiz_progress,
    render_sidebar,
)

# Educational tips shown during AI operations
QUIZ_GENERATION_TIPS = [
    "Assessment Crew is analyzing your learning to create targeted questions.",
    "Questions are tailored to test your understanding of key concepts.",
    "The quiz will help identify areas that need more practice.",
    "Take a deep breath - you've got this! 💪",
]

QUIZ_EVALUATION_TIPS = [
    "The AI is analyzing your answers for personalized feedback.",
    "Your weak areas will be identified for focused review.",
    "Performance Analyst is preparing your results.",
]


def render_quiz_page(
    quiz: Quiz | None = None,
    current_question_idx: int = 0,
    quiz_result: QuizResult | None = None,
    last_answer_result: AnswerResult | None = None,
    is_complete: bool = False,
    module_title: str = "",
    current_page: str = "quiz",
    on_navigate: Callable[[str], None] | None = None,
    on_submit_answer: Callable[[str, str], AnswerResult] | None = None,
    on_next_question: Callable[[], None] | None = None,
    on_continue_learning: Callable[[], None] | None = None,
    on_review_mistakes: Callable[[], None] | None = None,
    on_retake_quiz: Callable[[], None] | None = None,
) -> None:
    """Render the quiz page.
    
    Args:
        quiz: Current Quiz object with questions.
        current_question_idx: Index of current question (0-based).
        quiz_result: Final results (shown when quiz is complete).
        last_answer_result: Result of most recent answer submission.
        is_complete: Whether the quiz has been completed.
        module_title: Title of the module being tested.
        current_page: Current page for sidebar highlighting.
        on_navigate: Callback for sidebar navigation.
        on_submit_answer: Callback to submit answer. Takes (question_id, answer).
        on_next_question: Callback to move to next question.
        on_continue_learning: Callback when Continue Learning is clicked.
        on_review_mistakes: Callback when Review Mistakes is clicked.
        on_retake_quiz: Callback when Retake Quiz is clicked.
    
    Example:
        ```python
        render_quiz_page(
            quiz=quiz_service.current_quiz,
            current_question_idx=quiz_service.current_question_idx,
            on_submit_answer=lambda qid, ans: quiz_service.submit_answer(qid, ans),
            on_continue_learning=lambda: navigate_to_learning(),
        )
        ```
    """
    # Render sidebar
    render_sidebar(current_page=current_page, on_navigate=on_navigate)
    
    # Page header
    _render_header(module_title)
    
    if not quiz:
        _render_no_quiz_state()
        return
    
    # Show results if complete
    if is_complete and quiz_result:
        _render_results_section(
            quiz_result=quiz_result,
            on_continue=on_continue_learning,
            on_review=on_review_mistakes,
            on_retake=on_retake_quiz,
        )
        return
    
    # Progress indicator
    total_questions = len(quiz.questions)
    render_quiz_progress(
        current_question=current_question_idx + 1,
        total_questions=total_questions,
    )
    
    # Question display
    if current_question_idx < total_questions:
        question = quiz.questions[current_question_idx]
        _render_question_section(
            question=question,
            last_result=last_answer_result,
            on_submit=on_submit_answer,
            on_next=on_next_question,
        )


def _render_header(module_title: str = "") -> None:
    """Render the quiz page header.
    
    Args:
        module_title: Title of the module being tested.
    """
    st.markdown(
        f"""
        <div style="padding: 1rem 0; margin-bottom: 0.5rem;">
            <h1 style="margin: 0; font-size: 1.75rem;">📝 Quiz: {module_title}</h1>
            <p style="color: #666; margin-top: 0.25rem;">
                Module Assessment
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_no_quiz_state() -> None:
    """Render placeholder when no quiz is loaded."""
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 3rem;
            color: #6c757d;
        ">
            <span style="font-size: 3rem;">📝</span>
            <p>No quiz available. Complete a module to take a quiz.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_question_section(
    question: QuizQuestion,
    last_result: AnswerResult | None,
    on_submit: Callable[[str, str], AnswerResult] | None,
    on_next: Callable[[], None] | None,
) -> None:
    """Render the current question with answer options.
    
    Args:
        question: Current quiz question.
        last_result: Result of previous answer (if any).
        on_submit: Callback to submit answer.
        on_next: Callback to move to next question.
    """
    # Check if this question has been answered
    question_answered = last_result is not None and last_result.question_id == question.id
    
    # Question content
    st.markdown(f"### {question.question}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Initialize session state for selected answer
    answer_key = f"quiz_answer_{question.id}"
    if answer_key not in st.session_state:
        st.session_state[answer_key] = None
    
    # Answer options
    if question.options:
        selected = st.radio(
            "Select your answer:",
            options=question.options,
            key=f"radio_{question.id}",
            disabled=question_answered,
            label_visibility="collapsed",
        )
        st.session_state[answer_key] = selected
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Submit button (only show if not answered)
    if not question_answered:
        col1, col2, col3 = st.columns([0.3, 0.4, 0.3])
        with col2:
            if st.button(
                "Submit Answer",
                key=f"submit_{question.id}",
                use_container_width=True,
                type="primary",
                disabled=st.session_state[answer_key] is None,
            ):
                if on_submit and st.session_state[answer_key]:
                    on_submit(question.id, st.session_state[answer_key])
                    st.rerun()
    
    # Show feedback if answered
    if question_answered and last_result:
        _render_answer_feedback(last_result, question)
        
        # Next question button
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([0.3, 0.4, 0.3])
        with col2:
            if st.button(
                "Next Question →",
                key="next_question_btn",
                use_container_width=True,
            ):
                if on_next:
                    on_next()


def _render_answer_feedback(result: AnswerResult, question: QuizQuestion) -> None:
    """Render feedback after answering a question.
    
    Args:
        result: The answer result with correctness.
        question: The original question for correct answer reference.
    """
    if result.is_correct:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border: 1px solid #28a745;
                border-radius: 10px;
                padding: 1rem;
                margin: 1rem 0;
            ">
                <span style="font-size: 1.25rem;">✅</span>
                <strong style="color: #155724; margin-left: 0.5rem;">Correct!</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                border: 1px solid #dc3545;
                border-radius: 10px;
                padding: 1rem;
                margin: 1rem 0;
            ">
                <span style="font-size: 1.25rem;">❌</span>
                <strong style="color: #721c24; margin-left: 0.5rem;">Incorrect</strong>
                <p style="color: #721c24; margin: 0.5rem 0 0 0;">
                    The correct answer is: <strong>{result.correct_answer}</strong>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Show explanation
    if result.explanation:
        with st.expander("📖 Explanation", expanded=True):
            st.markdown(result.explanation)


def _render_results_section(
    quiz_result: QuizResult,
    on_continue: Callable[[], None] | None,
    on_review: Callable[[], None] | None,
    on_retake: Callable[[], None] | None,
) -> None:
    """Render the quiz results section.
    
    Args:
        quiz_result: Final quiz results.
        on_continue: Callback for Continue Learning.
        on_review: Callback for Review Mistakes.
        on_retake: Callback for Retake Quiz.
    """
    passed = quiz_result.passed
    score_display = f"{quiz_result.score_percentage}%"
    
    # Results banner
    if passed:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border: 2px solid #28a745;
                border-radius: 15px;
                padding: 2rem;
                margin: 1rem 0;
                text-align: center;
            ">
                <span style="font-size: 3rem;">🎉</span>
                <h2 style="color: #155724; margin: 0.5rem 0;">Quiz Complete!</h2>
                <div style="font-size: 2.5rem; font-weight: 700; color: #155724; margin: 0.5rem 0;">
                    {score_display}
                </div>
                <p style="color: #155724; font-size: 1.1rem;">
                    {quiz_result.correct_count}/{quiz_result.total_questions} correct
                </p>
                <p style="color: #155724; font-weight: 500; margin-top: 1rem;">
                    ✅ PASSED! Great job!
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
                border: 2px solid #ffc107;
                border-radius: 15px;
                padding: 2rem;
                margin: 1rem 0;
                text-align: center;
            ">
                <span style="font-size: 3rem;">📚</span>
                <h2 style="color: #856404; margin: 0.5rem 0;">Quiz Complete</h2>
                <div style="font-size: 2.5rem; font-weight: 700; color: #856404; margin: 0.5rem 0;">
                    {score_display}
                </div>
                <p style="color: #856404; font-size: 1.1rem;">
                    {quiz_result.correct_count}/{quiz_result.total_questions} correct
                </p>
                <p style="color: #856404; font-weight: 500; margin-top: 1rem;">
                    Keep practicing! Review the concepts and try again.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Feedback
    if quiz_result.feedback:
        st.markdown("### 💬 Feedback")
        st.markdown(quiz_result.feedback)
    
    # Weak concepts
    if quiz_result.weak_concepts:
        st.markdown("### 📌 Areas to Review")
        for concept in quiz_result.weak_concepts:
            st.markdown(f"- {concept}")
    
    # Action buttons
    st.markdown("<br>", unsafe_allow_html=True)
    
    if passed:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "📖 Review Mistakes",
                key="review_mistakes_btn",
                use_container_width=True,
            ):
                if on_review:
                    on_review()
        with col2:
            if st.button(
                "Continue Learning →",
                key="continue_learning_btn",
                use_container_width=True,
                type="primary",
            ):
                if on_continue:
                    on_continue()
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(
                "📖 Review Concepts",
                key="review_concepts_btn",
                use_container_width=True,
            ):
                if on_review:
                    on_review()
        with col2:
            if st.button(
                "🔄 Retake Quiz",
                key="retake_quiz_btn",
                use_container_width=True,
            ):
                if on_retake:
                    on_retake()
        with col3:
            if st.button(
                "Continue →",
                key="continue_anyway_btn",
                use_container_width=True,
            ):
                if on_continue:
                    on_continue()


def render_quiz_with_services(
    quiz_service,
    user_service=None,
    course_id: str | None = None,
    module_idx: int = 0,
    on_navigate: Callable[[str], None] | None = None,
    on_continue_learning: Callable[[], None] | None = None,
) -> None:
    """Render the quiz page with full service integration.
    
    This function manages quiz state including question progression,
    answer submission, and results.
    
    Args:
        quiz_service: QuizService instance.
        user_service: Optional UserService for preferences.
        course_id: Course ID for the quiz.
        module_idx: Module index for the quiz.
        on_navigate: Navigation callback.
        on_continue_learning: Callback when continuing after quiz.
    
    Example:
        ```python
        render_quiz_with_services(
            quiz_service=QuizService(),
            course_id="python-basics",
            module_idx=0,
            on_continue_learning=lambda: go_to_learning(),
        )
        ```
    """
    # Initialize session state for quiz
    if "quiz_current_idx" not in st.session_state:
        st.session_state["quiz_current_idx"] = 0
    if "quiz_last_result" not in st.session_state:
        st.session_state["quiz_last_result"] = None
    if "quiz_is_complete" not in st.session_state:
        st.session_state["quiz_is_complete"] = False
    if "quiz_final_result" not in st.session_state:
        st.session_state["quiz_final_result"] = None
    
    # Get user preferences
    user_prefs = None
    if user_service:
        user_prefs = user_service.get_preferences()
    
    # Generate quiz if not active
    if not quiz_service.is_quiz_active and course_id is not None:
        with st.spinner("📝 Assessment Crew is creating your quiz..."):
            try:
                quiz_service.generate_quiz(course_id, module_idx, user_prefs=user_prefs)
                # Reset state for new quiz
                st.session_state["quiz_current_idx"] = 0
                st.session_state["quiz_last_result"] = None
                st.session_state["quiz_is_complete"] = False
                st.session_state["quiz_final_result"] = None
            except Exception as e:
                st.error(f"❌ Failed to generate quiz: {str(e)}")
                return
    
    if not quiz_service.is_quiz_active:
        st.error("❌ No quiz available. Complete a module first.")
        return
    
    quiz = quiz_service.current_quiz
    
    # Define callbacks
    def handle_submit(question_id: str, answer: str) -> AnswerResult:
        try:
            result = quiz_service.submit_answer(question_id, answer)
            st.session_state["quiz_last_result"] = result
            return result
        except Exception as e:
            st.error(f"Error submitting answer: {str(e)}")
            return None
    
    def handle_next():
        current_idx = st.session_state["quiz_current_idx"]
        total = len(quiz.questions) if quiz else 0
        
        if current_idx + 1 >= total:
            # Quiz complete - get results with loading state
            with st.spinner("📊 Evaluating your answers..."):
                try:
                    result = quiz_service.get_results(user_prefs)
                    st.session_state["quiz_is_complete"] = True
                    st.session_state["quiz_final_result"] = result
                except Exception as e:
                    st.error(f"Error getting results: {str(e)}")
        else:
            # Move to next question
            st.session_state["quiz_current_idx"] = current_idx + 1
            st.session_state["quiz_last_result"] = None
        
        st.rerun()
    
    def handle_retake():
        # Reset and regenerate quiz with loading state
        if course_id is not None:
            with st.spinner("🔄 Generating a new quiz..."):
                quiz_service.generate_quiz(course_id, module_idx, user_prefs=user_prefs)
            st.session_state["quiz_current_idx"] = 0
            st.session_state["quiz_last_result"] = None
            st.session_state["quiz_is_complete"] = False
            st.session_state["quiz_final_result"] = None
            st.rerun()
    
    # Get module title from quiz
    module_title = quiz.module_title if quiz and quiz.module_title else ""
    
    render_quiz_page(
        quiz=quiz,
        current_question_idx=st.session_state["quiz_current_idx"],
        quiz_result=st.session_state["quiz_final_result"],
        last_answer_result=st.session_state["quiz_last_result"],
        is_complete=st.session_state["quiz_is_complete"],
        module_title=module_title,
        on_navigate=on_navigate,
        on_submit_answer=handle_submit,
        on_next_question=handle_next,
        on_continue_learning=on_continue_learning,
        on_review_mistakes=lambda: on_navigate("learning") if on_navigate else None,
        on_retake_quiz=handle_retake,
    )
