import re
from pathlib import Path

from workbook_io import sorted_items

TRANSLATE_SEPARATOR = "---"
MERGE_HINT_PATTERN = re.compile(r"^gộp\s*ý", re.IGNORECASE)


def format_item_block(descriptions: list[str]) -> str:
    lines = [f"- {desc}" for desc in descriptions]
    if len(descriptions) >= 3:
        merge_nums = ", ".join(str(i) for i in range(2, len(descriptions) + 1))
        lines.append(f"gộp ý {merge_nums} lại")
    return "\n".join(lines)


def format_translate_file(
    group_name: str,
    chapter_description: str,
    item_blocks: list[list[str]],
) -> str:
    parts = [
        f"- {group_name}",
        f"- {chapter_description}",
        "",
    ]
    parts.append("\n\n".join(format_item_block(block) for block in item_blocks))
    parts.extend(["", TRANSLATE_SEPARATOR, ""])
    return "\n".join(parts)


def parse_bullet_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    if MERGE_HINT_PATTERN.match(stripped):
        return None
    if stripped.startswith("- "):
        return stripped[2:].strip()
    return stripped


def parse_translate_section(text: str) -> tuple[str, str, list[list[str]]]:
    blocks = [block for block in text.strip().split("\n\n") if block.strip()]
    if not blocks:
        raise ValueError("Translation section is empty")

    chapter_lines = []
    for line in blocks[0].splitlines():
        parsed = parse_bullet_line(line)
        if parsed is not None:
            chapter_lines.append(parsed)

    if not chapter_lines:
        raise ValueError("Missing chapter translation lines")

    group_name = chapter_lines[0]
    chapter_description = chapter_lines[1] if len(chapter_lines) > 1 else ""

    item_blocks: list[list[str]] = []
    for block in blocks[1:]:
        lines = []
        for line in block.splitlines():
            parsed = parse_bullet_line(line)
            if parsed is not None:
                lines.append(parsed)
        if lines:
            item_blocks.append(lines)

    return group_name, chapter_description, item_blocks


def split_translate_file(content: str) -> tuple[str, str]:
    if TRANSLATE_SEPARATOR not in content:
        raise ValueError(
            f"Separator '{TRANSLATE_SEPARATOR}' not found in translate.txt"
        )
    source, translation = content.split(TRANSLATE_SEPARATOR, 1)
    return source, translation


def apply_translations(chapter_dir: Path, *, dry_run: bool = False) -> None:
    translate_path = chapter_dir / "translate.txt"
    if not translate_path.exists():
        raise SystemExit(f"File not found: {translate_path}")

    content = translate_path.read_text(encoding="utf-8")
    try:
        _, translation = split_translate_file(content)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if not translation.strip():
        raise SystemExit(
            "No translations found below separator. Paste translations and retry."
        )

    try:
        group_name, chapter_description, item_blocks = parse_translate_section(
            translation
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    items = sorted_items(chapter_dir)
    if len(item_blocks) != len(items):
        raise SystemExit(
            f"Translation has {len(item_blocks)} item block(s) but chapter has "
            f"{len(items)} item folder(s)."
        )

    writes = [
        (chapter_dir / "group.txt", group_name),
        (chapter_dir / "description.txt", chapter_description),
    ]
    for item_dir, lines in zip(items, item_blocks):
        title = lines[0]
        note = "\n".join(lines[1:]) if len(lines) > 1 else ""
        writes.append((item_dir / "title.txt", title))
        writes.append((item_dir / "note.txt", note))

    for path, text in writes:
        if dry_run:
            preview = text.replace("\n", "\\n")[:60]
            print(f"  {path.relative_to(chapter_dir)}: {preview!r}")
        else:
            path.write_text(text, encoding="utf-8")

    if dry_run:
        print("(dry-run: no files written)")
    else:
        print(f"Applied translations to {chapter_dir.name}")
        print(f"  group.txt: {group_name!r}")
        print(f"  description.txt: {len(chapter_description)} chars")
        for item_dir, lines in zip(items, item_blocks):
            print(f"  {item_dir.name}/title.txt: {lines[0][:50]!r}...")
