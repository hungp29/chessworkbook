import sys
import json
from pathlib import Path

from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
)
import matplotlib.pyplot as plt

import pytesseract

ROOT_DIR = Path("./img_root")
CONFIG_FILE = Path("crop_config.json")


def detect_board_orientation(img):

    img = img.convert("RGB")

    w, h = img.size

    square = w / 8

    #

    # góc trái trên nơi chứa số 1 hoặc 8

    #

    region = img.crop(
        (
            0,
            0,
            int(square * 0.35),
            int(square * 0.35),
        )
    )

    #

    # tăng tương phản cho OCR

    #

    gray = region.convert("L")

    gray = ImageEnhance.Contrast(gray).enhance(4)

    text = pytesseract.image_to_string(
        gray,
        config="--psm 10 -c tessedit_char_whitelist=12345678",
    )

    text = text.strip()

    if text == "1":

        return True  # black ở dưới

    if text == "8":

        return False  # white ở dưới

    print(f"WARNING: cannot detect orientation, OCR result='{text}'")

    return False


def has_checkmark(img, box, corner):

    pixels = img.load()

    x1, y1, x2, y2 = box

    TARGET = (126, 183, 78)
    TOLERANCE = 15

    #
    # vùng scan cho từng góc
    #

    if corner == "top_left":

        scan_x1 = x1
        scan_y1 = y1

        scan_x2 = int(x1 + (x2 - x1) * 0.30)
        scan_y2 = int(y1 + (y2 - y1) * 0.35)

    elif corner == "top_right":

        scan_x1 = int(x1 + (x2 - x1) * 0.70)
        scan_y1 = y1

        scan_x2 = x2
        scan_y2 = int(y1 + (y2 - y1) * 0.35)

    elif corner == "bottom_left":

        scan_x1 = x1
        scan_y1 = int(y1 + (y2 - y1) * 0.65)

        scan_x2 = int(x1 + (x2 - x1) * 0.30)
        scan_y2 = y2

    elif corner == "bottom_right":

        scan_x1 = int(x1 + (x2 - x1) * 0.70)
        scan_y1 = int(y1 + (y2 - y1) * 0.65)

        scan_x2 = x2
        scan_y2 = y2

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

    #

    # góc trên trái

    #

    if not skip_top_left:

        draw.line(
            (x1, y1, x1 + corner_len, y1),
            fill="black",
            width=width,
        )

        draw.line(
            (x1, y1, x1, y1 + corner_len),
            fill="black",
            width=width,
        )

    #

    # góc trên phải

    #

    if not skip_top_right:

        draw.line(
            (x2 - corner_len, y1, x2, y1),
            fill="black",
            width=width,
        )

        draw.line(
            (x2, y1, x2, y1 + corner_len),
            fill="black",
            width=width,
        )

    #

    # góc dưới trái

    #

    if not skip_bottom_left:

        draw.line(
            (x1, y2, x1 + corner_len, y2),
            fill="black",
            width=width,
        )

        draw.line(
            (x1, y2 - corner_len, x1, y2),
            fill="black",
            width=width,
        )

    #

    # góc dưới phải

    #

    if not skip_bottom_right:

        draw.line(
            (x2 - corner_len, y2, x2, y2),
            fill="black",
            width=width,
        )

        draw.line(
            (x2, y2 - corner_len, x2, y2),
            fill="black",
            width=width,
        )


def get_square_color(
    img,
    col,
    row,
    square,
    rel_x=0.5,
    rel_y=0.5,
):

    sample_x = int(col * square + square * rel_x)

    sample_y = int(row * square + square * rel_y)

    return img.getpixel((sample_x, sample_y))


