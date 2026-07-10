import argparse
import re

from workbook_io import ROOT_DIR, find_chapter, sorted_chapters


def create_chapter(args: argparse.Namespace) -> None:
    positional = args.rest
    description = ""

    if len(positional) >= 3:
        try:
            order = int(positional[0])
            folder_name = positional[1]
            display_name = positional[2]
            if len(positional) >= 4:
                description = positional[3]
        except ValueError:
            folder_name = positional[0]
            display_name = positional[1]
            if len(positional) >= 3:
                description = positional[2]
            existing_orders = []
            for path in ROOT_DIR.iterdir():
                if not path.is_dir():
                    continue
                match = re.match(r"^(\d+)_", path.name)
                if match:
                    existing_orders.append(int(match.group(1)))
            order = max(existing_orders, default=0) + 1
    elif len(positional) == 2:
        folder_name = positional[0]
        display_name = positional[1]
        existing_orders = []
        for path in ROOT_DIR.iterdir():
            if not path.is_dir():
                continue
            match = re.match(r"^(\d+)_", path.name)
            if match:
                existing_orders.append(int(match.group(1)))
        order = max(existing_orders, default=0) + 1
    else:
        raise SystemExit(
            "Usage: template.py chapter <folder_name> <display_name> [description]\n"
            "   or: template.py chapter <order> <folder_name> <display_name> [description]"
        )

    if args.order is not None:
        order = args.order

    chapter_dir = ROOT_DIR / f"{order:02d}_{folder_name}"
    if chapter_dir.exists():
        raise SystemExit(f"Chapter already exists: {chapter_dir}")

    chapter_dir.mkdir(parents=True)
    (chapter_dir / "group.txt").write_text(display_name, encoding="utf-8")
    (chapter_dir / "description.txt").write_text(description, encoding="utf-8")

    print()
    print(f"Created chapter: {display_name}")
    print(f"Order: {order}")
    print(f"Folder: {chapter_dir}")
    print()


def create_item(args: argparse.Namespace) -> None:
    chapters = sorted_chapters()
    if not chapters:
        raise SystemExit(f"No chapters found in {ROOT_DIR}")

    positional = args.rest
    if len(positional) >= 2:
        chapter = find_chapter(positional[0])
        if chapter is not None:
            title = positional[1]
            note = "\n".join(positional[2:]) if len(positional) > 2 else (args.note or "")
        else:
            chapter = chapters[-1]
            title = positional[0]
            note = "\n".join(positional[1:]) if len(positional) > 1 else (args.note or "")
    else:
        chapter = chapters[-1]
        title = positional[0]
        note = args.note or ""

    nums = []
    for path in chapter.glob("item*"):
        match = re.match(r"item(\d+)$", path.name)
        if match:
            nums.append(int(match.group(1)))

    next_no = max(nums, default=0) + 1
    item = chapter / f"item{next_no:03d}"
    (item / "raw").mkdir(parents=True)
    (item / "cropped").mkdir()
    (item / "title.txt").write_text(title, encoding="utf-8")
    (item / "note.txt").write_text(note, encoding="utf-8")

    print()
    print(f"Created item: {item.name}")
    print(f"Chapter: {chapter.name}")
    print()


def main() -> None:
    ROOT_DIR.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="Create chapter or item folders")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    chapter_parser = subparsers.add_parser("chapter", help="Create a new chapter")
    chapter_parser.add_argument(
        "rest",
        nargs="+",
        help='[order] folder_name display_name [description]',
    )
    chapter_parser.add_argument(
        "--order",
        type=int,
        help="Override chapter order number",
    )
    chapter_parser.set_defaults(func=create_chapter)

    item_parser = subparsers.add_parser("item", help="Create a new item")
    item_parser.add_argument(
        "rest",
        nargs="+",
        help='[chapter] title [note...] — e.g. stalemate "My title" hint here',
    )
    item_parser.add_argument(
        "--note",
        default="",
        help="Optional item note (used when no extra positional notes)",
    )
    item_parser.set_defaults(func=create_item)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
