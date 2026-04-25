"""اختبارات أساسية"""
import pytest
from bot.utils import generate_referral_code, get_badge, format_file_size


def test_generate_referral_code():
    """اختبار توليد كود إحالة"""
    code = generate_referral_code(123456789)
    assert code.startswith("ref_123456789_")
    assert len(code) > 10


def test_get_badge():
    """اختبار الشارات"""
    assert "مبتدئ" in get_badge(10)
    assert "نشط" in get_badge(100)
    assert "نهم" in get_badge(300)
    assert "محترف" in get_badge(600)
    assert "أسطوري" in get_badge(1500)


def test_format_file_size():
    """اختبار تنسيق حجم الملف"""
    assert format_file_size(500) == "500 B"
    assert "KB" in format_file_size(1500)
    assert "MB" in format_file_size(1500000)
    assert "GB" in format_file_size(1500000000)
