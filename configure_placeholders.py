from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPLACEMENTS = {
    "YOUR_DOCKERHUB_USERNAME": input("DockerHub username: ").strip(),
    "YOUR_EC2_PUBLIC_IP": input("EC2 public IP: ").strip(),
    "YOUR_JENKINS_USERNAME": input("Jenkins username: ").strip(),
    "YOUR_JENKINS_API_TOKEN": input("Jenkins API token: ").strip(),
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
