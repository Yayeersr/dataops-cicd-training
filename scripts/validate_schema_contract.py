"""
เรียกจาก fabric-ci.yml สำหรับ item type Lakehouse/Warehouse
เช็คว่า schema ที่ประกาศไว้ตรงตาม contract ที่ downstream พึ่งพาอยู่ไหม
ยังไม่มี Lakehouse item ใน repo นี้ — เป็น placeholder รอเพิ่ม item ประเภทนี้จริง
"""
import sys


def validate(item_path: str) -> bool:
    print(f"[validate_schema_contract] checking {item_path} ... skipped (placeholder)")
    return True


if __name__ == "__main__":
    item_path = sys.argv[1]
    if not validate(item_path):
        sys.exit(1)
