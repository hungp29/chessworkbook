from pathlib import Path
import sys, re, subprocess

ROOT_DIR = Path("./img_root")
ROOT_DIR.mkdir(exist_ok=True)

if len(sys.argv) < 4:

    raise SystemExit(
        "Usage: create_template.py chapter <order> <folder_name> <display_name> "
        "OR item <chapter> <title> [note]"
    )

mode = sys.argv[1]

if mode == "chapter":

    # chapter <order> <folder_name> <display_name>

    # chapter <folder_name> <display_name>

    description = ""

    if len(sys.argv) >= 4:

        try:

            order = int(sys.argv[2])

            folder_name = sys.argv[3]

            display_name = sys.argv[4]

            if len(sys.argv) == 6:

                description = sys.argv[5]

        except ValueError:

            folder_name = sys.argv[2]

            display_name = sys.argv[3]

            description = ""

            if len(sys.argv) >= 5:

                description = sys.argv[4]

            existing_orders = []

            for p in ROOT_DIR.iterdir():

                if not p.is_dir():

                    continue

                m = re.match(r"^(\d+)_", p.name)

                if m:

                    existing_orders.append(int(m.group(1)))

            order = max(existing_orders, default=0) + 1

    else:

        raise SystemExit(
            "Usage: chapter <order> <folder_name> <display_name> [description]\n"
            "   or: chapter <folder_name> <display_name> [description]"
        )

    chapter_dir = ROOT_DIR / f"{order:02d}_{folder_name}"

    if chapter_dir.exists():

        raise Exception(f"Chapter already exists: {chapter_dir}")

    chapter_dir.mkdir(parents=True)

    (chapter_dir / "group.txt").write_text(
        display_name,
        encoding="utf-8",
    )

    (chapter_dir / "description.txt").write_text(
        description,
        encoding="utf-8",
    )

    print()

    print(f"Created chapter: {display_name}")

    print(f"Order: {order}")

    print(f"Folder: {chapter_dir}")

    print()

elif mode == "item":

    if len(sys.argv) < 3:

        raise SystemExit("Usage: template.py item [chapter] <title> [note]")

    chapters = sorted(
        [p for p in ROOT_DIR.iterdir() if p.is_dir()],
        key=lambda p: p.name,
    )

    if not chapters:

        raise Exception("No chapters found")

    # item <chapter> <title> [note]

    # item <title> [note]

    if len(sys.argv) >= 4:

        chapter_name = sys.argv[2]

        matches = [
            p
            for p in ROOT_DIR.iterdir()
            if p.is_dir() and p.name.endswith(f"_{chapter_name}")
        ]

        if matches:

            if len(matches) > 1:

                raise Exception(f"Multiple chapters match: {chapter_name}")

            chapter = matches[0]

            title = sys.argv[3]

            notes = sys.argv[4:]

        else:

            chapter = chapters[-1]

            title = sys.argv[2]

            notes = sys.argv[3:]

    else:

        chapter = chapters[-1]

        title = sys.argv[2]

        notes = []

    nums = []

    for p in chapter.glob("item*"):

        m = re.match(r"item(\d+)$", p.name)

        if m:

            nums.append(int(m.group(1)))

    next_no = max(nums, default=0) + 1

    item = chapter / f"item{next_no:03d}"

    (item / "raw").mkdir(parents=True)

    (item / "cropped").mkdir()

    (item / "title.txt").write_text(title, encoding="utf-8")

    (item / "note.txt").write_text(
        "\n".join(notes),
        encoding="utf-8",
    )

    print()

    print(f"Created item: {item.name}")

    print(f"Chapter: {chapter.name}")

    print()

    # try:

    #     subprocess.run(["open", str(item / "raw")])

    # except Exception:

    #     pass
