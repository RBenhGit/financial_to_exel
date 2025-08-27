"""
Basic test to verify pytest discovery works after test reorganization.
"""
import pytest


def test_basic_math():
    """Test basic mathematical operations."""
    assert 2 + 2 == 4
    assert 10 / 2 == 5
    assert 3 * 3 == 9


def test_basic_string():
    """Test basic string operations."""
    assert "hello".upper() == "HELLO"
    assert len("test") == 4


def test_basic_list():
    """Test basic list operations."""
    test_list = [1, 2, 3]
    assert len(test_list) == 3
    assert test_list[0] == 1


if __name__ == "__main__":
    pytest.main([__file__])