import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pytesseract
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps
from pytesseract.pytesseract import TesseractNotFoundError

from ocr_utils import configure_tesseract
from workbook_io import (
    CONFIG_FILE,
    FONTS_DIR,
    ROOT_DIR,
    find_chapter,
    list_images,
    sorted_chapters,
    sorted_items,
)

_tesseract_warning_shown = False


def warn_missing_tesseract() -> None:
    global _tesseract_warning_shown
    if _tesseract_warning_shown:
        return
    _tesseract_warning_shown = True
    print(
        "WARNING: tesseract not found; assuming white at bottom.\n"
        "  Install: brew install tesseract\n"
        "  Or override: crop.py --white-bottom  /  crop.py --black-bottom"
    )

# def add_board_border(
#     img,
#     border_size=6,
#     border_color=(220, 220, 220),
# ):
#     return ImageOps.expand(
#         img,
#         border=border_size,
#         fill=border_color,
#     )
def add_board_border(img):
    outer = 10
    inner = 1

    img = ImageOps.expand(
        img,
        border=outer,
        fill=(245, 245, 245),
    )

    img = ImageOps.expand(
        img,
        border=inner,
        fill=(200, 200, 200),
    )

    return img, outer + inner

def detect_board_orientation(img, *, force_flipped: bool | None = None):
    if force_flipped is not None:
        return force_flipped

    if not configure_tesseract():
        warn_missing_tesseract()
        return False

    img = img.convert("RGB")
    w, h = img.size
    square = w / 8

    region = img.crop((0, 0, int(square * 0.35), int(square * 0.35)))
    gray = ImageEnhance.Contrast(region.convert("L")).enhance(4)

    try:
        text = pytesseract.image_to_string(
            gray,
            config="--psm 10 -c tessedit_char_whitelist=12345678",
        ).strip()
    except TesseractNotFoundError:
        warn_missing_tesseract()
        return False

    if text == "1":
        return True  # black ở dưới
    if text == "8":
        return False  # white ở dưới

    print(f"WARNING: cannot detect orientation, OCR result='{text}'")
    return False


def has_checkmark(img, box, corner):
    img = img.convert("RGB")
    pixels = img.load()
    x1, y1, x2, y2 = box

    TARGET = (126, 183, 78)
    TOLERANCE = 15

    if corner == "top_left":
        scan_x1, scan_y1 = x1, y1
        scan_x2 = int(x1 + (x2 - x1) * 0.30)
        scan_y2 = int(y1 + (y2 - y1) * 0.35)
    elif corner == "top_right":
        scan_x1 = int(x1 + (x2 - x1) * 0.70)
        scan_y1 = y1
        scan_x2, scan_y2 = x2, int(y1 + (y2 - y1) * 0.35)
    elif corner == "bottom_left":
        scan_x1, scan_y1 = x1, int(y1 + (y2 - y1) * 0.65)
        scan_x2 = int(x1 + (x2 - x1) * 0.30)
        scan_y2 = y2
    elif corner == "bottom_right":
        scan_x1 = int(x1 + (x2 - x1) * 0.70)
        scan_y1 = int(y1 + (y2 - y1) * 0.65)
        scan_x2, scan_y2 = x2, y2
    else:
        raise ValueError(f"Unknown corner: {corner}")

    count = 0
    for y in range(scan_y1, scan_y2):
        for x in range(scan_x1, scan_x2):
            r, g, b = pixels[x, y]
            if (
                abs(r - TARGET[0]) <= TOLERANCE
                and abs(g - TARGET[1]) <= TOLERANCE
                and abs(b - TARGET[2]) <= TOLERANCE
            ):
                count += 1
                if count >= 20:
                    return True
    return False


def draw_corner_box(
    draw,
    box,
    width=6,
    corner_len=20,
    skip_top_left=False,
    skip_top_right=False,
    skip_bottom_left=False,
    skip_bottom_right=False,
):
    x1, y1, x2, y2 = box

    if not skip_top_left:
        draw.line((x1, y1, x1 + corner_len, y1), fill="black", width=width)
        draw.line((x1, y1, x1, y1 + corner_len), fill="black", width=width)

    if not skip_top_right:
        draw.line((x2 - corner_len, y1, x2, y1), fill="black", width=width)
        draw.line((x2, y1, x2, y1 + corner_len), fill="black", width=width)

    if not skip_bottom_left:
        draw.line((x1, y2, x1 + corner_len, y2), fill="black", width=width)
        draw.line((x1, y2 - corner_len, x1, y2), fill="black", width=width)

    if not skip_bottom_right:
        draw.line((x2 - corner_len, y2, x2, y2), fill="black", width=width)
        draw.line((x2, y2 - corner_len, x2, y2), fill="black", width=width)


def get_square_color(img, col, row, square, rel_x=0.5, rel_y=0.5):
    sample_x = int(col * square + square * rel_x)
    sample_y = int(row * square + square * rel_y)
    return img.getpixel((sample_x, sample_y))


