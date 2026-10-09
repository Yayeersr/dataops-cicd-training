"""
ตัวช่วยตั้งค่า Lab 0 / Lab 1 แบบ copy-run — กรอก GUID ลงไฟล์ config ให้ถูกที่ ไม่ต้องไล่แก้มือ
(ลดโอกาสพิมพ์ผิด / สลับ dev-prod ซึ่งเป็นสาเหตุหลักที่ rule ถูกข้ามเงียบๆ)

ไม่แก้อะไรนอกจากไฟล์ config 3 ไฟล์ และไม่รัน git ให้ — คำสั่ง git ยังรันเองตามขั้นตอนใน handout

คำสั่ง (GUID #1–#6 ตามตารางใน Lab 0 ขั้น 5):

  # Lab 0 ขั้น 6 — กรอก workspace-config.yml + endpoint-targets.yml
  python scripts/setup_lab.py config --dev <#1> --prod <#2> --prod-endpoint <#4>

  # Lab 0 ขั้น 7 — เขียน rule ใน fabric_items/parameter.yml
  python scripts/setup_lab.py parameter --dev-endpoint <#3> --prod-endpoint <#4> --lh-dev <#5> --lh-prod <#6>

  # Lab 1 ขั้น 2 — สร้างโค้ด Notebook ที่กรอกชื่อ + GUID แล้ว (ใส่ --copy เพื่อคัดลอกเข้า clipboard)
  python scripts/setup_lab.py notebook <ชื่อ> --dev-endpoint <#3> --lh-dev <#5> --copy

  # เช็คทุกอย่างว่าไฟล์ config สอดคล้องกัน (รันได้ทุกเมื่อ ก่อน push ก็ได้)
  python scripts/setup_lab.py check [--require-all]

รันซ้ำได้ (แก้ GUID ที่กรอกผิดได้โดยรันคำสั่งเดิมด้วยค่าใหม่)
"""

import argparse
import os
import re
import subprocess
import sys

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
WS_CONFIG = os.path.join(ROOT, "workspace-config.yml")
EP_TARGETS = os.path.join(ROOT, "endpoint-targets.yml")
PARAM = os.path.join(ROOT, "fabric_items", "parameter.yml")
NB_CODE = os.path.join(ROOT, "docs", "lab-notebook-code.py")

GUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
PLACEHOLDER_RE = re.compile(r"<[^>]*>")

PARAM_PLACEHOLDERS = {
    "dev_ep": "<WORKSPACE_ID_ENDPOINT_DEV>",
    "prod_ep": "<WORKSPACE_ID_ENDPOINT_PROD>",
    "lh_dev": "<LAKEHOUSE_ID_ENDPOINT_DEV>",
    "lh_prod": "<LAKEHOUSE_ID_ENDPOINT_PROD>",
}


class LabError(Exception):
    pass


# ----------------------------------------------------------------------------- helpers
def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def guid(label, value):
    """ตรวจ format ของ GUID — ตัดช่องว่าง/เครื่องหมายคำพูด/ปีกกาที่ติดมาตอน copy"""
    v = (value or "").strip().strip('"').strip("'").strip("{}").strip().lower()
    if PLACEHOLDER_RE.search(v):
        raise LabError(f"{label}: ยังเป็น placeholder ({value}) — ใส่ GUID จริงจาก URL ของ Fabric")
    if not GUID_RE.match(v):
        raise LabError(
            f"{label}: '{value}' ไม่ใช่ GUID (ต้องหน้าตาแบบ 8-4-4-4-12 เช่น xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) "
            "— copy จาก URL ใน Fabric: เลขหลัง /groups/ = workspace, เลขหลัง /lakehouses/ = Lakehouse"
        )
    return v


def all_distinct(pairs):
    seen = {}
    for label, v in pairs:
        if v in seen:
            raise LabError(
                f"{label} ซ้ำกับ {seen[v]} ({v}) — แต่ละตัวต้องเป็นคนละ GUID "
                "(ซ้ำ = copy ผิดอัน หรือสลับ dev/prod)"
            )
        seen[v] = label


def sub_once(text, pattern, repl, what):
    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise LabError(f"หา {what} ในไฟล์ไม่เจอ — ไฟล์ถูกแก้โครงสร้างไปหรือเปล่า? (ดู README ของ template)")
    return new


def nl(text):
    return "\r\n" if "\r\n" in text else "\n"


