"""
จำลอง live DQ gate บนเครื่องตัวเอง — ใช้ในช่วงสอนแนวคิด Gate โดยไม่ต้องรอ Spark บน Fabric

gate จริง = Notebook/Pipeline ที่มี check (Great Expectations) อยู่ข้างใน แล้ว CI สั่งรันบน Fabric ผ่าน REST API
(scripts/run_live_dq_gate.py) ถ้า check ไม่ผ่าน Notebook จะ raise → job จบด้วย Failed → job ใน CI แดง
สคริปต์นี้ทำ logic เดียวกัน (สร้างข้อมูลเล็กๆ ใน memory → รัน expectation → ผ่านก็จบปกติ ไม่ผ่านก็ exit 1)
ต่างกันแค่รันในเครื่อง ไม่แตะ Fabric จึงเสร็จในไม่กี่วินาที

รัน:
    python scripts/simulate_dq_gate.py
    python scripts/simulate_dq_gate.py --name <ชื่อ>        # ใส่ชื่อ Notebook gate ของคุณในข้อความผลลัพธ์

(สำหรับผู้สอน: --inject-null ใส่ค่า null เข้าไปให้ check ไม่ผ่าน เพื่อโชว์ว่า gate แดงเป็นแบบไหน)
"""

import argparse
import contextlib
import io
import os
import sys

os.environ.setdefault("GX_ANALYTICS_ENABLED", "false")

import pandas as pd  # noqa: E402
import great_expectations as gx  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

parser = argparse.ArgumentParser()
parser.add_argument("--name", default="<ชื่อ>", help="ชื่อย่อของคุณ (ใช้แสดงในผลลัพธ์เท่านั้น)")
parser.add_argument("--inject-null", action="store_true", help="(ผู้สอน) ใส่ค่า null ให้ check ไม่ผ่าน")
args = parser.parse_args()

# ข้อมูลทดสอบเล็กๆ — ใน gate จริง Notebook อ่านจากตารางจริงใน Lakehouse
df = pd.DataFrame({"id": [1, 2, 3], "qty": [10, 5, 0]})
if args.inject_null:
    df.loc[1, "qty"] = None

context = gx.get_context(mode="ephemeral")
batch = (
    context.data_sources.add_pandas("pandas")
    .add_dataframe_asset(name="dqgate")
    .add_batch_definition_whole_dataframe("batch")
    .get_batch(batch_parameters={"dataframe": df})
)

checks = [
    ("qty ต้องไม่เป็น null", gx.expectations.ExpectColumnValuesToNotBeNull(column="qty")),
    ("qty ต้องไม่ติดลบ", gx.expectations.ExpectColumnValuesToBeBetween(column="qty", min_value=0)),
]

failed = []
for label, expectation in checks:
    # GX พ่น progress bar "Calculating Metrics" ลง stderr — กลบไว้ให้ผลลัพธ์อ่านง่าย
    with contextlib.redirect_stderr(io.StringIO()):
        ok = batch.validate(expectation).success
    print(f"[dqgate] {label}: {'PASS' if ok else 'FAIL'} ({len(df)} rows)", flush=True)
    if not ok:
        failed.append(label)

item = f"nb_{args.name}_dq"
if failed:
    # gate จริงจะ raise ใน Notebook → job Failed → CI แดง และบล็อก merge/deploy
    print(f"live data_quality gate fail — notebook '{item}' จบด้วยสถานะ 'Failed' ({', '.join(failed)})", flush=True)
    sys.exit(1)

print(f"live data_quality gate ผ่าน — notebook '{item}' Succeeded", flush=True)
