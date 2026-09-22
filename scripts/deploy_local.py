import os
import shutil
import argparse
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items
from azure.identity import InteractiveBrowserCredential

# Manual escape hatch สำหรับกรณีที่ deploy.py (Service Principal) publish ไม่ผ่านเพราะ
# "User does not have access to the connection used in the Pipeline" — SP ไม่มีสิทธิ์บน
# connection ที่ item อ้างอิง (เช่น Copy Data ไปยัง Lakehouse/Warehouse) แต่ user คนที่สร้าง
# connection เองมีสิทธิ์อยู่แล้ว — รันจากเครื่องตัวเอง (เปิด browser login) แทน SP
#
# ข้อจำกัด: รันผ่าน GitHub Actions ไม่ได้ (runner เปิด browser login ไม่ได้) ใช้เป็น fallback
# รันมือเท่านั้น ไม่ใช่ตัวแทน deploy-prod ถาวร

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ITEMS_DIR = os.path.join(BASE_DIR, "..", "fabric_items")

# item type ทั้งหมดที่ fabric-cicd รองรับ — ต้อง sync กับ deploy.py เสมอ (ดู comment ที่นั่น
# สำหรับที่มาของ list นี้: fabric_cicd.constants.ItemType)
ALL_SUPPORTED_ITEM_TYPES = [
    "ApacheAirflowJob",
    "CopyJob",
    "DataAgent",
    "DataBuildToolJob",
    "DataPipeline",
    "Dataflow",
    "Environment",
    "Eventhouse",
    "Eventstream",
    "GraphQLApi",
    "KQLDashboard",
    "KQLDatabase",
    "KQLQueryset",
    "Lakehouse",
    "Map",
    "MirroredDatabase",
    "MLExperiment",
    "MountedDataFactory",
    "Notebook",
    "Ontology",
    "PaginatedReport",
    "Reflex",
    "Report",
    "SemanticModel",
    "SparkJobDefinition",
    "SQLDatabase",
    "UserDataFunction",
    "VariableLibrary",
    "Warehouse",
]


# workspace GUID ของแต่ละ environment ที่รู้จักอยู่แล้ว — ให้ไม่ต้องพิมพ์ GUID เองทุกครั้ง
# TODO(setup): แทนที่ค่า placeholder ด้านล่างด้วย workspace ID จริงหลังสร้าง workspace เสร็จ
ENVIRONMENT_WORKSPACE_IDS = {
    "dev": "<WORKSPACE_ID_DEV>",
    "prod": "<WORKSPACE_ID_PROD>",
    "target": "<WORKSPACE_ID_PROD>",  # alias ของ prod
}


def _clean_pycache(root: str) -> None:
    for dirpath, dirnames, _ in os.walk(root):
        if "__pycache__" in dirnames:
            shutil.rmtree(os.path.join(dirpath, "__pycache__"))
            dirnames.remove("__pycache__")


def _load_dotenv(path: str) -> None:
    # เหมือน deploy.py — โหลด .env local แบบเบาๆ ไม่มีก็ข้ามเงียบๆ (deploy_local.py เองไม่ต้อง
    # ใช้ค่าอะไรจาก .env เพราะ login ผ่าน browser ตรงๆ แต่เก็บไว้เผื่อ script อื่นแชร์ .env เดียวกัน)
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


parser = argparse.ArgumentParser()
parser.add_argument(
    "--workspace",
    required=True,
    help=f"Fabric workspace ID (GUID) หรือ alias: {', '.join(ENVIRONMENT_WORKSPACE_IDS)}",
)
parser.add_argument("--environment", default="dev")
parser.add_argument("--items-path", default=None)
parser.add_argument("--repo-dir", default=None)
args = parser.parse_args()

_load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

workspace_id = ENVIRONMENT_WORKSPACE_IDS.get(args.workspace, args.workspace)

items_root = os.path.join(BASE_DIR, "..", args.repo_dir) if args.repo_dir else REPO_ITEMS_DIR
_clean_pycache(items_root)

credential = InteractiveBrowserCredential()

workspace = FabricWorkspace(
    workspace_id=workspace_id,
    environment=args.environment,
    repository_directory=items_root,
    item_type_in_scope=ALL_SUPPORTED_ITEM_TYPES,
    token_credential=credential,
)

publish_all_items(workspace)
unpublish_all_orphan_items(workspace)