# ----------------------------------------------------------------------------- config
def cmd_config(args):
    dev = guid("--dev (#1 workspace dev)", args.dev)
    prod = guid("--prod (#2 workspace prod)", args.prod)
    prod_ep = guid("--prod-endpoint (#4 workspace prod-endpoint)", args.prod_endpoint)
    all_distinct([("#1 dev", dev), ("#2 prod", prod), ("#4 prod-endpoint", prod_ep)])

    t = read(WS_CONFIG)
    t = sub_once(t, r'^(dev:\s*)"[^"]*"', rf'\g<1>"{dev}"', "บรรทัด dev: ใน workspace-config.yml")
    t = sub_once(t, r'^(prod:\s*)"[^"]*"', rf'\g<1>"{prod}"', "บรรทัด prod: ใน workspace-config.yml")
    write(WS_CONFIG, t)

    t = read(EP_TARGETS)
    t = sub_once(t, r'^(\s+prod:\s*)"[^"]*"', rf'\g<1>"{prod_ep}"', "target prod ใน endpoint-targets.yml")
    write(EP_TARGETS, t)

    print("✅ workspace-config.yml  dev  =", dev)
    print("✅ workspace-config.yml  prod =", prod)
    print("✅ endpoint-targets.yml  prod =", prod_ep)
    print("\nขั้นต่อไป: git add workspace-config.yml endpoint-targets.yml → commit → push dev → merge เข้า main → push")


# ----------------------------------------------------------------------------- parameter
PARAM_BLOCK = """find_replace:
  # workspace id ของ endpoint (เขียนตรงเป็น abfss:// path ในโค้ด ไม่ใช้ default_lakehouse attach
  # เพราะเป็นคนละ workspace จาก Notebook เอง — $items.../$id / $workspace.$id resolve ไม่ได้
  # ข้ามเวิร์คสเปซ ต้อง hardcode ตรงนี้แทน)
  - find_value: "{dev_ep}"
    replace_value:
      _ALL_: "{prod_ep}"
    item_type: "Notebook"

  # lakehouse id ของ lh_endpoint_lab
  - find_value: "{lh_dev}"
    replace_value:
      _ALL_: "{lh_prod}"
    item_type: "Notebook"

"""


def cmd_parameter(args):
    v = {
        "dev_ep": guid("--dev-endpoint (#3 workspace dev-endpoint)", args.dev_endpoint),
        "prod_ep": guid("--prod-endpoint (#4 workspace prod-endpoint)", args.prod_endpoint),
        "lh_dev": guid("--lh-dev (#5 Lakehouse dev)", args.lh_dev),
        "lh_prod": guid("--lh-prod (#6 Lakehouse prod)", args.lh_prod),
    }
    all_distinct([("#3 dev-endpoint", v["dev_ep"]), ("#4 prod-endpoint", v["prod_ep"]),
                  ("#5 Lakehouse dev", v["lh_dev"]), ("#6 Lakehouse prod", v["lh_prod"])])

    t = read(PARAM)
    eol = nl(t)
    t = t.replace("\r\n", "\n")
    m = re.search(r"^find_replace:\s*\n", t, flags=re.M)
    end = t.find("\n# --- ตัวอย่าง", m.end() if m else 0)
    if not m or end == -1:
        raise LabError("หาบล็อก find_replace: ใน fabric_items/parameter.yml ไม่เจอ — ไฟล์ถูกแก้โครงสร้างไปหรือเปล่า?")
    t = t[:m.start()] + PARAM_BLOCK.format(**v) + t[end + 1:]
    write(PARAM, t.replace("\n", eol))

    print("✅ fabric_items/parameter.yml")
    print(f"   workspace : {v['dev_ep']}  →  {v['prod_ep']}")
    print(f"   lakehouse : {v['lh_dev']}  →  {v['lh_prod']}")
    print("\nขั้นต่อไป: python scripts/debug_parameterization.py --environment dev   แล้ว git add / commit / push")


