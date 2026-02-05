"""
Unit tests for Prompt Loader

Tests cover:
- PromptLoader initialization
- Loading prompts by shortcut
- Loading files directly
- Listing available prompts
- Convenience methods for specific prompts
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestPromptLoaderInit:
    """Tests for PromptLoader initialization"""

    def test_creates_instance(self):
        """Should create PromptLoader instance"""
        from services.prompt_loader import PromptLoader

        loader = PromptLoader()

        assert loader is not None

    def test_accepts_custom_path(self):
        """Should accept custom knowledge path"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PromptLoader(knowledge_path=tmpdir)

            assert str(loader.knowledge_path) == tmpdir

    def test_has_prompt_files_mapping(self):
        """Should have PROMPT_FILES mapping"""
        from services.prompt_loader import PromptLoader

        assert PromptLoader.PROMPT_FILES is not None
        assert len(PromptLoader.PROMPT_FILES) > 0

    def test_mapping_includes_core_shortcuts(self):
        """Should include core workflow shortcuts"""
        from services.prompt_loader import PromptLoader

        shortcuts = PromptLoader.PROMPT_FILES

        assert "full" in shortcuts
        assert "r1" in shortcuts
        assert "r2" in shortcuts
        assert "r3" in shortcuts
        assert "r4" in shortcuts


