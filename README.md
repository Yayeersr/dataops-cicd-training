# dataops-cicd-training

Repo แยกสำหรับ **DataOps / CI-CD Workshop** โดยเฉพาะ — ไม่ใช้ `dataops-fabric-pilot` (repo ของงานจริง) เพื่อไม่ให้ commit/PR ฝึกหัดของผู้เข้าอบรมปนกับ git history ของงานจริง โครงสร้าง/กลไกเหมือนกับ `dataops-fabric-pilot` ทุกอย่าง (pattern-based CI, `ci-config.yml`, GUID mapping ผ่าน `parameter.yml`) เพียงแต่ตัด item ของจริงออกให้เหลือแค่ scaffold ว่างๆ พร้อมให้ผู้เข้าอบรมมาเพิ่ม `nb_<ชื่อ>_lab` ของตัวเองระหว่าง workshop

ดูดีไซน์เต็มได้ที่ `DataOps-CICD-Workflow.md` (repo เอกสารแยก) และสไลด์/handout ของ workshop

---

## ไฟล์ที่ใช้ในระบบ

### CI (เช็คก่อน merge) — ขาดไม่ได้

| ไฟล์ | หน้าที่ |
|---|---|
| `.github/workflows/fabric-ci.yml` | ตัว workflow ที่รันจริงทุก push/PR |
| `ci-config.yml` | กฎว่า item ไหนต้องเช็คแบบไหน (`unit_test` / `data_quality` / `structure` / `schema` / `none`) — เริ่มต้นมีแค่ `_defaults` ว่างให้ผู้เข้าอบรมมาเพิ่ม entry เอง |
| `requirements.txt` | dependency ที่ CI ต้องติดตั้งก่อนรันเช็ค |
| `tests/unit/test_<name>.py` | test คู่กับ Notebook แต่ละตัว (ชื่อต้องตรงชื่อ item เป๊ะ) |
| `great_expectations/checkpoints/dq_<name>.yml` | checkpoint คู่กับ item ที่ check = `data_quality` |
| `scripts/validate_pipeline_structure.py`, `validate_schema_contract.py` | script กลางสำหรับ check = `structure` / `schema` |

### CD (deploy จริง) — ขาดไม่ได้

| ไฟล์ | หน้าที่ |
|---|---|
| `scripts/deploy.py` | publish item เข้า workspace ปลายทาง + ลบ item เก่าที่หายจาก repo (ใช้ Service Principal ผ่าน GitHub Actions) |
| `scripts/deploy_local.py` | เหมือน `deploy.py` แต่ login ผ่าน browser ตรงๆ — ใช้ตอน SP ไม่มีสิทธิ์บน connection object |
| `fabric_items/` | payload จริงที่จะถูก deploy (sync มาจาก Fabric Git Integration ของ workspace แต่ละคน) |
| `fabric_items/parameter.yml` | remap GUID (lakehouse/workspace) ให้ตรง environment ปลายทาง — มี rule กว้างรองรับ `nb_<ชื่อ>_lab` ของทุกคนไว้แล้ว (ดู TODO ในไฟล์) |
| `workspace-config.yml` | workspace ID ของ environment หลัก (`dev`/`prod`) — จุดเดียวที่ต้องแก้ก่อน training, `fabric-ci.yml` และ `deploy_local.py` อ่านจากที่นี่ |

### เครื่องมือเสริม — ไม่มีก็รันได้

| ไฟล์ | หน้าที่ | ใช้ตอนไหน |
|---|---|---|
| `scripts/debug_parameterization.py` | validate `parameter.yml` แบบ offline ไม่ต้องมี Azure credential | ก่อน push เช็ค syntax เร็วๆ |

---

## ข้อจำกัด/กฎที่ต้องรู้ก่อนเริ่มงาน

1. **สร้าง item ผ่าน Fabric UI เท่านั้น** — ห้าม hand-write ไฟล์ item ตรงเข้า `fabric_items/` เอง (logicalId จะไม่ตรง ทำให้ Fabric sync conflict) ต้องกด **Commit ผ่าน Fabric UI (Source Control panel) เสมอ**

2. **ชื่อไฟล์ test ต้องตรงชื่อ item เป๊ะ** — `nb_xxx.Notebook` ↔ `tests/unit/test_xxx.py` ไม่ตรง CI หาไม่เจอ error ทันที

3. **`ci-config.yml` เป็น fail-safe เข้ม** — ไม่ระบุ = ต้องมี unit test เสมอ (default) ถ้าจะข้ามต้องเขียน `skip_check: true` + `skip_reason` เสมอ ห้ามปล่อยว่าง ไม่งั้น CI fail แทนที่จะผ่านเงียบๆ

4. **`parameter.yml` ระวัง environment key พิมพ์ผิด** — ถ้า key (`dev`/`prod`) ไม่ตรงกับที่ `deploy.py --environment` ส่งเข้าไป **fabric-cicd จะข้าม rule นั้นไปเงียบๆ ไม่ error เตือน** ต้องเช็คเอง

5. **Deploy-prod ต้องมี manual approval** — ตั้งไว้ที่ GitHub Environment protection (`production`) ก่อน push เข้า `main` จะไม่ deploy ทันที

6. **repo นี้เป็นของฝึกหัดล้วนๆ** — item/data ที่เขียนระหว่าง workshop จะถูกล้างทิ้งเป็นระยะ อย่าเก็บงานจริงไว้ที่นี่

---

## Setup ที่ต้องทำก่อน workshop (checklist สำหรับ facilitator)

ดูรายละเอียดเต็มในข้อความสรุปที่ส่งมาพร้อม repo นี้ — สรุปสั้นๆ:

- [ ] สร้าง GitHub repo จาก scaffold นี้ + push ขึ้น
- [ ] ตั้ง branch `dev` (+ branch protection ต้องการ approve อย่างน้อย 1 คน)
- [ ] ตั้ง GitHub Environment `production` + required reviewer
- [ ] ตั้ง GitHub Secrets: `FABRIC_TENANT_ID`, `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_SECRET`
- [ ] สร้าง Fabric workspace: `ws-dataops-dev-<ชื่อ>` ต่อผู้เข้าอบรม 1 คน, `ws-dataops-prod` 1 อัน, `ws-dataops-endpoint-dev` + `ws-dataops-endpoint-prod` อย่างละ 1 อัน (ทุก workspace ต้องอยู่บน Fabric capacity ไม่ใช่ Pro trial)
- [ ] สร้าง Lakehouse `lh_endpoint_lab` ใน `ws-dataops-endpoint-dev` และ `ws-dataops-endpoint-prod`
- [ ] เอา workspace GUID ของ `ws-dataops-prod` ไปใส่ใน `workspace-config.yml` (key `prod`) — `fabric-ci.yml` (deploy-prod job) กับ `deploy_local.py` อ่านจากไฟล์นี้ที่เดียว ไม่ต้องไล่แก้ทีละไฟล์
- [ ] เอา lakehouse/endpoint workspace GUID ที่ได้ไปแทนที่ placeholder ใน `fabric_items/parameter.yml` (แยกคนละเรื่องจาก workspace หลัก)
