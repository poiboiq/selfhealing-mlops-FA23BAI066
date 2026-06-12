from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPLACEMENTS = {
    "fa23bai066": input("DockerHub username: ").strip(),
    "35.154.192.217": input("EC2 public IP: ").strip(),
    "admin": input("Jenkins username: ").strip(),
    "1105b128c1088f875d7509e504cdf0414d": input("Jenkins API token: ").strip(),
}

missing = [key for key, value in REPLACEMENTS.items() if not value]
if missing:
    print("Missing values:", ", ".join(missing))
    sys.exit(1)

text_exts = {".py", ".yml", ".yaml", ".html", ".txt", ".md", "", ".rollback"}
for path in ROOT.rglob("*"):
    if ".git" in path.parts or not path.is_file():
        continue
    if path.suffix not in text_exts and path.name not in {"Jenkinsfile", "Jenkinsfile.rollback", "Dockerfile"}:
        continue
    data = path.read_text(encoding="utf-8")
    new = data
    for old, value in REPLACEMENTS.items():
        new = new.replace(old, value)
    if new != data:
        path.write_text(new, encoding="utf-8", newline="\n")
        print("patched", path.relative_to(ROOT))

print("Done. Now commit and push both branches.")