def redraw_coordinates(
    img,
    flipped=False,
):

    img = img.convert("RGB")

    draw = ImageDraw.Draw(img)

    w, h = img.size

    square = w / 8

    try:

        font = ImageFont.truetype(
            "./fonts/NotoSans-Bold.ttf",
            int(square * 0.25),
        )

    except:

        font = ImageFont.load_default()

    # WHITE_TEXT = (169, 194, 145)

    # GREEN_TEXT = (237, 237, 210)
    WHITE_TEXT = (84, 82, 81)
    GREEN_TEXT = (248, 248, 248)

    GREEN_BG = (169, 194, 145)
    WHITE_BG = (237, 237, 210)

    #
    # a-h
    #

    files = "hgfedcba" if flipped else "abcdefgh"

    for col, ch in enumerate(files):

        x = int(col * square + square * 0.90)

        y = int(h - square * 0.08)

        # bg = GREEN_BG if col % 2 == 0 else WHITE_BG

        bg = get_square_color(
            img,
            col,
            7,
            square,
            rel_x=0.90,  # gần vị trí chữ
            rel_y=0.75,  # phía trên chữ một chút
        )

        draw.rectangle(
            (
                x - 10,
                y - 25,
                x + 10,
                y + 4,
            ),
            fill=bg,
        )

        text_color = GREEN_TEXT if col % 2 == 0 else WHITE_TEXT

        draw.text(
            (x, y - 12),
            ch,
            fill=text_color,
            font=font,
            anchor="mm",
        )

    #
    # 1-8
    #

    for row in range(8):

        rank = str(row + 1) if flipped else str(8 - row)

        x = int(square * 0.08)

        y = int(row * square + square * 0.12)

        # bg = WHITE_BG if row % 2 == 0 else GREEN_BG
        bg = get_square_color(
            img,
            0,
            row,
            square,
            rel_x=0.20,  # bên phải số một chút
            rel_y=0.12,
        )

        draw.rectangle(
            (
                x - 10,
                y - 10,
                x + 10,
                y + 15,
            ),
            fill=bg,
        )

        text_color = GREEN_TEXT if row % 2 != 0 else WHITE_TEXT

        draw.text(
            (x, y),
            rank,
            fill=text_color,
            font=font,
            anchor="mm",
        )

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


