from pathlib import Path
import os

ROOT = Path(".")


EXCLUDED = {
    ".git",
    ".venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".streamlit",
    "node_modules",
}


def tree(path, indent=""):
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

    for item in items:

        if item.name in EXCLUDED:
            continue

        if item.is_dir():
            print(f"{indent}📁 {item.name}/")
            tree(item, indent + "    ")

        else:
            size = item.stat().st_size / 1024
            print(f"{indent}📄 {item.name} ({size:.1f} KB)")


print("=" * 70)
print("STOCK AI PROJECT INVENTORY")
print("=" * 70)

tree(ROOT)