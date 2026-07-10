from pathlib import Path
import re
import shutil

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR / "img_root"
RAW_DIR = ROOT_DIR / "raw"
OUT_DIR = BASE_DIR / "out"
FONTS_DIR = BASE_DIR / "fonts"
CONFIG_FILE = BASE_DIR / "crop_config.json"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def read_text_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def sorted_chapters(root: Path = ROOT_DIR) -> list[Path]:
    return sorted(
        p for p in root.iterdir() if p.is_dir() and p.name != RAW_DIR.name
    )


def find_chapter(name: str, root: Path = ROOT_DIR) -> Path | None:
    matches = [
        p
        for p in root.iterdir()
        if p.is_dir() and p.name != RAW_DIR.name and p.name.endswith(f"_{name}")
    ]
    if len(matches) > 1:
        raise ValueError(f"Multiple chapters match: {name}")
    return matches[0] if matches else None


def sorted_items(chapter: Path) -> list[Path]:
    return sorted(
        p for p in chapter.iterdir() if p.is_dir() and p.name.startswith("item")
    )


def chapter_display_name(chapter: Path) -> str:
    return read_text_file(chapter / "group.txt") or chapter.name


def chapter_description(chapter: Path) -> str:
    return read_text_file(chapter / "description.txt")


def item_title(item: Path) -> str:
    return read_text_file(item / "title.txt") or item.name


def item_note(item: Path) -> str:
    return read_text_file(item / "note.txt")


def list_images(directory: Path) -> list[Path]:
    return sorted(
        p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
    )


def next_chapter_number(root: Path = ROOT_DIR) -> int:
    orders = []
    for path in root.iterdir():
        if not path.is_dir() or path.name == RAW_DIR.name:
            continue
        match = re.match(r"^(\d+)_", path.name)
        if match:
            orders.append(int(match.group(1)))
    return max(orders, default=0) + 1


def slugify_chapter_name(name: str) -> str:
    from ocr_utils import normalize_text

    text = normalize_text(name)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "chapter"


def make_chapter_dir(name: str, root: Path = ROOT_DIR) -> Path:
    order = next_chapter_number(root)
    slug = slugify_chapter_name(name)
    chapter_dir = root / f"{order:02d}_{slug}"
    if chapter_dir.exists():
        raise FileExistsError(f"Chapter already exists: {chapter_dir}")
    chapter_dir.mkdir(parents=True)
    return chapter_dir


def next_item_number(chapter: Path) -> int:
    nums = []
    for path in chapter.glob("item*"):
        match = re.match(r"item(\d+)$", path.name)
        if match:
            nums.append(int(match.group(1)))
    return max(nums, default=0) + 1


def ensure_item_skeleton(item_dir: Path) -> None:
    (item_dir / "raw").mkdir(parents=True, exist_ok=True)
    (item_dir / "cropped").mkdir(parents=True, exist_ok=True)
    for name in ("title.txt", "note.txt"):
        path = item_dir / name
        if not path.exists():
            path.write_text("", encoding="utf-8")


def prepare_item_dir(chapter: Path, number: int) -> Path:
    item_dir = chapter / f"item{number:03d}"
    ensure_item_skeleton(item_dir)
    return item_dir


def remove_item_dirs(chapter: Path) -> None:
    for path in sorted_items(chapter):
        shutil.rmtree(path)
