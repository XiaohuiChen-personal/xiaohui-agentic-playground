"""Unit tests for sensei.utils.constants module.

Tests environment loading and API key utilities.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestLoadEnvironment:
    """Tests for load_environment function."""
    
    def test_loads_from_workspace_root(self, tmp_path, monkeypatch):
        """Should load .env from workspace root."""
        # Create a fake workspace structure
        workspace_root = tmp_path / "workspace"
        project_root = workspace_root / "3-crew-ai" / "sensei"
        utils_dir = project_root / "src" / "sensei" / "utils"
        utils_dir.mkdir(parents=True)
        
        # Create .env in workspace root
        env_file = workspace_root / ".env"
        env_file.write_text("TEST_VAR=workspace_value\n")
        
        # Patch the module paths
        import sensei.utils.constants as constants
        monkeypatch.setattr(constants, "WORKSPACE_ROOT", workspace_root)
        monkeypatch.setattr(constants, "PROJECT_ROOT", project_root)
        
        # Clear any existing test var
        monkeypatch.delenv("TEST_VAR", raising=False)
        
        # Load environment
        result = constants.load_environment()
        
        assert result is True
        assert os.environ.get("TEST_VAR") == "workspace_value"
    
    def test_falls_back_to_project_env(self, tmp_path, monkeypatch):
        """Should fall back to project-specific .env if workspace .env not found."""
        # Create a fake workspace structure
        workspace_root = tmp_path / "workspace"
        project_root = workspace_root / "3-crew-ai" / "sensei"
        project_root.mkdir(parents=True)
        
        # Create .env only in project root (not workspace)
        env_file = project_root / ".env"
        env_file.write_text("TEST_VAR=project_value\n")
        
        # Patch the module paths
        import sensei.utils.constants as constants
        monkeypatch.setattr(constants, "WORKSPACE_ROOT", workspace_root)
        monkeypatch.setattr(constants, "PROJECT_ROOT", project_root)
        
        # Clear any existing test var
        monkeypatch.delenv("TEST_VAR", raising=False)
        
        # Load environment
        result = constants.load_environment()
        
        assert result is True
        assert os.environ.get("TEST_VAR") == "project_value"
    
    def test_returns_false_when_no_env_file(self, tmp_path, monkeypatch):
        """Should return False when no .env file exists."""
        # Create empty directories
        workspace_root = tmp_path / "workspace"
        project_root = workspace_root / "3-crew-ai" / "sensei"
        project_root.mkdir(parents=True)
        
        # Patch the module paths
        import sensei.utils.constants as constants
        monkeypatch.setattr(constants, "WORKSPACE_ROOT", workspace_root)
        monkeypatch.setattr(constants, "PROJECT_ROOT", project_root)
        
        # Load environment
        result = constants.load_environment()
        
        assert result is False


class TestGetApiKey:
    """Tests for get_api_key function."""
    
    def test_returns_openai_key(self, monkeypatch):
        """Should return OPENAI_API_KEY when requested."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
        
        from sensei.utils.constants import get_api_key
        
        assert get_api_key("openai") == "sk-test-openai"
        assert get_api_key("OPENAI") == "sk-test-openai"  # Case insensitive
    
    def test_returns_anthropic_key(self, monkeypatch):
        """Should return ANTHROPIC_API_KEY when requested."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic")
        
        from sensei.utils.constants import get_api_key
        
        assert get_api_key("anthropic") == "sk-test-anthropic"
    
    def test_returns_google_key(self, monkeypatch):
        """Should return GOOGLE_API_KEY when requested."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        
        from sensei.utils.constants import get_api_key
        
        assert get_api_key("google") == "test-google-key"
    
    def test_returns_none_for_missing_key(self, monkeypatch):
        """Should return None when API key is not set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        from sensei.utils.constants import get_api_key
        
        assert get_api_key("openai") is None
    
    def test_returns_none_for_unknown_provider(self):
        """Should return None for unknown provider."""
        from sensei.utils.constants import get_api_key
        
        assert get_api_key("unknown_provider") is None


class TestCheckRequiredApiKeys:
    """Tests for check_required_api_keys function."""
    
    def test_returns_all_true_when_all_keys_set(self, monkeypatch):
        """Should return all True when all keys are set."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic")
        monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
        
        from sensei.utils.constants import check_required_api_keys
        
        result = check_required_api_keys()
        
        assert result["openai"] is True
        assert result["anthropic"] is True
        assert result["google"] is True
    
    def test_returns_false_for_missing_keys(self, monkeypatch):
        """Should return False for missing keys."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        
        from sensei.utils.constants import check_required_api_keys
        
        result = check_required_api_keys()
        
        assert result["openai"] is False
        assert result["anthropic"] is False
        assert result["google"] is False
    
    def test_returns_mixed_results(self, monkeypatch):
        """Should correctly report mixed key status."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
        
        from sensei.utils.constants import check_required_api_keys
        
        result = check_required_api_keys()
        
        assert result["openai"] is True
        assert result["anthropic"] is False
        assert result["google"] is True


class TestPathConstants:
    """Tests for path constants."""
    
    def test_project_root_exists(self):
        """PROJECT_ROOT should point to sensei directory."""
        from sensei.utils.constants import PROJECT_ROOT
        
        # Should exist
        assert PROJECT_ROOT.exists()
        # Should contain pyproject.toml
        assert (PROJECT_ROOT / "pyproject.toml").exists()
    
    def test_data_dir_path(self):
        """DATA_DIR should be under PROJECT_ROOT."""
        from sensei.utils.constants import DATA_DIR, PROJECT_ROOT
        
        assert DATA_DIR == PROJECT_ROOT / "data"
    
    def test_courses_dir_path(self):
        """COURSES_DIR should be under DATA_DIR."""
        from sensei.utils.constants import COURSES_DIR, DATA_DIR
        
        assert COURSES_DIR == DATA_DIR / "courses"
