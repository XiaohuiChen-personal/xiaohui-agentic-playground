"""Functional tests with real LLM API calls.

These tests are marked with @pytest.mark.functional and should be run
separately as they incur API costs and are non-deterministic.

Run with: pytest tests/test_functional/ -v -m functional
Skip with: pytest --ignore=tests/test_functional/
"""