def redraw_coordinates(img, flipped=False):
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    square = w / 8

    try:
        font = ImageFont.truetype(
            str(FONTS_DIR / "NotoSans-Bold.ttf"),
            int(square * 0.25),
        )
    except OSError:
        font = ImageFont.load_default()

    WHITE_TEXT = (84, 82, 81)
    GREEN_TEXT = (248, 248, 248)

    files = "hgfedcba" if flipped else "abcdefgh"
    for col, ch in enumerate(files):
        x = int(col * square + square * 0.90)
        y = int(h - square * 0.08)
        bg = get_square_color(img, col, 7, square, rel_x=0.90, rel_y=0.75)
        draw.rectangle((x - 10, y - 25, x + 10, y + 4), fill=bg)
        text_color = GREEN_TEXT if col % 2 == 0 else WHITE_TEXT
        draw.text((x, y - 12), ch, fill=text_color, font=font, anchor="mm")

    for row in range(8):
        rank = str(row + 1) if flipped else str(8 - row)
        x = int(square * 0.08)
        y = int(row * square + square * 0.12)
        bg = get_square_color(img, 0, row, square, rel_x=0.20, rel_y=0.12)
        draw.rectangle((x - 10, y - 10, x + 10, y + 15), fill=bg)
        text_color = GREEN_TEXT if row % 2 != 0 else WHITE_TEXT
        draw.text((x, y), rank, fill=text_color, font=font, anchor="mm")

    return img


def lighten_board_green(img):
    img = img.convert("RGB")
    pixels = img.load()

    TARGET = (119, 150, 87)
    TOLERANCE = 15
    NEW_COLOR = (170, 195, 145)
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            if (
                abs(r - TARGET[0]) <= TOLERANCE
                and abs(g - TARGET[1]) <= TOLERANCE
                and abs(b - TARGET[2]) <= TOLERANCE
            ):
                pixels[x, y] = NEW_COLOR

    return img


HIGHLIGHT_TARGETS = (
    (247, 246, 130),
    (186, 201, 69),
    (210, 106, 82),
    (228, 166, 14),
    (251, 183, 42),
    (237, 124, 106),
    (253, 185, 26)
)
HIGHLIGHT_TOLERANCE = 10
HIGHLIGHT_MIN_RATIO = 0.08
HIGHLIGHT_MIN_PIXELS = 20
HIGHLIGHT_INNER_PAD_RATIO = 0.15


def is_highlight_color(r, g, b) -> bool:
    return any(
        abs(r - tr) <= HIGHLIGHT_TOLERANCE
        and abs(g - tg) <= HIGHLIGHT_TOLERANCE
        and abs(b - tb) <= HIGHLIGHT_TOLERANCE
        for tr, tg, tb in HIGHLIGHT_TARGETS
    )


def find_highlighted_squares(img, board_offset=0) -> list[tuple[int, int, int, int]]:
    """Return board squares that contain enough highlight pixels."""
    img = img.convert("RGB")
    pixels = img.load()
    w, h = img.size
    board_size = w - board_offset * 2
    square = board_size / 8
    squares = []

    for row in range(8):
        for col in range(8):
            x1 = int(board_offset + col * square)
            y1 = int(board_offset + row * square)
            x2 = int(board_offset + (col + 1) * square)
            y2 = int(board_offset + (row + 1) * square)

            pad_x = max(2, int((x2 - x1) * HIGHLIGHT_INNER_PAD_RATIO))
            pad_y = max(2, int((y2 - y1) * HIGHLIGHT_INNER_PAD_RATIO))
            inner_x1 = x1 + pad_x
            inner_y1 = y1 + pad_y
            inner_x2 = x2 - pad_x
            inner_y2 = y2 - pad_y
            if inner_x2 <= inner_x1 or inner_y2 <= inner_y1:
                continue

            total = 0
            count = 0
            for y in range(inner_y1, inner_y2):
                for x in range(inner_x1, inner_x2):
                    total += 1
                    if is_highlight_color(*pixels[x, y]):
                        count += 1

            threshold = max(HIGHLIGHT_MIN_PIXELS, int(total * HIGHLIGHT_MIN_RATIO))
            if count >= threshold:
                squares.append((x1, y1, x2, y2))

    return squares


def add_highlight_border(img, board_offset=0):
    img = img.convert("RGB")
    squares = find_highlighted_squares(img, board_offset)
    draw = ImageDraw.Draw(img)
    board_size = img.size[0] - board_offset * 2
    square = board_size / 8
    corner_len = int(square * 0.18)

    print("highlighted squares =", len(squares))
    for snapped_box in squares:
        draw_corner_box(
            draw,
            snapped_box,
            width=8,
            corner_len=corner_len,
            skip_top_left=has_checkmark(img, snapped_box, "top_left"),
            skip_top_right=has_checkmark(img, snapped_box, "top_right"),
            skip_bottom_left=has_checkmark(img, snapped_box, "bottom_left"),
            skip_bottom_right=has_checkmark(img, snapped_box, "bottom_right"),
        )

    return img