# ----------------------------------------------------------------------------- notebook
def copy_to_clipboard(text):
    """คัดลอกเข้า clipboard — Windows ใช้ PowerShell Set-Clipboard (รองรับภาษาไทย), mac/linux ใช้ pbcopy/xclip"""
    if sys.platform == "win32":
        import tempfile

        tmp = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
                f.write(text)
                tmp = f.name
            ps = f"Set-Clipboard -Value (Get-Content -Raw -Encoding UTF8 -LiteralPath '{tmp}')"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True)
            return True
        except Exception:
            pass
        finally:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
    else:
        for cmd in (["pbcopy"], ["xclip", "-selection", "clipboard"]):
            try:
                subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                return True
            except Exception:
                continue
    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def cmd_notebook(args):
    name = args.name.strip()
    if not re.fullmatch(r"[a-z0-9]+", name):
        raise LabError(f"ชื่อ '{args.name}' ต้องเป็น a-z ตัวเล็ก/ตัวเลข เท่านั้น (ไม่มีเว้นวรรค/ขีด/ตัวใหญ่)")
    dev_ep = guid("--dev-endpoint (#3)", args.dev_endpoint)
    lh_dev = guid("--lh-dev (#5)", args.lh_dev)
    if dev_ep == lh_dev:
        raise LabError("#3 กับ #5 เป็น GUID เดียวกัน — workspace กับ Lakehouse ต้องเป็นคนละ GUID")

    code = read(NB_CODE).replace("\r\n", "\n")
    code = sub_once(code, r'^name = "<ชื่อ>"', f'name = "{name}"', 'บรรทัด name = "<ชื่อ>" ใน docs/lab-notebook-code.py')
    code = sub_once(code, r'"<GUID #3 workspace dev-endpoint>"', f'"{dev_ep}"', "placeholder GUID #3")
    code = sub_once(code, r'"<GUID #5 Lakehouse lh_endpoint_lab \(dev\)>"', f'"{lh_dev}"', "placeholder GUID #5")

    if args.out:
        write(args.out, code)
        print(f"✅ เขียนโค้ดลง {args.out}")
    if args.copy:
        if copy_to_clipboard(code):
            print("✅ คัดลอกโค้ดเข้า clipboard แล้ว — ไปวางในเซลล์แรกของ Notebook ใน Fabric ได้เลย (Ctrl+V)")
        else:
            print("⚠ คัดลอกเข้า clipboard ไม่ได้ — copy จากข้อความด้านล่างเอง")
    if not args.copy or not args.out:
        print("\n" + "=" * 20 + " โค้ด Notebook (copy ทั้งก้อน) " + "=" * 20)
        print(code)
        print("=" * 70)
    print("ก่อนกด Run: Add Lakehouse → Existing → lh_endpoint_lab (dev-endpoint ของคุณ)")


# ----------------------------------------------------------------------------- check
def yaml_load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def extract_param(data):
    rules = (data or {}).get("find_replace") or []
    out = {}
    for r in rules:
        if not isinstance(r, dict):
            continue
        rv = r.get("replace_value") or {}
        out.setdefault("rules", []).append((str(r.get("find_value")), str(rv.get("_ALL_")), r.get("item_type")))
    return out.get("rules", [])


