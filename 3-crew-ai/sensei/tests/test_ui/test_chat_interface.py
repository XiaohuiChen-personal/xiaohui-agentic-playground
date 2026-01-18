"""Unit tests for chat_interface component."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.enums import MessageRole
from sensei.models.schemas import ChatMessage


class TestRenderChat:
    """Tests for render_chat function."""

    def test_render_chat_empty_messages(
        self, mock_streamlit, sample_chat_messages_empty
    ):
        """Test rendering chat with no messages."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat
            
            result = render_chat(messages=sample_chat_messages_empty)
            
            mock_streamlit.markdown.assert_called()
            assert result is None

    def test_render_chat_with_messages(self, mock_streamlit, sample_chat_messages):
        """Test rendering chat with messages."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat
            
            result = render_chat(messages=sample_chat_messages)
            
            # Should render chat messages
            mock_streamlit.chat_message.assert_called()
            assert result is None

    def test_render_chat_with_dict_messages(
        self, mock_streamlit, sample_chat_messages_dict
    ):
        """Test rendering chat with dict messages."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat
            
            result = render_chat(messages=sample_chat_messages_dict)
            
            mock_streamlit.chat_message.assert_called()
            assert result is None

    def test_render_chat_with_send_callback(
        self, mock_streamlit, sample_chat_messages
    ):
        """Test chat with send callback."""
        mock_streamlit.chat_input.return_value = "Test message"
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat
            
            callback = MagicMock()
            result = render_chat(
                messages=sample_chat_messages,
                on_send=callback,
            )
            
            callback.assert_called_with("Test message")
            assert result == "Test message"

    def test_render_chat_no_input(self, mock_streamlit, sample_chat_messages):
        """Test chat when no input is provided."""
        mock_streamlit.chat_input.return_value = None
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat
            
            callback = MagicMock()
            result = render_chat(
                messages=sample_chat_messages,
                on_send=callback,
            )
            
            callback.assert_not_called()
            assert result is None

    def test_render_chat_custom_placeholder(
        self, mock_streamlit, sample_chat_messages_empty
    ):
        """Test chat with custom placeholder."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat
            
            render_chat(
                messages=sample_chat_messages_empty,
                placeholder="Custom placeholder...",
            )
            
            mock_streamlit.chat_input.assert_called()

    def test_render_chat_disabled(
        self, mock_streamlit, sample_chat_messages
    ):
        """Test disabled chat input."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat
            
            render_chat(
                messages=sample_chat_messages,
                disabled=True,
            )
            
            # chat_input should be called with disabled=True
            mock_streamlit.chat_input.assert_called()

    def test_render_chat_no_context_hint(
        self, mock_streamlit, sample_chat_messages_empty
    ):
        """Test chat without context hint."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat
            
            render_chat(
                messages=sample_chat_messages_empty,
                show_context_hint=False,
            )
            
            # Should still render but without hint
            mock_streamlit.markdown.assert_called()


class TestRenderChatCompact:
    """Tests for render_chat_compact function."""

    def test_render_compact_basic(self, mock_streamlit, sample_chat_messages):
        """Test compact chat rendering."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_compact
            
            result = render_chat_compact(messages=sample_chat_messages)
            
            mock_streamlit.markdown.assert_called()
            assert result is None

    def test_render_compact_max_messages(self, mock_streamlit):
        """Test compact chat respects max_messages."""
        messages = [
            ChatMessage(role=MessageRole.USER, content=f"Message {i}")
            for i in range(10)
        ]
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_compact
            
            render_chat_compact(
                messages=messages,
                max_messages=3,
            )
            
            # Should show caption about limited messages
            mock_streamlit.caption.assert_called()

    def test_render_compact_fewer_than_max(self, mock_streamlit):
        """Test compact chat when messages < max."""
        messages = [
            ChatMessage(role=MessageRole.USER, content="Message 1")
        ]
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_compact
            
            render_chat_compact(
                messages=messages,
                max_messages=5,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_compact_with_send(self, mock_streamlit, sample_chat_messages):
        """Test compact chat with send callback."""
        mock_streamlit.chat_input.return_value = "Compact message"
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_compact
            
            callback = MagicMock()
            result = render_chat_compact(
                messages=sample_chat_messages,
                on_send=callback,
            )
            
            callback.assert_called_with("Compact message")
            assert result == "Compact message"


class TestRenderMessage:
    """Tests for _render_message private function."""

    def test_render_message_user(self, mock_streamlit):
        """Test rendering user message."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message
            
            message = ChatMessage(role=MessageRole.USER, content="User message")
            _render_message(message)
            
            mock_streamlit.chat_message.assert_called_with("user", avatar="👤")

    def test_render_message_assistant(self, mock_streamlit):
        """Test rendering assistant message."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message
            
            message = ChatMessage(role=MessageRole.ASSISTANT, content="Assistant message")
            _render_message(message)
            
            mock_streamlit.chat_message.assert_called_with("assistant", avatar="🥋")

    def test_render_message_system(self, mock_streamlit):
        """Test rendering system message."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message
            
            message = ChatMessage(role=MessageRole.SYSTEM, content="System message")
            _render_message(message)
            
            mock_streamlit.info.assert_called_with("System message")

    def test_render_message_dict_user(self, mock_streamlit):
        """Test rendering user message from dict."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message
            
            message = {"role": "user", "content": "Dict user message"}
            _render_message(message)
            
            mock_streamlit.chat_message.assert_called_with("user", avatar="👤")

    def test_render_message_dict_assistant(self, mock_streamlit):
        """Test rendering assistant message from dict."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message
            
            message = {"role": "assistant", "content": "Dict assistant message"}
            _render_message(message)
            
            mock_streamlit.chat_message.assert_called_with("assistant", avatar="🥋")

    def test_render_message_dict_invalid_role(self, mock_streamlit):
        """Test rendering message with invalid role defaults to assistant."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message
            
            message = {"role": "invalid", "content": "Invalid role message"}
            _render_message(message)
            
            # Should default to assistant
            mock_streamlit.chat_message.assert_called_with("assistant", avatar="🥋")

    def test_render_message_dict_with_enum_role(self, mock_streamlit):
        """Test rendering message dict with MessageRole enum."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message
            
            message = {"role": MessageRole.USER, "content": "Enum role message"}
            _render_message(message)
            
            mock_streamlit.chat_message.assert_called_with("user", avatar="👤")


class TestRenderMessageCompact:
    """Tests for _render_message_compact private function."""

    def test_render_compact_user(self, mock_streamlit):
        """Test compact user message."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message_compact
            
            message = ChatMessage(role=MessageRole.USER, content="User message")
            _render_message_compact(message)
            
            mock_streamlit.markdown.assert_called()

    def test_render_compact_assistant(self, mock_streamlit):
        """Test compact assistant message."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message_compact
            
            message = ChatMessage(role=MessageRole.ASSISTANT, content="Assistant message")
            _render_message_compact(message)
            
            mock_streamlit.markdown.assert_called()

    def test_render_compact_long_message_truncated(self, mock_streamlit):
        """Test compact message truncates long content."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message_compact
            
            long_content = "x" * 300
            message = ChatMessage(role=MessageRole.USER, content=long_content)
            _render_message_compact(message)
            
            mock_streamlit.markdown.assert_called()

    def test_render_compact_dict_message(self, mock_streamlit):
        """Test compact rendering from dict."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message_compact
            
            message = {"role": "user", "content": "Dict message"}
            _render_message_compact(message)
            
            mock_streamlit.markdown.assert_called()

    def test_render_compact_invalid_role_string(self, mock_streamlit):
        """Test compact with invalid role string."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_message_compact
            
            message = {"role": "invalid_role", "content": "Invalid"}
            _render_message_compact(message)
            
            # Should default to assistant styling
            mock_streamlit.markdown.assert_called()


class TestRenderChatInput:
    """Tests for _render_chat_input private function."""

    def test_render_chat_input_basic(self, mock_streamlit):
        """Test basic chat input rendering."""
        mock_streamlit.chat_input.return_value = None
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_chat_input
            
            result = _render_chat_input()
            
            mock_streamlit.chat_input.assert_called()
            assert result is None

    def test_render_chat_input_with_message(self, mock_streamlit):
        """Test chat input with message submitted."""
        mock_streamlit.chat_input.return_value = "Hello world"
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_chat_input
            
            callback = MagicMock()
            result = _render_chat_input(on_send=callback)
            
            callback.assert_called_with("Hello world")
            assert result == "Hello world"

    def test_render_chat_input_custom_placeholder(self, mock_streamlit):
        """Test chat input with custom placeholder."""
        mock_streamlit.chat_input.return_value = None
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_chat_input
            
            _render_chat_input(placeholder="Custom placeholder")
            
            mock_streamlit.chat_input.assert_called()

    def test_render_chat_input_disabled(self, mock_streamlit):
        """Test disabled chat input."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_chat_input
            
            _render_chat_input(disabled=True)
            
            mock_streamlit.chat_input.assert_called()


class TestRenderEmptyChat:
    """Tests for _render_empty_chat private function."""

    def test_render_empty_chat(self, mock_streamlit):
        """Test empty chat rendering."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import _render_empty_chat
            
            _render_empty_chat()
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.caption.assert_called()


class TestRenderTypingIndicator:
    """Tests for render_typing_indicator function."""

    def test_render_typing_indicator(self, mock_streamlit):
        """Test typing indicator rendering."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_typing_indicator
            
            render_typing_indicator()
            
            mock_streamlit.markdown.assert_called()


class TestRenderChatError:
    """Tests for render_chat_error function."""

    def test_render_chat_error(self, mock_streamlit):
        """Test chat error rendering."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_error
            
            render_chat_error("Something went wrong")
            
            mock_streamlit.error.assert_called()
            mock_streamlit.caption.assert_called()


class TestRenderChatWithForm:
    """Tests for render_chat_with_form function."""

    def test_render_with_form_basic(self, mock_streamlit, sample_chat_messages):
        """Test form-based chat rendering."""
        mock_streamlit.form_submit_button.return_value = False
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_with_form
            
            result = render_chat_with_form(messages=sample_chat_messages)
            
            mock_streamlit.form.assert_called()
            assert result is None

    def test_render_with_form_empty_messages(
        self, mock_streamlit, sample_chat_messages_empty
    ):
        """Test form chat with empty messages."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_with_form
            
            result = render_chat_with_form(messages=sample_chat_messages_empty)
            
            mock_streamlit.form.assert_called()
            assert result is None

    def test_render_with_form_submit(self, mock_streamlit, sample_chat_messages):
        """Test form submission."""
        mock_streamlit.form_submit_button.return_value = True
        mock_streamlit.text_input.return_value = "Form message"
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_with_form
            
            callback = MagicMock()
            result = render_chat_with_form(
                messages=sample_chat_messages,
                on_send=callback,
            )
            
            callback.assert_called_with("Form message")
            assert result == "Form message"

    def test_render_with_form_empty_input(self, mock_streamlit, sample_chat_messages):
        """Test form with empty input submission."""
        mock_streamlit.form_submit_button.return_value = True
        mock_streamlit.text_input.return_value = ""
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_with_form
            
            callback = MagicMock()
            result = render_chat_with_form(
                messages=sample_chat_messages,
                on_send=callback,
            )
            
            # Callback should not be called for empty input
            callback.assert_not_called()
            assert result is None

    def test_render_with_form_whitespace_input(
        self, mock_streamlit, sample_chat_messages
    ):
        """Test form with whitespace-only input."""
        mock_streamlit.form_submit_button.return_value = True
        mock_streamlit.text_input.return_value = "   "
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_with_form
            
            callback = MagicMock()
            result = render_chat_with_form(
                messages=sample_chat_messages,
                on_send=callback,
            )
            
            callback.assert_not_called()
            assert result is None

    def test_render_with_form_custom_key(self, mock_streamlit, sample_chat_messages):
        """Test form with custom form key."""
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_with_form
            
            render_chat_with_form(
                messages=sample_chat_messages,
                form_key="custom_form",
            )
            
            mock_streamlit.form.assert_called()

    def test_render_with_form_strips_input(
        self, mock_streamlit, sample_chat_messages
    ):
        """Test that form input is stripped."""
        mock_streamlit.form_submit_button.return_value = True
        mock_streamlit.text_input.return_value = "  Message with spaces  "
        
        with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
            from sensei.ui.components.chat_interface import render_chat_with_form
            
            callback = MagicMock()
            result = render_chat_with_form(
                messages=sample_chat_messages,
                on_send=callback,
            )
            
            callback.assert_called_with("Message with spaces")
            assert result == "Message with spaces"
