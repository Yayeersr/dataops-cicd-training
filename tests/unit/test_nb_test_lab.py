"""
Unit test จริงสำหรับ nb_test_lab — import ฟังก์ชัน pure Python จาก notebook-content.py
ตรงๆ (ไม่ต้องมี Spark/Fabric runtime) เป็นตัวอย่างแนวทางแยก transformation logic ออกจาก
Spark I/O ให้ unit test ได้จริงใน CI (GitHub Actions runner ไม่มี Spark/Fabric ให้ใช้)

ทำไม import ด้วย importlib แทน `import` ปกติ: notebook-content.py ไม่ได้อยู่ใต้ package
Python ปกติ (อยู่ใน fabric_items/nb_test_lab.Notebook/) — comment marker แบบ Fabric
(# CELL, # META ฯลฯ) เป็นแค่ comment เฉยๆ ทำให้ไฟล์ยังเป็น valid Python module โหลดตรงได้
"""

import importlib.util
import os

_NOTEBOOK_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "fabric_items", "nb_test_lab.Notebook", "notebook-content.py",
)
_spec = importlib.util.spec_from_file_location("nb_test_lab", _NOTEBOOK_PATH)
nb_test_lab = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nb_test_lab)


def test_clean_customer_id_strips_non_digits():
    assert nb_test_lab.clean_customer_id(" A123-45 ") == "12345"


def test_clean_customer_id_handles_none_and_no_digits():
    assert nb_test_lab.clean_customer_id(None) is None
    assert nb_test_lab.clean_customer_id("abc") is None


def test_clip_score_within_range_unchanged():
    assert nb_test_lab.clip_score(85) == 85


def test_clip_score_clips_out_of_range_values():
    assert nb_test_lab.clip_score(150) == 100
    assert nb_test_lab.clip_score(-10) == 0


def test_clip_score_invalid_input_returns_none():
    assert nb_test_lab.clip_score("not-a-number") is None