class TestLoadPrompt:
    """Tests for load_prompt method"""

    def test_loads_prompt_by_shortcut(self):
        """Should load prompt file by shortcut"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test prompt file
            test_filename = PromptLoader.PROMPT_FILES.get("full", "test.md")
            test_path = Path(tmpdir) / test_filename
            test_path.write_text("Test prompt content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.load_prompt("full")

            assert content == "Test prompt content"

    def test_raises_for_unknown_shortcut(self):
        """Should raise ValueError for unknown shortcut"""
        from services.prompt_loader import PromptLoader

        loader = PromptLoader()

        with pytest.raises(ValueError) as exc_info:
            loader.load_prompt("nonexistent_shortcut")

        assert "Unknown shortcut" in str(exc_info.value)

    def test_raises_for_missing_file(self):
        """Should raise FileNotFoundError for missing file"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PromptLoader(knowledge_path=tmpdir)

            with pytest.raises(FileNotFoundError):
                loader.load_prompt("full")

    def test_normalizes_shortcut_case(self):
        """Should normalize shortcut to lowercase"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            test_filename = PromptLoader.PROMPT_FILES.get("full", "test.md")
            test_path = Path(tmpdir) / test_filename
            test_path.write_text("Test content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.load_prompt("FULL")

            assert content == "Test content"

    def test_strips_whitespace_from_shortcut(self):
        """Should strip whitespace from shortcut"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            test_filename = PromptLoader.PROMPT_FILES.get("full", "test.md")
            test_path = Path(tmpdir) / test_filename
            test_path.write_text("Test content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.load_prompt("  full  ")

            assert content == "Test content"


class TestLoadFile:
    """Tests for load_file method"""

    def test_loads_file_by_name(self):
        """Should load file by filename"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test_file.md"
            test_path.write_text("File content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.load_file("test_file.md")

            assert content == "File content"

    def test_raises_for_missing_file(self):
        """Should raise FileNotFoundError for missing file"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PromptLoader(knowledge_path=tmpdir)

            with pytest.raises(FileNotFoundError):
                loader.load_file("nonexistent.md")


class TestListMethods:
    """Tests for listing methods"""

    def test_list_available_prompts(self):
        """Should list all available prompt shortcuts"""
        from services.prompt_loader import PromptLoader

        loader = PromptLoader()
        shortcuts = loader.list_available_prompts()

        assert isinstance(shortcuts, list)
        assert "full" in shortcuts
        assert "r1" in shortcuts

    def test_list_knowledge_files(self):
        """Should list files in knowledge folder"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.md").write_text("content")
            (Path(tmpdir) / "file2.md").write_text("content")

            loader = PromptLoader(knowledge_path=tmpdir)
            files = loader.list_knowledge_files()

            assert "file1.md" in files
            assert "file2.md" in files

    def test_list_knowledge_files_empty_folder(self):
        """Should return empty list for empty folder"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PromptLoader(knowledge_path=tmpdir)
            files = loader.list_knowledge_files()

            assert files == []

    def test_list_knowledge_files_nonexistent_folder(self):
        """Should return empty list for nonexistent folder"""
        from services.prompt_loader import PromptLoader

        loader = PromptLoader(knowledge_path="/nonexistent/path")
        files = loader.list_knowledge_files()

        assert files == []


class TestGetPromptInfo:
    """Tests for get_prompt_info method"""

    def test_returns_prompt_info(self):
        """Should return info dict for valid shortcut"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            test_filename = PromptLoader.PROMPT_FILES.get("full", "test.md")
            test_path = Path(tmpdir) / test_filename
            test_path.write_text("Test content")

            loader = PromptLoader(knowledge_path=tmpdir)
            info = loader.get_prompt_info("full")

            assert info["shortcut"] == "full"
            assert info["filename"] == test_filename
            assert info["exists"] is True
            assert info["size"] > 0

    def test_returns_none_for_unknown_shortcut(self):
        """Should return None for unknown shortcut"""
        from services.prompt_loader import PromptLoader

        loader = PromptLoader()
        info = loader.get_prompt_info("nonexistent")

        assert info is None

    def test_shows_nonexistent_file(self):
        """Should show exists=False for missing file"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PromptLoader(knowledge_path=tmpdir)
            info = loader.get_prompt_info("full")

            assert info["exists"] is False
            assert info["size"] == 0


class TestConvenienceMethods:
    """Tests for convenience methods"""

    def test_build_comprehensive_stage2_prompt(self):
        """Should load round-specific prompt"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create r1 file
            r1_filename = PromptLoader.PROMPT_FILES.get("r1", "r1.md")
            (Path(tmpdir) / r1_filename).write_text("Round 1 content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.build_comprehensive_stage2_prompt(dispute_round=1)

            assert content == "Round 1 content"

    def test_get_round_prompt(self):
        """Should get prompt for specific round"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            r2_filename = PromptLoader.PROMPT_FILES.get("r2", "r2.md")
            (Path(tmpdir) / r2_filename).write_text("Round 2 content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_round_prompt(2)

            assert content == "Round 2 content"

    def test_get_client_report_prompt(self):
        """Should get client report prompt"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("clientreport", "report.md")
            (Path(tmpdir) / filename).write_text("Client report content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_client_report_prompt()

            assert content == "Client report content"

    def test_get_internal_analysis_prompt(self):
        """Should get internal analysis prompt"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("internalanalysis", "analysis.md")
            (Path(tmpdir) / filename).write_text("Analysis content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_internal_analysis_prompt()

            assert content == "Analysis content"

    def test_get_5day_knockout_prompt(self):
        """Should get 5-day knockout prompt"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("5dayknockout", "5day.md")
            (Path(tmpdir) / filename).write_text("5 day knockout content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_5day_knockout_prompt()

            assert content == "5 day knockout content"

    def test_get_identity_theft_prompt(self):
        """Should get identity theft prompt"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("idtheft", "idtheft.md")
            (Path(tmpdir) / filename).write_text("ID theft content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_identity_theft_prompt()

            assert content == "ID theft content"

    def test_get_inquiry_dispute_prompt_standard(self):
        """Should get standard inquiry prompt"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("inquiry", "inquiry.md")
            (Path(tmpdir) / filename).write_text("Inquiry content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_inquiry_dispute_prompt(identity_theft=False)

            assert content == "Inquiry content"

    def test_get_inquiry_dispute_prompt_identity_theft(self):
        """Should get identity theft inquiry prompt"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("inquirytheft", "inquirytheft.md")
            (Path(tmpdir) / filename).write_text("Inquiry theft content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_inquiry_dispute_prompt(identity_theft=True)

            assert content == "Inquiry theft content"

    def test_get_portal_quick_fix_prompt(self):
        """Should get portal quick fix prompt"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("portalfix", "portalfix.md")
            (Path(tmpdir) / filename).write_text("Portal fix content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_portal_quick_fix_prompt()

            assert content == "Portal fix content"

    def test_get_violation_checklist(self):
        """Should get violation checklist"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("checklist", "checklist.md")
            (Path(tmpdir) / filename).write_text("Checklist content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_violation_checklist()

            assert content == "Checklist content"

    def test_get_workflow_cheatsheet(self):
        """Should get workflow cheatsheet"""
        from services.prompt_loader import PromptLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = PromptLoader.PROMPT_FILES.get("workflow", "workflow.md")
            (Path(tmpdir) / filename).write_text("Workflow content")

            loader = PromptLoader(knowledge_path=tmpdir)
            content = loader.get_workflow_cheatsheet()

            assert content == "Workflow content"


class TestFactoryFunction:
    """Tests for get_prompt_loader factory function"""

    def test_returns_prompt_loader(self):
        """Should return PromptLoader instance"""
        from services.prompt_loader import get_prompt_loader, PromptLoader

        loader = get_prompt_loader()

        assert isinstance(loader, PromptLoader)

    def test_accepts_custom_path(self):
        """Should accept custom path"""
        from services.prompt_loader import get_prompt_loader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = get_prompt_loader(knowledge_path=tmpdir)

            assert str(loader.knowledge_path) == tmpdir
