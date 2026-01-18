"""Unit tests for display formatting utilities."""

from datetime import datetime

import pytest

from sensei.utils.formatters import (
    format_date,
    format_datetime,
    format_duration,
    format_percentage,
    format_score,
    truncate_text,
)


# ==================== TEST: FORMAT DURATION ====================


class TestFormatDuration:
    """Tests for format_duration()."""
    
    def test_zero_minutes(self):
        """Should return '0m' for zero minutes."""
        assert format_duration(0) == "0m"
    
    def test_negative_minutes(self):
        """Should return '0m' for negative values."""
        assert format_duration(-10) == "0m"
        assert format_duration(-100) == "0m"
    
    def test_minutes_only(self):
        """Should return only minutes when less than an hour."""
        assert format_duration(1) == "1m"
        assert format_duration(30) == "30m"
        assert format_duration(45) == "45m"
        assert format_duration(59) == "59m"
    
    def test_hours_only(self):
        """Should return only hours when no remaining minutes."""
        assert format_duration(60) == "1h"
        assert format_duration(120) == "2h"
        assert format_duration(180) == "3h"
    
    def test_hours_and_minutes(self):
        """Should return hours and minutes when both are present."""
        assert format_duration(61) == "1h 1m"
        assert format_duration(90) == "1h 30m"
        assert format_duration(125) == "2h 5m"
        assert format_duration(150) == "2h 30m"
    
    def test_large_values(self):
        """Should handle large values correctly."""
        assert format_duration(600) == "10h"
        assert format_duration(1440) == "24h"  # 1 day in minutes
        assert format_duration(1500) == "25h"


# ==================== TEST: FORMAT PERCENTAGE ====================


class TestFormatPercentage:
    """Tests for format_percentage()."""
    
    def test_zero_percent(self):
        """Should return '0%' for 0.0."""
        assert format_percentage(0.0) == "0%"
    
    def test_hundred_percent(self):
        """Should return '100%' for 1.0."""
        assert format_percentage(1.0) == "100%"
    
    def test_typical_percentages(self):
        """Should correctly format typical percentages."""
        assert format_percentage(0.5) == "50%"
        assert format_percentage(0.75) == "75%"
        assert format_percentage(0.25) == "25%"
    
    def test_rounds_down(self):
        """Should round down to integer (uses int())."""
        assert format_percentage(0.333) == "33%"
        assert format_percentage(0.666) == "66%"
        assert format_percentage(0.999) == "99%"
    
    def test_clamps_above_one(self):
        """Should clamp values above 1.0 to 100%."""
        assert format_percentage(1.5) == "100%"
        assert format_percentage(2.0) == "100%"
    
    def test_clamps_below_zero(self):
        """Should clamp values below 0.0 to 0%."""
        assert format_percentage(-0.5) == "0%"
        assert format_percentage(-1.0) == "0%"


# ==================== TEST: FORMAT DATE ====================


class TestFormatDate:
    """Tests for format_date()."""
    
    def test_typical_date(self):
        """Should format a typical date correctly."""
        dt = datetime(2026, 1, 10)
        assert format_date(dt) == "Jan 10, 2026"
    
    def test_single_digit_day(self):
        """Should format single-digit days with leading zero."""
        dt = datetime(2026, 1, 1)
        assert format_date(dt) == "Jan 01, 2026"
    
    def test_various_months(self):
        """Should correctly abbreviate all months."""
        assert format_date(datetime(2026, 1, 15)) == "Jan 15, 2026"
        assert format_date(datetime(2026, 2, 15)) == "Feb 15, 2026"
        assert format_date(datetime(2026, 3, 15)) == "Mar 15, 2026"
        assert format_date(datetime(2026, 4, 15)) == "Apr 15, 2026"
        assert format_date(datetime(2026, 5, 15)) == "May 15, 2026"
        assert format_date(datetime(2026, 6, 15)) == "Jun 15, 2026"
        assert format_date(datetime(2026, 7, 15)) == "Jul 15, 2026"
        assert format_date(datetime(2026, 8, 15)) == "Aug 15, 2026"
        assert format_date(datetime(2026, 9, 15)) == "Sep 15, 2026"
        assert format_date(datetime(2026, 10, 15)) == "Oct 15, 2026"
        assert format_date(datetime(2026, 11, 15)) == "Nov 15, 2026"
        assert format_date(datetime(2026, 12, 15)) == "Dec 15, 2026"
    
    def test_datetime_with_time_ignores_time(self):
        """Should ignore time component."""
        dt = datetime(2026, 1, 10, 14, 30, 45)
        assert format_date(dt) == "Jan 10, 2026"


