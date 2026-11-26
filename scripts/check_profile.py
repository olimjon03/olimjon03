"""Check profile image accessibility and local asset references without network access."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]


class ProfileImages(HTMLParser):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.errors = []
        self.images = 0

    def handle_starttag(self, tag, attrs):
        if tag != "img":
            return
        self.images += 1
        attrs = dict(attrs)
        if "alt" not in attrs:
            self.errors.append(f"{self.name}: image missing alt attribute")
        src = attrs.get("src", "")
        if not src:
            self.errors.append(f"{self.name}: image missing source")
            return
        parsed = urlsplit(src)
        if parsed.scheme or parsed.netloc:
            return
        target = (ROOT / unquote(parsed.path)).resolve()
        if not target.is_relative_to(ROOT) or not target.is_file():
            self.errors.append(f"{self.name}: missing or unsafe local asset {src}")
        if parsed.path == "assets/pro-hero.svg" and "Build with purpose" not in attrs.get("alt", "") and "목적" not in attrs.get("alt", ""):
            self.errors.append(f"{self.name}: banner alt must describe its message")
        if parsed.path == "assets/pro-footer.svg" and "waving" in attrs.get("alt", "").lower():
            self.errors.append(f"{self.name}: footer alt describes obsolete artwork")


def main():
    errors = []
    count = 0
    for name in ("README.md", "README.ko.md"):
        parser = ProfileImages(name)
        parser.feed((ROOT / name).read_text(encoding="utf-8"))
        errors.extend(parser.errors)
        count += parser.images
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: 2 locales, {count} images; alt attributes and local assets checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
