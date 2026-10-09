# ==========================================================================================
# โค้ดสำหรับ Notebook ของ Lab 1 (nb_<ชื่อ>_lab) — คัดลอกทั้งไฟล์นี้ไปวางในเซลล์แรกของ Notebook
# ที่สร้างผ่าน Fabric UI (ไฟล์นี้อยู่ใน docs/ จึงไม่ถูก deploy และ CI ไม่สแกน)
#
# ต้องแก้ 3 จุดก่อนกด Run:
#   1) name                  = ชื่อย่อของตัวเอง (a-z ตัวเล็ก/ตัวเลข)
#   2) ENDPOINT_WORKSPACE_ID = GUID #3 (workspace dev-endpoint ของคุณ จดไว้ใน Lab 0)
#   3) ENDPOINT_LAKEHOUSE_ID = GUID #5 (Lakehouse lh_endpoint_lab ฝั่ง dev จดไว้ใน Lab 0)
#
# ก่อนกด Run ต้องแนบ Lakehouse ให้ Notebook: Add Lakehouse → Existing lakehouse →
# lh_endpoint_lab ใน ws-dataops-dev-endpoint-<ชื่อ> (Fabric ต้องมี default lakehouse ถึงจะมี spark)
#
# GUID 2 ค่านี้ต้องตรงกับ find_value ใน fabric_items/parameter.yml เป๊ะ — ถ้าแก้ภายหลัง
# ต้องแก้ rule ตาม ไม่งั้น fabric-cicd จะข้าม rule นั้นเงียบๆ
# ==========================================================================================

# ===== แก้ 3 จุด: ชื่อย่อของตัวเอง (a-z ตัวเล็ก/ตัวเลข) และ GUID 2 บรรทัดด้านล่าง =====
name = "<ชื่อ>"


def build_table_name(learner_name):
    """ตั้งชื่อ table ปลายทางเป็น ci_endpoint_test_lab_<ชื่อ> เสมอ กันชื่อชนกับเพื่อนคนอื่น"""
    return f"ci_endpoint_test_lab_{learner_name}"


table_name = build_table_name(name)

# GUID ของ workspace/lakehouse ฝั่ง "dev-endpoint" ของคุณเอง (ที่จดไว้ใน Lab 0)
ENDPOINT_WORKSPACE_ID = "<GUID #3 workspace dev-endpoint>"
ENDPOINT_LAKEHOUSE_ID = "<GUID #5 Lakehouse lh_endpoint_lab (dev)>"

endpoint_path = (
    f"abfss://{ENDPOINT_WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com"
    f"/{ENDPOINT_LAKEHOUSE_ID}/Tables/{table_name}"
)

# เขียนจริงเข้า Lakehouse เฉพาะตอนรันในเครื่องมือ Fabric (มี spark session ให้ใช้) —
# ถ้าไฟล์นี้ถูก import ไปเทสด้วย pytest (ไม่มี spark) จะข้ามส่วนนี้ไปเฉยๆ ไม่ error
if "spark" in dir():
    df = spark.createDataFrame([(1, f"hello from {name}")], ["id", "message"])
    df.write.format("delta").mode("overwrite").save(endpoint_path)
    print(f"เขียนเข้า table: {table_name}")
else:
    print(f"[dry-run นอก Fabric] จะเขียนเข้า table: {table_name} ที่ {endpoint_path}")
