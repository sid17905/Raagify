"""Refresh README screenshots from the user's named pics/ files."""

from pathlib import Path
from urllib.parse import quote
import re

ROOT = Path(__file__).resolve().parent.parent
SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def main():
    pictures = sorted(
        (
            path
            for path in (ROOT / "pics").rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED
        ),
        key=lambda path: path.relative_to(ROOT / "pics").as_posix().casefold(),
    )
    lines = []
    for picture in pictures:
        title = re.sub(r"[_-]+", " ", picture.stem).strip().capitalize()
        title = title.replace("[", "").replace("]", "")
        relative = quote(picture.relative_to(ROOT).as_posix(), safe="/")
        lines.append(f"**Observed — {title}:**\n\n![{title}]({relative})")
    content = (
        "\n\n".join(lines)
        if lines
        else "**Unverified:** Screenshots have not been supplied yet."
    )
    readme = ROOT / "README.md"
    source = readme.read_text(encoding="utf-8")
    pattern = r"(?<=<!-- screenshots:start -->).*?(?=<!-- screenshots:end -->)"
    assert re.search(pattern, source, re.S), "README screenshot markers are required"
    readme.write_text(
        re.sub(pattern, lambda _: "\n\n" + content + "\n\n", source, flags=re.S),
        encoding="utf-8",
    )
    print(f"Observed: linked {len(pictures)} existing screenshots in README")


if __name__ == "__main__":
    main()
