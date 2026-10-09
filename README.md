# dataops-cicd-training (template)

Template repo สำหรับ **DataOps / CI-CD Workshop** — ผู้เข้าอบรมแต่ละคนกด **Use this template** สร้าง repo ของตัวเอง (public) แล้วตั้งค่าเองทั้งหมดใน **Lab 0** (workspace 4 อัน, secrets, config, environment, branch rules) ก่อนทำ **Lab 1** (สร้าง Notebook และพาผ่าน CI) โครงสร้าง/กลไกเหมือนกับงานจริง (pattern-based CI, `ci-config.yml`, GUID mapping ผ่าน `parameter.yml`) เพียงแต่ตัด item ของจริงออกให้เหลือแค่ scaffold ว่างๆ

ดูขั้นตอนทีละข้อได้ที่สไลด์/handout ของ workshop (หัวข้อ Lab 0 และ Lab 1)

---

## ไฟล์ที่ใช้ในระบบ

### CI (เช็คก่อน merge) — ขาดไม่ได้

| ไฟล์ | หน้าที่ |
|---|---|
| `.github/workflows/fabric-ci.yml` | ตัว workflow ที่รันจริงทุก push/PR |
| `ci-config.yml` | กฎว่า item ไหนต้องเช็คแบบไหน (`unit_test` / `data_quality` / `structure` / `schema` / `none`) — เริ่มต้นมีแค่ `_defaults` ว่างให้ผู้เข้าอบรมมาเพิ่ม entry เอง |
| `requirements.txt` | dependency ที่ CI ต้องติดตั้งก่อนรันเช็ค |
| `tests/unit/test_<name>.py` | test คู่กับ Notebook แต่ละตัว (ชื่อต้องตรงชื่อ item เป๊ะ) |
| `scripts/new_lab.py` | สร้าง `tests/unit/test_nb_<ชื่อ>_lab.py` ให้อัตโนมัติ (เช็คก่อนว่ามี item นั้นจริงใน `fabric_items/` แล้วค่อยสร้าง) — ใช้แทนการพิมพ์ชื่อไฟล์เองเพื่อกันพิมพ์ผิด รัน: `python scripts/new_lab.py <ชื่อ>` |
| `scripts/setup_lab.py` | ตัวช่วย copy-run สำหรับ Lab 1: `config` (กรอก `workspace-config.yml` + `endpoint-targets.yml`), `parameter` (เขียน rule ใน `parameter.yml`), `notebook` (สร้างโค้ด Notebook ที่กรอกชื่อ+GUID แล้ว, `--copy` ลง clipboard), `check` (เช็คทุก config สอดคล้องกัน รวมเทียบ GUID ในโค้ด Notebook กับ `find_value` — กัน rule ถูกข้ามเงียบๆ) — ดูตัวอย่างคำสั่งที่หัวไฟล์ |
| `docs/lab-notebook-code.py` | โค้ดที่ผู้เรียนคัดลอกไปวางใน Notebook ของ Lab 1 (แก้ชื่อ + GUID #3, #5) — อยู่ใน `docs/` จึงไม่ถูก deploy และ CI ไม่สแกน |
| `scripts/run_live_dq_gates.py`, `scripts/run_live_dq_gate.py`, `dq-gates.yml` | **live DQ gate** — `dq-gates.yml` ระบุ Notebook/Pipeline ที่มี check (GX) ข้างใน, `run_live_dq_gates.py` สั่งรันจริงบน Fabric ผ่าน REST API แล้วรอผล (`run_live_dq_gate.py` ตัวรันทีละ item) — job `dq-gate-dev` (บน PR → main, workspace dev) และ `dq-gate-poc` (หลัง deploy-prod, workspace prod) ถ้ายังไม่มี entry จะผ่านพร้อม notice · โค้ด Notebook ตัวอย่าง: `docs/lab-dq-gate-notebook-code.py` · เป็นกลไกแยกนอก 5 check pattern โดยตั้งใจ (ต้องมี item deploy อยู่แล้วถึงรันได้) |
| `scripts/simulate_dq_gate.py` | **จำลอง** live DQ gate บนเครื่อง (สร้างข้อมูลเล็กๆ → รัน Great Expectations → exit 0 = ผ่าน / exit 1 = ไม่ผ่าน) ใช้ในช่วงสอนแนวคิด Gate โดยไม่ต้องรอ Spark บน Fabric — ไม่แตะ Fabric ไม่ผูกกับ CI · `--inject-null` (ผู้สอน) ทำให้ check ไม่ผ่านเพื่อโชว์ gate แดง |
| `great_expectations/checkpoints/dq_<name>.yml` | checkpoint คู่กับ item ที่ check = `data_quality` — copy จาก `dq_example.yml` (ตัวอย่าง) แล้วแก้ตามจริง |
| `scripts/run_data_quality_checkpoint.py` | script กลางสำหรับ check = `data_quality` — อ่าน checkpoint yaml แล้วรันผ่าน GX 1.x Python API (ไม่ใช่ CLI แบบเดิม ดู comment ในไฟล์) |
| `great_expectations/fixtures/dq_example_data.csv` | ข้อมูลตัวอย่างคู่กับ `dq_example.yml` |
| `scripts/validate_pipeline_structure.py`, `validate_schema_contract.py` | script กลางสำหรับ check = `structure` / `schema` |

### CD (deploy จริง) — ขาดไม่ได้

| ไฟล์ | หน้าที่ |
|---|---|
| `scripts/deploy.py` | publish item เข้า workspace ปลายทาง + ลบ item เก่าที่หายจาก repo (ใช้ Service Principal ผ่าน GitHub Actions) |
| `scripts/deploy_local.py` | เหมือน `deploy.py` แต่ login ผ่าน browser ตรงๆ — ใช้ตอน SP ไม่มีสิทธิ์บน connection object |
| `fabric_items/` | payload จริงที่จะถูก deploy (sync มาจาก Fabric Git Integration ของ workspace แต่ละคน) |
| `fabric_items_endpoint/` | โฟลเดอร์ที่ผูกกับ **dev-endpoint workspace** ผ่าน Git integration — Lakehouse ที่ผู้เรียน Commit จาก Fabric มาอยู่ที่นี่ แล้ว CI (`deploy_endpoints.py`) เอาไป deploy ที่ prod-endpoint (ใน template ว่างเปล่า มีแค่ `Readme.md`) |
| `fabric_items/parameter.yml` | remap GUID (lakehouse/workspace) ให้ตรง environment ปลายทาง — มี rule กว้างครอบคลุมทุก Notebook แต่ **ต้องแทนที่ placeholder 4 ตัวด้วย GUID ของตัวเอง** (Lab 0 ขั้น 7 · ดู TODO ในไฟล์) |
| `workspace-config.yml` | workspace ID ของ environment หลัก (`dev`/`prod`) — **แต่ละคนแก้เองใน Lab 1 ส่วน A (A.4)**, `fabric-ci.yml` และ `deploy_local.py` อ่านจากที่นี่ |
| `endpoint-targets.yml` | endpoint item ไป workspace ไหนต่อ environment — **แก้ target `prod` เองใน Lab 1 ส่วน A (A.4)** (ตัวอ่านคือ `scripts/deploy_endpoints.py`) |

### เครื่องมือเสริม — ไม่มีก็รันได้

| ไฟล์ | หน้าที่ | ใช้ตอนไหน |
|---|---|---|
| `scripts/debug_parameterization.py` | validate `parameter.yml` แบบ offline ไม่ต้องมี Azure credential | ก่อน push เช็ค syntax เร็วๆ |
| `scripts/generate_parameter_all_types.py` | สแกน repo หา GUID ที่ต้อง remap เทียบกับ item จริงของ dev workspace — `--dry-run` ไม่แก้ไฟล์ (ต้อง login `--interactive`) | **ผู้เรียนรันใน Lab 1 Phase 3** แล้วอ่านผล |
| `scripts/verify_deployed_guids.py` | ตรวจว่า GUID ของ dev ตกค้างใน target หลัง deploy ไหม (PASS/INFO/SKIPPED) | **ผู้สอนรัน demo ใน M9** (ใช้เวลาหลายนาที ผู้เรียนไม่ต้องรัน) |

---

## ข้อจำกัด/กฎที่ต้องรู้ก่อนเริ่มงาน

1. **สร้าง item ผ่าน Fabric UI เท่านั้น** — ห้าม hand-write ไฟล์ item ตรงเข้า `fabric_items/` เอง (logicalId จะไม่ตรง ทำให้ Fabric sync conflict) ต้องกด **Commit ผ่าน Fabric UI (Source Control panel) เสมอ**

2. **ชื่อไฟล์ test ต้องตรงชื่อ item เป๊ะ** — `nb_xxx.Notebook` ↔ `tests/unit/test_xxx.py` ไม่ตรง CI หาไม่เจอ error ทันที

3. **`ci-config.yml` เป็น fail-safe เข้ม** — ไม่ระบุ = ต้องมี unit test เสมอ (default) ถ้าจะข้ามต้องเขียน `skip_check: true` + `skip_reason` เสมอ ห้ามปล่อยว่าง ไม่งั้น CI fail แทนที่จะผ่านเงียบๆ

4. **`parameter.yml` ระวัง environment key พิมพ์ผิด** — ถ้า key (`dev`/`prod`) ไม่ตรงกับที่ `deploy.py --environment` ส่งเข้าไป **fabric-cicd จะข้าม rule นั้นไปเงียบๆ ไม่ error เตือน** ต้องเช็คเอง

5. **Deploy-prod ต้องมี manual approval** — ตั้งไว้ที่ GitHub Environment protection (`production`) ก่อน push เข้า `main` จะไม่ deploy ทันที

6. **repo นี้เป็นของฝึกหัดล้วนๆ** — อย่าเก็บงานจริงไว้ที่นี่ · GUID ใน `workspace-config.yml`, `endpoint-targets.yml`, `fabric_items/parameter.yml` ที่เป็น placeholder (`<...>`) ต้องแทนด้วยค่าของตัวเองก่อนใช้งาน

---

## ผู้เรียนต้องทำเอง — สรุปสั้น

รายละเอียดทีละขั้นอยู่ใน handout

**Lab 0 — ตั้งค่า GitHub + Fabric (ไม่มี GUID ไม่มี Lakehouse)**

1. สร้าง Fabric workspace 4 อัน: `ws-dataops-dev-<ชื่อ>`, `ws-dataops-prod-<ชื่อ>`, `ws-dataops-dev-endpoint-<ชื่อ>`, `ws-dataops-prod-endpoint-<ชื่อ>` (บน Fabric capacity ไม่ใช่ Pro เปล่า)
2. สร้าง repo ของตัวเองจาก template นี้ (**public** — private บนแพลนฟรีไม่มี Required reviewers/branch rules) + แตก branch `dev` + เชิญ buddy + clone ลงเครื่อง
3. ตั้ง GitHub Secrets: `FABRIC_TENANT_ID`, `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_SECRET`
4. ให้ Service Principal เป็น Contributor บนทั้ง 4 workspace
5. สร้าง GitHub token (classic, scope `repo`) → เชื่อม dev-endpoint (`/fabric_items_endpoint`) และ dev (`/fabric_items`) กับ Git ที่ branch `dev`
6. ตั้ง GitHub Environment `production` (Required reviewers + deployment branch `main`)
7. push commit ว่างเข้า `dev` ให้ CI รัน 1 ครั้ง → ตั้ง branch rules (`main` ล็อกเต็ม, `dev` ไม่บังคับ PR)

**Lab 1 — workflow เต็ม (ส่วน A–E)**

- **A. Endpoint:** สร้าง Lakehouse `lh_endpoint_lab` ที่ dev-endpoint → Commit → จด GUID #1–#5 → `setup_lab.py config` → PR `dev→main` → approve `deploy-endpoints` → จด GUID #6
- **B. Notebook + test + parameter:** feature branch → สลับ ws-dev ไป feature branch → สร้าง Notebook → `new_lab.py` (ไฟล์ test) → `setup_lab.py parameter` (ครบ 6 GUID) → dry-run
- **C. DQ gate:** เขียน Notebook `nb_<ชื่อ>_dq` (`docs/lab-dq-gate-notebook-code.py`) → รันให้ผ่านใน Fabric → ลงทะเบียน `dq-gates.yml` + `ci-config.yml` (`skip_check` + เหตุผล); ซ้อมในเครื่องได้ด้วย `scripts/simulate_dq_gate.py`
- **D. Push → PR → dev:** push → CI บน branch → PR เข้า `dev` → buddy approve → merge
- **E. Deploy production:** PR `dev→main` → `dq-gate-dev` → approve environment → `deploy-prod` + `deploy-endpoints` → `dq-gate-poc` → ตรวจใน prod workspace

## ผู้สอนต้องเตรียมก่อนวัน workshop

- [ ] ตั้ง repo นี้เป็น **Template repository** (Settings → Template repository) และให้ branch เริ่มต้น (`main`) มีไฟล์ครบทุกอย่าง
- [ ] Service Principal สำหรับ lab + ค่า Tenant ID / Client ID / Client Secret ไว้แจก (เพิ่ม SP เข้า security group ที่เปิดสิทธิ์เรียก Fabric API)
- [ ] Fabric capacity ที่ผูก workspace ได้ + tenant setting ที่ให้ sync workspace กับ Git และให้ SP เรียก Fabric API
- [ ] จับคู่ buddy สำหรับ approve PR
