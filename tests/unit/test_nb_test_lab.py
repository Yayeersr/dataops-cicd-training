"""
Dry-run test สำหรับ nb_test_lab — item ทดสอบกลไก CI ของ dataops-cicd-training
ยังไม่มี transformation logic จริง (notebook ว่าง สร้างผ่าน Fabric MCP เพื่อทดสอบ pattern-based
check เท่านั้น) — test นี้แค่พิสูจน์ว่ากลไก "unit_test pattern ต้องมีไฟล์ test คู่กับชื่อ item"
ทำงานถูกต้องจริง (CI หาไฟล์นี้เจอ -> รัน -> ผ่าน)
"""


def test_placeholder():
    assert True
