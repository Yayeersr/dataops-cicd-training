# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# ## nb_test_lab
#
# ตัวอย่าง notebook สำหรับ training — โชว์แนวทางแยก transformation logic (pure Python)
# ออกจากโค้ดที่ต้องพึ่ง Spark session (`spark.read`/`spark.write`) เพื่อให้ CI unit test
# ฟังก์ชันพวกนี้ได้ตรงๆ โดยไม่ต้องมี live Fabric runtime (ดู tests/unit/test_nb_test_lab.py
# ที่ import ไฟล์นี้ตรงๆ แล้วเรียกฟังก์ชันด้านล่างทดสอบ)
#
# ใน production notebook จริง เซลล์ที่อ่าน/เขียนข้อมูลจาก Lakehouse จะใช้ spark.read.format(...)
# / df.write.format(...) แทน — cell demo ด้านล่างตั้งใจใช้ pandas ธรรมดาแทน เพื่อให้ทั้งไฟล์
# รันได้เองนอก Fabric ด้วย (สำหรับ dry-run test เท่านั้น)

# CELL ********************

def clean_customer_id(raw_id):
    """แปลง customer_id ดิบให้เหลือแต่ตัวเลขล้วน ตัดช่องว่าง/เครื่องหมายพิเศษออก — คืนค่า None ถ้าไม่เหลือตัวเลขเลย"""
    if raw_id is None:
        return None
    cleaned = "".join(ch for ch in str(raw_id) if ch.isdigit())
    return cleaned or None


def clip_score(raw_score, min_value=0, max_value=100):
    """บังคับค่า score ให้อยู่ในช่วง [min_value, max_value] เสมอ กันค่าผิดปกติหลุดเข้า Gold layer — คืนค่า None ถ้าแปลงเป็นตัวเลขไม่ได้"""
    try:
        score = float(raw_score)
    except (TypeError, ValueError):
        return None
    return max(min_value, min(max_value, score))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Demo: แสดงผลลัพธ์การ cleanse ตัวอย่างข้อมูล (ตั้งใจใช้ pandas ธรรมดา ไม่ใช้ spark.read
# เพื่อให้ cell นี้รันได้เองตอน import ทดสอบด้วย pytest ด้วย — ใน production notebook จริง
# แถวนี้ควรเป็น spark.read.format("delta").load(...) แทน)
import pandas as pd

sample = pd.DataFrame({"customer_id": [" A123-45 ", None, "999"], "score": [150, 42, -10]})
sample["customer_id"] = sample["customer_id"].apply(clean_customer_id)
sample["score"] = sample["score"].apply(clip_score)
print(sample)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
