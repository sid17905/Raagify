"""Prepare an isolated publishing checkout, excluding runtime and private files."""

from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / ".cache" / "publish"
if not (DEST / ".git").is_dir():
    raise SystemExit("First clone the authorized repository into .cache/publish")
skip = {
    "target",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "runtime",
}
folders = {"backend", "frontend", "ml-service", "docs", "verification"}
files = {
    "README.md",
    ".env.example",
    ".gitignore",
    ".gitattributes",
    "compose.yaml",
    "tools/maven.py",
    "tools/publish.py",
}
selected = [ROOT / x for x in files]
for folder in folders:
    for p in (ROOT / folder).rglob("*"):
        if p.is_file() and not any(
            part in skip for part in p.relative_to(ROOT / folder).parts
        ):
            if folder == "ml-service" and "models" in p.parts and p.name != ".gitkeep":
                continue
            if folder == "docs" and p.name == "REA_GUIDE_INDEX.md":
                continue
            selected.append(p)
for source in selected:
    relative = source.relative_to(ROOT)
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
excludes = ROOT / ".cache" / "git-excludes"
excludes.write_text("")
git = [
    "git",
    "-c",
    f"safe.directory={DEST.as_posix()}",
    "-c",
    "core.autocrlf=false",
    "-c",
    f"core.excludesFile={excludes.as_posix()}",
    "-C",
    str(DEST),
]
subprocess.run([*git, "add", "--all"], check=True)
subprocess.run([*git, "add", "--renormalize", "."], check=True)
validation=subprocess.run(
    [*git, "diff", "--cached", "--check", "--", ".", ":(exclude)verification/logs/**"],
    capture_output=True,text=True,encoding="utf-8",errors="replace",
)
if validation.returncode:
    print("\n".join(validation.stdout.splitlines()[:20]))
    raise SystemExit("Staged source whitespace check failed")
print(f"Observed: copied and staged {len(selected)} source/evidence files in {DEST}")
