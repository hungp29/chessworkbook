import argparse
from pathlib import Path

from translate_io import apply_translations
from workbook_io import ROOT_DIR, find_chapter, sorted_chapters


def resolve_chapter(name: str | None) -> Path:
    if name:
        chapter = find_chapter(name)
        if chapter is None:
            raise SystemExit(f"Chapter not found: {name}")
        return chapter

    chapters = sorted_chapters()
    if not chapters:
        raise SystemExit(f"No chapters found in {ROOT_DIR}")
    return chapters[-1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply pasted translations from translate.txt to metadata files"
    )
    parser.add_argument(
        "chapter",
        nargs="?",
        help="Chapter folder suffix, e.g. test for 03_test",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without updating files",
    )
    args = parser.parse_args()

    chapter_dir = resolve_chapter(args.chapter)
    print(f"Using chapter: {chapter_dir.name}")
    apply_translations(chapter_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