# ==================== TEST: FORMAT DATETIME ====================


class TestFormatDatetime:
    """Tests for format_datetime()."""
    
    def test_morning_time(self):
        """Should format AM time correctly."""
        dt = datetime(2026, 1, 10, 9, 30)
        assert format_datetime(dt) == "Jan 10, 2026 at 09:30 AM"
    
    def test_afternoon_time(self):
        """Should format PM time correctly."""
        dt = datetime(2026, 1, 10, 14, 30)
        assert format_datetime(dt) == "Jan 10, 2026 at 02:30 PM"
    
    def test_midnight(self):
        """Should format midnight correctly."""
        dt = datetime(2026, 1, 10, 0, 0)
        assert format_datetime(dt) == "Jan 10, 2026 at 12:00 AM"
    
    def test_noon(self):
        """Should format noon correctly."""
        dt = datetime(2026, 1, 10, 12, 0)
        assert format_datetime(dt) == "Jan 10, 2026 at 12:00 PM"
    
    def test_single_digit_minutes(self):
        """Should format single-digit minutes with leading zero."""
        dt = datetime(2026, 1, 10, 14, 5)
        assert format_datetime(dt) == "Jan 10, 2026 at 02:05 PM"


# ==================== TEST: TRUNCATE TEXT ====================


class TestTruncateText:
    """Tests for truncate_text()."""
    
    def test_text_shorter_than_max(self):
        """Should return unchanged text if shorter than max_length."""
        assert truncate_text("Hi", 10) == "Hi"
        assert truncate_text("Hello", 10) == "Hello"
    
    def test_text_equal_to_max(self):
        """Should return unchanged text if equal to max_length."""
        assert truncate_text("Hello", 5) == "Hello"
    
    def test_text_longer_than_max(self):
        """Should truncate and add suffix."""
        assert truncate_text("Hello World", 8) == "Hello..."
    
    def test_custom_suffix(self):
        """Should use custom suffix."""
        assert truncate_text("Hello World", 9, "…") == "Hello Wo…"
        assert truncate_text("Hello World", 10, " >>") == "Hello W >>"
    
    def test_empty_string(self):
        """Should handle empty string."""
        assert truncate_text("", 10) == ""
    
    def test_max_length_less_than_suffix(self):
        """Should return truncated suffix if max_length <= suffix length."""
        assert truncate_text("Hello World", 3) == "..."
        assert truncate_text("Hello World", 2) == ".."
        assert truncate_text("Hello World", 1) == "."
    
    def test_max_length_equals_suffix(self):
        """Should return exactly the suffix if max_length equals suffix length."""
        assert truncate_text("Hello World", 3) == "..."
    
    def test_unicode_text(self):
        """Should handle unicode correctly."""
        # "你好世界" has 4 characters (len() counts unicode chars correctly)
        # When max_length < len(text), truncation happens
        # max_length=3 with suffix "..." (3 chars) means truncate_at=0, returns just suffix
        assert truncate_text("你好世界", 3) == "..."
        # Longer unicode text - "这是一段很长的中文文本" has 11 chars
        # max_length=8 with suffix "..." means truncate_at=5, returns first 5 chars + "..."
        assert truncate_text("这是一段很长的中文文本", 8) == "这是一段很..."
        # Unicode text that fits
        assert truncate_text("你好", 10) == "你好"
    
    def test_empty_suffix(self):
        """Should work with empty suffix."""
        assert truncate_text("Hello World", 5, "") == "Hello"


# ==================== TEST: FORMAT SCORE ====================


class TestFormatScore:
    """Tests for format_score()."""
    
    def test_perfect_score(self):
        """Should format perfect score correctly."""
        assert format_score(10, 10) == "10/10 (100%)"
        assert format_score(5, 5) == "5/5 (100%)"
    
    def test_zero_score(self):
        """Should format zero score correctly."""
        assert format_score(0, 10) == "0/10 (0%)"
    
    def test_partial_score(self):
        """Should format partial scores correctly."""
        assert format_score(7, 10) == "7/10 (70%)"
        assert format_score(3, 4) == "3/4 (75%)"
    
    def test_zero_total(self):
        """Should handle zero total gracefully."""
        assert format_score(0, 0) == "0/0 (0%)"
    
    def test_rounds_down(self):
        """Should round percentage down (uses int())."""
        assert format_score(1, 3) == "1/3 (33%)"
        assert format_score(2, 3) == "2/3 (66%)"
    
    def test_single_question(self):
        """Should handle single question quizzes."""
        assert format_score(1, 1) == "1/1 (100%)"
        assert format_score(0, 1) == "0/1 (0%)"
