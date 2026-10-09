# ==========================================================================================
# โค้ดสำหรับ Notebook DQ gate (nb_<ชื่อ>_dq) — สร้างผ่าน Fabric UI ใน ws-dataops-dev-<ชื่อ> แล้ววางโค้ดแยก 2 เซลล์
# (ไฟล์นี้อยู่ใน docs/ จึงไม่ถูก deploy และ CI ไม่สแกน)
#
# Notebook นี้คือ "gate": CI สั่งรันจริงบน Fabric (scripts/run_live_dq_gates.py) ถ้า check ข้างในไม่ผ่าน
# จะ raise → job fail → ผู้เรียนเห็นสีแดงใน Actions (dev: ก่อน deploy · prod: หลัง deploy)
#
# ขั้นตอน:
#   1) สร้าง Notebook ชื่อ nb_<ชื่อ>_dq แล้ว Add Lakehouse → lh_endpoint_lab (dev-endpoint ของคุณ)
#      เหมือน Notebook ใน Lab 1 (Fabric ต้องมี default lakehouse ถึงจะมี spark)
#   2) วางเซลล์ 1 และเซลล์ 2 ด้านล่าง แก้ 3 จุดตามหมายเหตุ แล้ว Run ดูว่า PASS
#   3) Commit ผ่าน Source Control ใน Fabric
#   4) เพิ่มใน dq-gates.yml:     nb_<ชื่อ>_dq: { item_type: notebook, stages: [dev, prod] }
#   5) เพิ่มใน ci-config.yml:    nb_<ชื่อ>_dq: { skip_check: true, skip_reason: "live DQ gate — เช็คผ่าน dq-gate-dev/dq-gate-poc" }
#      (Notebook ปกติต้องมี unit test — gate นี้ต้องรันบน Spark จริง ไม่ใช่ mock จึงเช็คผ่าน job live แทน)
#
# GUID 2 ค่า (ENDPOINT_*) ต้องตรงกับ find_value ใน fabric_items/parameter.yml เป๊ะ
# (rule กว้างของ Notebook เดิมครอบให้อยู่แล้ว — deploy ไป prod แล้วจะชี้ lh_endpoint_lab ฝั่ง prod ให้เอง)
# ==========================================================================================


# ===== เซลล์ 1: ติดตั้ง Great Expectations (เซลล์นี้เซลล์เดียว ห้ามใส่โค้ดอื่นปน) =====
# %pip install "great_expectations>=1.0,<2.0"


# ===== เซลล์ 2: seed ข้อมูลทดสอบ + เช็ค — แก้ 3 จุด: name และ GUID 2 บรรทัด =====
name = "<ชื่อ>"
ENDPOINT_WORKSPACE_ID = "<GUID #3 workspace dev-endpoint>"
ENDPOINT_LAKEHOUSE_ID = "<GUID #5 Lakehouse lh_endpoint_lab (dev)>"

import great_expectations as gx

table_path = (
    f"abfss://{ENDPOINT_WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com"
    f"/{ENDPOINT_LAKEHOUSE_ID}/Tables/dqgate_{name}"
)

# seed ตารางทดสอบถ้ายังไม่มี — ทำให้ gate รันได้ทั้ง dev และ prod โดยไม่ต้องรอ Notebook อื่นเขียนข้อมูลก่อน
try:
    spark.read.format("delta").load(table_path)
except Exception:
    seed_df = spark.createDataFrame([(1, 10), (2, 5), (3, 0)], ["id", "qty"])
    seed_df.write.format("delta").mode("overwrite").save(table_path)

df = spark.read.format("delta").load(table_path).toPandas()

context = gx.get_context(mode="ephemeral")
batch = (
    context.data_sources.add_pandas("pandas")
    .add_dataframe_asset(name="dqgate")
    .add_batch_definition_whole_dataframe("batch")
    .get_batch(batch_parameters={"dataframe": df})
)
result = batch.validate(gx.expectations.ExpectColumnValuesToNotBeNull(column="qty")).success
print(f"[dqgate] qty not-null check: {'PASS' if result else 'FAIL'} ({len(df)} rows)")

# raise เมื่อ fail — นี่คือสิ่งที่ทำให้ job ใน CI แดง (ลองแก้ seed ให้มี None ดูว่า gate fail จริง)
if not result:
    raise AssertionError("Data quality check failed: qty มีค่า null")
