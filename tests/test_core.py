"""Tests for adaptive-personal-syllabus core module."""

from adaptive_personal_syllabus.core import main


def test_main(capsys):
    """Test main entry point."""
    main()
    captured = capsys.readouterr()
    assert "adaptive-personal-syllabus" in captured.out