def resolve_targets(args: list[str]) -> tuple[Path, str | None]:
    chapters = sorted_chapters()
    if not chapters:
        raise SystemExit(f"No chapters found in {ROOT_DIR}")

    if not args:
        return chapters[-1], None

    if len(args) == 1:
        chapter = find_chapter(args[0])
        if chapter:
            return chapter, None
        return chapters[-1], args[0]

    chapter = find_chapter(args[0])
    if chapter is None:
        raise SystemExit(f"Chapter not found: {args[0]}")
    return chapter, args[1]


def select_crop_area(item_dirs: list[Path]) -> tuple[int, int, int, int]:
    sample_file = None
    for item_dir in item_dirs:
        files = list_images(item_dir / "raw")
        if files:
            sample_file = files[0]
            break

    if sample_file is None:
        raise SystemExit("No images found for crop selection")

    img = Image.open(sample_file)
    fig, ax = plt.subplots(figsize=(8, 10))
    ax.imshow(img)
    ax.set_title("Click TOP-LEFT then BOTTOM-RIGHT")
    points = plt.ginput(2, timeout=-1)
    plt.close()

    if len(points) != 2:
        raise SystemExit("Must select exactly 2 points")

    x1, y1 = map(int, points[0])
    x2, y2 = map(int, points[1])
    left, top = min(x1, x2), min(y1, y2)
    right, bottom = max(x1, x2), max(y1, y2)
    return left, top, right, bottom


def process_items(
    item_dirs: list[Path],
    crop_box: tuple[int, int, int, int],
    *,
    force_flipped: bool | None = None,
) -> int:
    left, top, right, bottom = crop_box
    total_images = 0

    for item_dir in item_dirs:
        print(f"Processing {item_dir.name}")
        raw_dir = item_dir / "raw"
        cropped_dir = item_dir / "cropped"
        cropped_dir.mkdir(parents=True, exist_ok=True)

        files = list_images(raw_dir)
        if not files:
            print("  Skip: no images")
            continue

        for idx, file in enumerate(files, start=1):
            with Image.open(file) as img:
                cropped = img.crop((left, top, right, bottom))
                flipped = detect_board_orientation(
                    cropped,
                    force_flipped=force_flipped,
                )
                print(file.name, "BLACK_BOTTOM" if flipped else "WHITE_BOTTOM")
                cropped = lighten_board_green(cropped)
                cropped = redraw_coordinates(cropped, flipped=flipped)
                cropped, board_offset = add_board_border(cropped)
                cropped = add_highlight_border(cropped, board_offset)
                cropped.save(cropped_dir / f"{idx:03d}.png")

        print(f"  Processed {len(files)} images")
        total_images += len(files)

    return total_images


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop and process chess board images")
    parser.add_argument("chapter", nargs="?", help="Chapter folder suffix or name")
    parser.add_argument("item", nargs="?", help="Item folder name, e.g. item001")
    parser.add_argument(
        "--select",
        action="store_true",
        help="Re-select crop area interactively",
    )
    orientation = parser.add_mutually_exclusive_group()
    orientation.add_argument(
        "--black-bottom",
        action="store_true",
        help="Skip OCR; treat board as black-on-bottom",
    )
    orientation.add_argument(
        "--white-bottom",
        action="store_true",
        help="Skip OCR; treat board as white-on-bottom",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all chapters and items",
    )
    args = parser.parse_args()

    if args.black_bottom:
        force_flipped = True
    elif args.white_bottom:
        force_flipped = False
    else:
        force_flipped = None

    if args.all:
        chapters = sorted_chapters()
        if not chapters:
            raise SystemExit(f"No chapters found in {ROOT_DIR}")
        
        item_dirs = []
        for chapter in chapters:
            item_dirs.extend(sorted_items(chapter))
        
        if not item_dirs:
            raise SystemExit("No items found")
        print(f"Using all chapters ({len(chapters)})")
    else:
        positional = [a for a in (args.chapter, args.item) if a]
        chapter_dir, item_name = resolve_targets(positional)
        print(f"Using chapter: {chapter_dir.name}")

        if item_name:
            item_dirs = [chapter_dir / item_name]
            if not item_dirs[0].exists():
                raise SystemExit(f"Item folder not found: {item_dirs[0]}")
        else:
            item_dirs = sorted_items(chapter_dir)
            if not item_dirs:
                raise SystemExit(f"No items found in {chapter_dir}")

    if CONFIG_FILE.exists() and not args.select:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        crop_box = (cfg["left"], cfg["top"], cfg["right"], cfg["bottom"])
    else:
        crop_box = select_crop_area(item_dirs)
        CONFIG_FILE.write_text(
            json.dumps(
                {
                    "left": crop_box[0],
                    "top": crop_box[1],
                    "right": crop_box[2],
                    "bottom": crop_box[3],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(
            f"Saved crop area: ({crop_box[0]}, {crop_box[1]}) -> "
            f"({crop_box[2]}, {crop_box[3]})"
        )

    total_images = process_items(item_dirs, crop_box, force_flipped=force_flipped)
    print()
    print(f"Done. Processed {total_images} images.")


if __name__ == "__main__":
    main()