def cmd_check(args):
    problems, pending, notes = [], [], []

    def val(label, v):
        """คืนค่า GUID ที่ใช้ได้ หรือ None (บันทึกเป็น pending/problem)"""
        s = str(v or "").strip()
        if not s or PLACEHOLDER_RE.search(s):
            pending.append(f"{label}: ยังไม่ได้กรอก ({s or 'ว่าง'})")
            return None
        if not GUID_RE.match(s.lower()):
            problems.append(f"{label}: '{s}' ไม่ใช่ GUID")
            return None
        return s.lower()

    ws = yaml_load(WS_CONFIG)
    ws_dev = val("workspace-config.yml → dev (#1)", ws.get("dev"))
    ws_prod = val("workspace-config.yml → prod (#2)", ws.get("prod"))

    ep = yaml_load(EP_TARGETS)
    ep_prod = None
    for item, spec in ep.items():
        t = (spec or {}).get("targets") or {}
        if "prod" in t:
            ep_prod = val(f"endpoint-targets.yml → {item}.targets.prod (#4)", t["prod"])

    rules = extract_param(yaml_load(PARAM))
    p = {}
    if len(rules) >= 2:
        p["dev_ep"] = val("parameter.yml → rule 1 find_value (#3)", rules[0][0])
        p["prod_ep"] = val("parameter.yml → rule 1 replace_value (#4)", rules[0][1])
        p["lh_dev"] = val("parameter.yml → rule 2 find_value (#5)", rules[1][0])
        p["lh_prod"] = val("parameter.yml → rule 2 replace_value (#6)", rules[1][1])
    else:
        pending.append("parameter.yml: ยังไม่มี rule ครบ 2 ข้อ (workspace + lakehouse)")

    # ซ้ำกันไม่ได้
    named = [("#1 dev", ws_dev), ("#2 prod", ws_prod), ("#4 prod-endpoint (endpoint-targets)", ep_prod),
             ("#3 dev-endpoint", p.get("dev_ep")), ("#5 Lakehouse dev", p.get("lh_dev")),
             ("#6 Lakehouse prod", p.get("lh_prod"))]
    seen = {}
    for label, v in named:
        if not v:
            continue
        if v in seen and not (label.startswith("#4") and seen[v].startswith("#4")):
            problems.append(f"{label} ซ้ำกับ {seen[v]} ({v}) — น่าจะ copy ผิดอัน/สลับ dev-prod")
        seen.setdefault(v, label)

    # #4 ต้องตรงกันระหว่าง endpoint-targets กับ parameter.yml
    if ep_prod and p.get("prod_ep") and ep_prod != p["prod_ep"]:
        problems.append(
            f"#4 ไม่ตรงกัน: endpoint-targets.yml = {ep_prod} แต่ parameter.yml = {p['prod_ep']} "
            "— ทั้งสองต้องเป็น workspace prod-endpoint เดียวกัน"
        )

    # โค้ด Notebook ต้องใช้ GUID เดียวกับ find_value เป๊ะ (ไม่ตรง = rule ถูกข้ามเงียบๆ)
    nb_checked = 0
    items_dir = os.path.join(ROOT, "fabric_items")
    for dirpath, _, files in os.walk(items_dir):
        if "notebook-content.py" not in files:
            continue
        path = os.path.join(dirpath, "notebook-content.py")
        src = read(path)
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        mw = re.search(r'^ENDPOINT_WORKSPACE_ID\s*=\s*"([^"]*)"', src, flags=re.M)
        ml = re.search(r'^ENDPOINT_LAKEHOUSE_ID\s*=\s*"([^"]*)"', src, flags=re.M)
        if not mw or not ml:
            continue
        nb_checked += 1
        for label, got, want in (("ENDPOINT_WORKSPACE_ID", mw.group(1), p.get("dev_ep")),
                                 ("ENDPOINT_LAKEHOUSE_ID", ml.group(1), p.get("lh_dev"))):
            if PLACEHOLDER_RE.search(got):
                problems.append(f"{rel}: {label} ยังเป็น placeholder — แก้เป็น GUID dev-endpoint ของคุณก่อน commit")
            elif want and got.lower() != want:
                problems.append(
                    f"{rel}: {label} = {got} แต่ parameter.yml find_value = {want} — ไม่ตรงกัน "
                    "rule จะหา GUID ไม่เจอแล้วข้ามเงียบๆ (deploy ผ่านแต่ชี้ dev)"
                )
    if nb_checked:
        notes.append(f"ตรวจโค้ด Notebook {nb_checked} ไฟล์ เทียบกับ parameter.yml แล้ว")
    else:
        notes.append("ยังไม่มี Notebook ใน fabric_items/ ที่ใช้ ENDPOINT_*_ID — ข้ามการเทียบโค้ด (ปกติถ้ายังไม่ถึง Lab 1)")

    for n in notes:
        print("ℹ ", n)
    for m in pending:
        print("⏳", m)
    for m in problems:
        print("❌", m)
    if not problems and not pending:
        print("✅ config ครบและสอดคล้องกันทั้งหมด")
    elif not problems:
        print("\n✅ ไม่พบข้อผิดพลาด — ที่เหลือเป็นช่องที่ยังไม่ได้กรอก (ปกติถ้ายังทำไม่ถึงขั้นนั้น)")
    if problems or (args.require_all and pending):
        sys.exit(1)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="ตัวช่วยตั้งค่า Lab 0 / Lab 1 (ดูตัวอย่างคำสั่งที่หัวไฟล์)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("config", help="กรอก workspace-config.yml + endpoint-targets.yml (Lab 0 ขั้น 6)")
    c.add_argument("--dev", required=True, help="GUID #1 workspace dev")
    c.add_argument("--prod", required=True, help="GUID #2 workspace prod")
    c.add_argument("--prod-endpoint", required=True, help="GUID #4 workspace prod-endpoint")
    c.set_defaults(fn=cmd_config)

    c = sub.add_parser("parameter", help="เขียน rule ใน fabric_items/parameter.yml (Lab 0 ขั้น 7)")
    c.add_argument("--dev-endpoint", required=True, help="GUID #3 workspace dev-endpoint")
    c.add_argument("--prod-endpoint", required=True, help="GUID #4 workspace prod-endpoint")
    c.add_argument("--lh-dev", required=True, help="GUID #5 Lakehouse lh_endpoint_lab ฝั่ง dev")
    c.add_argument("--lh-prod", required=True, help="GUID #6 Lakehouse lh_endpoint_lab ฝั่ง prod")
    c.set_defaults(fn=cmd_parameter)

    c = sub.add_parser("notebook", help="สร้างโค้ด Notebook ที่กรอกชื่อ + GUID แล้ว (Lab 1 ขั้น 2)")
    c.add_argument("name", help="ชื่อย่อ (a-z ตัวเล็ก/ตัวเลข)")
    c.add_argument("--dev-endpoint", required=True, help="GUID #3")
    c.add_argument("--lh-dev", required=True, help="GUID #5")
    c.add_argument("--copy", action="store_true", help="คัดลอกโค้ดเข้า clipboard")
    c.add_argument("--out", help="เขียนโค้ดลงไฟล์ (ไม่บังคับ)")
    c.set_defaults(fn=cmd_notebook)

    c = sub.add_parser("check", help="เช็คว่า config ทุกไฟล์สอดคล้องกัน")
    c.add_argument("--require-all", action="store_true", help="ช่องที่ยังไม่กรอกถือว่า fail ด้วย")
    c.set_defaults(fn=cmd_check)

    args = ap.parse_args()
    try:
        args.fn(args)
    except LabError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