def add_highlight_border(img):

    img = img.convert("RGB")

    TARGETS = [
        (247, 246, 130),  # vàng
        (186, 201, 69),  # xanh
    ]
    TOLERANCE = 10

    def is_highlight_color(r, g, b):

        for tr, tg, tb in TARGETS:

            if (
                abs(r - tr) <= TOLERANCE
                and abs(g - tg) <= TOLERANCE
                and abs(b - tb) <= TOLERANCE
            ):

                return True

        return False

    w, h = img.size
    pixels = img.load()

    visited = set()
    boxes = []

    for y in range(h):
        for x in range(w):

            if (x, y) in visited:
                continue

            r, g, b = pixels[x, y]

            if is_highlight_color(r, g, b):

                stack = [(x, y)]
                visited.add((x, y))

                min_x = max_x = x
                min_y = max_y = y

                while stack:

                    cx, cy = stack.pop()

                    min_x = min(min_x, cx)
                    max_x = max(max_x, cx)

                    min_y = min(min_y, cy)
                    max_y = max(max_y, cy)

                    for nx, ny in (
                        (cx - 1, cy),
                        (cx + 1, cy),
                        (cx, cy - 1),
                        (cx, cy + 1),
                    ):

                        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:

                            nr, ng, nb = pixels[nx, ny]

                            if is_highlight_color(nr, ng, nb):

                                visited.add((nx, ny))
                                stack.append((nx, ny))

                boxes.append((min_x, min_y, max_x, max_y))

    draw = ImageDraw.Draw(img)

    square = w / 8

    for box in boxes:

        if (box[2] - box[0]) < 10:

            continue

        if (box[3] - box[1]) < 10:

            continue

        #
        # snap về đúng ô cờ
        #

        center_x = (box[0] + box[2]) / 2

        center_y = (box[1] + box[3]) / 2

        col = int(center_x // square)

        row = int(center_y // square)

        x1 = int(col * square)

        y1 = int(row * square)

        x2 = int(x1 + square)

        y2 = int(y1 + square)

        snapped_box = (x1, y1, x2, y2)

        corner_len = int(square * 0.18)

        skip_top_left = has_checkmark(
            img,
            snapped_box,
            "top_left",
        )

        skip_top_right = has_checkmark(
            img,
            snapped_box,
            "top_right",
        )

        skip_bottom_left = has_checkmark(
            img,
            snapped_box,
            "bottom_left",
        )

        skip_bottom_right = has_checkmark(
            img,
            snapped_box,
            "bottom_right",
        )

        draw_corner_box(
            draw,
            snapped_box,
            width=8,
            corner_len=corner_len,
            skip_top_left=skip_top_left,
            skip_top_right=skip_top_right,
            skip_bottom_left=skip_bottom_left,
            skip_bottom_right=skip_bottom_right,
        )

    return img


# =====================================================

# ARGS

# =====================================================

force_select = "--select" in sys.argv

args = [a for a in sys.argv[1:] if not a.startswith("--")]

chapter_name = None

item_name = None

chapters = sorted(
    [p for p in ROOT_DIR.iterdir() if p.is_dir()],
    key=lambda p: p.name,
)

if not chapters:

    raise Exception("No chapters found")

if len(args) == 0:

    # crop chapter cuối cùng

    chapter_dir = chapters[-1]

elif len(args) == 1:

    matches = [
        p for p in ROOT_DIR.iterdir() if p.is_dir() and p.name.endswith(f"_{args[0]}")
    ]

    if matches:

        chapter_dir = matches[0]

    else:

        chapter_dir = chapters[-1]

        item_name = args[0]

else:

    chapter_name = args[0]

    item_name = args[1]

    matches = [
        p
        for p in ROOT_DIR.iterdir()
        if p.is_dir() and p.name.endswith(f"_{chapter_name}")
    ]

    if not matches:

        raise Exception(f"Chapter not found: {chapter_name}")

    if len(matches) > 1:

        raise Exception(f"Multiple chapters match: {chapter_name}")

    chapter_dir = matches[0]

print(f"Using chapter: {chapter_dir.name}")

# =====================================================
# FIND ITEMS
# =====================================================

if item_name:

    item_dirs = [chapter_dir / item_name]

    if not item_dirs[0].exists():

        raise Exception(f"Item folder not found: {item_dirs[0]}")

else:

    item_dirs = sorted(
        p for p in chapter_dir.iterdir() if p.is_dir() and p.name.startswith("item")
    )

    if not item_dirs:

        raise Exception(f"No items found in {chapter_dir}")

# =====================================================
# LOAD / SELECT CROP AREA
# =====================================================

if CONFIG_FILE.exists() and not force_select:

    cfg = json.loads(CONFIG_FILE.read_text())

    left = cfg["left"]
    top = cfg["top"]
    right = cfg["right"]
    bottom = cfg["bottom"]

else:

    sample_file = None

    for item_dir in item_dirs:

        raw_dir = item_dir / "raw"

        files = sorted(
            [
                p
                for p in raw_dir.iterdir()
                if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
            ]
        )

        if files:
            sample_file = files[0]
            break

    if sample_file is None:
        raise Exception("No images found")

    img = Image.open(sample_file)

    fig, ax = plt.subplots(figsize=(8, 10))

    ax.imshow(img)

    ax.set_title("Click TOP-LEFT then BOTTOM-RIGHT")

    points = plt.ginput(2, timeout=-1)

    plt.close()

    if len(points) != 2:

        raise Exception("Must select exactly 2 points")

    x1, y1 = map(int, points[0])

    x2, y2 = map(int, points[1])

    left = min(x1, x2)
    top = min(y1, y2)

    right = max(x1, x2)
    bottom = max(y1, y2)

    CONFIG_FILE.write_text(
        json.dumps(
            {
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
            },
            indent=2,
        )
    )

    print(f"Saved crop area: " f"({left}, {top}) -> ({right}, {bottom})")

# =====================================================
# PROCESS ITEMS
# =====================================================

total_images = 0

for item_dir in item_dirs:

    print(f"Processing {item_dir.name}")

    raw_dir = item_dir / "raw"

    cropped_dir = item_dir / "cropped"

    cropped_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        [
            p
            for p in raw_dir.iterdir()
            if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
        ]
    )

    if not files:

        print(f"  Skip: no images")

        continue

    for idx, file in enumerate(files, start=1):

        with Image.open(file) as img:

            cropped = img.crop(
                (
                    left,
                    top,
                    right,
                    bottom,
                )
            )

            flipped = detect_board_orientation(cropped)

            print(
                file.name,
                "BLACK_BOTTOM" if flipped else "WHITE_BOTTOM",
            )

            cropped = lighten_board_green(cropped)

            cropped = redraw_coordinates(cropped, flipped=flipped)

            cropped = add_highlight_border(cropped)

            # cropped = ImageEnhance.Contrast(cropped).enhance(1.5)

            # cropped = cropped.filter(
            #     ImageFilter.UnsharpMask(
            #         radius=1,
            #         percent=120,
            #         threshold=3,
            #     )
            # )

            # cropped.save(
            #     cropped_dir / f"{idx:03d}.jpg",
            #     quality=95,
            # )
            cropped.save(cropped_dir / f"{idx:03d}.png")

    print(f"  Processed {len(files)} images")

    total_images += len(files)

print()
print(f"Done. Processed {total_images} images.")
