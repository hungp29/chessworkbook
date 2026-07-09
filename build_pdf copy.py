import sys
from pathlib import Path

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    KeepTogether,
    Flowable,
)

from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

pdfmetrics.registerFont(
    TTFont(
        "NotoSans",
        "./fonts/NotoSans-Regular.ttf",
    )
)

pdfmetrics.registerFont(
    TTFont(
        "NotoSans-Bold",
        "./fonts/NotoSans-Bold.ttf",
    )
)

pdfmetrics.registerFont(
    TTFont(
        "NotoSans-Italic",
        "./fonts/NotoSans-Italic.ttf",
    )
)

pdfmetrics.registerFont(
    TTFont(
        "NotoSans-BoldItalic",
        "./fonts/NotoSans-BoldItalic.ttf",
    )
)

ROOT_DIR = Path("./img_root")
OUT_DIR = Path("./out")
OUT_DIR.mkdir(exist_ok=True)

# PAGE_WIDTH = 595
# PAGE_HEIGHT = 842
PAGE_WIDTH, PAGE_HEIGHT = A4

INNER_MARGIN = 60
OUTER_MARGIN = 20

TOP_MARGIN = 40
BOTTOM_MARGIN = 30

IMAGE_SIZE = 160
IMAGE_GAP = 10

USE_MIRROR_MARGIN = "--single-margin" not in sys.argv


# =====================================================
# DOCUMENT TEMPLATE
# =====================================================


class EndOfTOC(Flowable):

    def wrap(self, availWidth, availHeight):

        return (0, 0)

    def draw(self):

        pass


class ChessWorkbookDoc(BaseDocTemplate):

    toc_last_page = None
    content_start_page = 1

    def __init__(self, filename):

        super().__init__(
            filename,
            leftMargin=OUTER_MARGIN,
            rightMargin=OUTER_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
        )

        if USE_MIRROR_MARGIN:

            content_width = PAGE_WIDTH - INNER_MARGIN - OUTER_MARGIN

        else:

            content_width = PAGE_WIDTH - OUTER_MARGIN * 2

        content_height = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN

        #
        # TOC
        #

        if USE_MIRROR_MARGIN:

            toc_odd_frame = Frame(
                INNER_MARGIN,
                BOTTOM_MARGIN,
                content_width,
                content_height,
                id="toc_odd",
            )

            toc_even_frame = Frame(
                OUTER_MARGIN,
                BOTTOM_MARGIN,
                content_width,
                content_height,
                id="toc_even",
            )

        else:

            toc_odd_frame = Frame(
                OUTER_MARGIN,
                BOTTOM_MARGIN,
                content_width,
                content_height,
                id="toc_odd",
            )

            toc_even_frame = Frame(
                OUTER_MARGIN,
                BOTTOM_MARGIN,
                content_width,
                content_height,
                id="toc_even",
            )

        #
        # CONTENT
        #

        if USE_MIRROR_MARGIN:

            content_odd_frame = Frame(
                INNER_MARGIN,
                BOTTOM_MARGIN,
                content_width,
                content_height,
                id="content_odd",
            )

            content_even_frame = Frame(
                OUTER_MARGIN,
                BOTTOM_MARGIN,
                content_width,
                content_height,
                id="content_even",
            )

        else:

            content_odd_frame = Frame(
                OUTER_MARGIN,
                BOTTOM_MARGIN,
                content_width,
                content_height,
                id="content_odd",
            )

            content_even_frame = Frame(
                OUTER_MARGIN,
                BOTTOM_MARGIN,
                content_width,
                content_height,
                id="content_even",
            )

        toc_odd_template = PageTemplate(
            id="toc_odd",
            frames=[toc_odd_frame],
            onPage=self.draw_header_footer,
            autoNextPageTemplate="toc_even",
        )

        toc_even_template = PageTemplate(
            id="toc_even",
            frames=[toc_even_frame],
            onPage=self.draw_header_footer,
            autoNextPageTemplate="toc_odd",
        )

        content_odd_template = PageTemplate(
            id="content_odd",
            frames=[content_odd_frame],
            onPage=self.draw_header_footer,
            autoNextPageTemplate="content_even",
        )

        content_even_template = PageTemplate(
            id="content_even",
            frames=[content_even_frame],
            onPage=self.draw_header_footer,
            autoNextPageTemplate="content_odd",
        )

        self.addPageTemplates(
            [
                toc_odd_template,
                toc_even_template,
                content_odd_template,
                content_even_template,
            ]
        )

    def draw_header_footer(self, canvas, doc):

        canvas.saveState()

        canvas.setFont(
            "NotoSans",
            9,
        )

        page = canvas.getPageNumber()

        # print(f"page={page}, template={doc.pageTemplate.id}")

        display_page = page - self.content_start_page + 1

        canvas.drawString(
            PAGE_WIDTH / 2 - 40,
            20,
            "Mỡ Mỡ Chess Workbook",
        )

        #
        # Không đánh số TOC / blank page
        #

        if display_page >= 1:

            if not USE_MIRROR_MARGIN:

                canvas.drawRightString(
                    PAGE_WIDTH - OUTER_MARGIN,
                    20,
                    str(display_page),
                )

            else:

                if page % 2 == 1:

                    canvas.drawRightString(
                        PAGE_WIDTH - OUTER_MARGIN,
                        20,
                        str(display_page),
                    )

                else:

                    canvas.drawString(
                        OUTER_MARGIN,
                        20,
                        str(display_page),
                    )

        canvas.restoreState()

    def beforePage(self):

        current_template = getattr(
            self.pageTemplate,
            "id",
            "unknown",
        )

        # print(
        #     f"page={self.page}, current={current_template}, toc_last={self.toc_last_page}"
        # )

        if self.toc_last_page is not None and self.page > self.toc_last_page:
            if self.page % 2 == 0:

                self.handle_nextPageTemplate("content_odd")

            else:

                self.handle_nextPageTemplate("content_even")

    def afterFlowable(self, flowable):

        if isinstance(flowable, EndOfTOC):

            self.toc_last_page = self.page

            return

        if not isinstance(flowable, Paragraph):

            return

        style_name = flowable.style.name

        text = flowable.getPlainText()

        if style_name == "Chapter":

            key = "chapter_" + str(self.page) + "_" + text.replace(" ", "_")

            self.canv.bookmarkPage(key)

            display_page = self.page - self.content_start_page + 1

            if display_page < 1:

                display_page = 1

            self.notify(
                "TOCEntry",
                (
                    0,
                    text,
                    display_page,
                    key,
                ),
            )


# =====================================================
# DOC
# =====================================================

doc = ChessWorkbookDoc("Chess Workbook.pdf")

styles = getSampleStyleSheet()

chapter_style = ParagraphStyle(
    name="Chapter",
    parent=styles["Heading1"],
    fontName="NotoSans-Bold",
    fontSize=20,
    spaceAfter=0,
)

chapter_description_style = ParagraphStyle(
    name="ChapterDescription",
    parent=styles["BodyText"],
    fontName="NotoSans-Italic",
    fontSize=9,
    leading=12,
    textColor="#555555",
    spaceBefore=2,
    spaceAfter=8,
)

item_style = ParagraphStyle(
    name="Item",
    parent=styles["Heading3"],
    fontName="NotoSans",
    fontSize=10,
)

note_style = ParagraphStyle(
    name="Note",
    parent=styles["BodyText"],
    fontName="NotoSans-Italic",
    fontSize=9,
    textColor="#555555",
    leading=11,
    spaceBefore=4,
    spaceAfter=0,
)

toc_style = ParagraphStyle(
    name="TOCChapter",
    fontName="NotoSans",
    fontSize=12,
    leftIndent=20,
    firstLineIndent=-10,
    spaceBefore=4,
    leading=14,
)


toc_title_style = ParagraphStyle(
    name="TOCTitle",
    parent=styles["Title"],
    fontName="NotoSans-Bold",
)

image_number_style = ParagraphStyle(
    name="ImageNumber",
    parent=styles["BodyText"],
    alignment=1,  # center
    fontName="NotoSans",
    fontSize=9,
    leading=10,
    spaceBefore=0,
    spaceAfter=0,
)


def build_story(insert_blank_after_toc=False):
    from reportlab.platypus import NextPageTemplate

    story = []

    # =====================================================
    # COVER TOC
    # =====================================================

    # story.append(NextPageTemplate("toc_odd"))

    story.append(
        Paragraph(
            "Mục lục",
            toc_title_style,
        )
    )

    story.append(Spacer(1, 20))

    toc = TableOfContents()

    toc.levelStyles = [toc_style]

    story.append(toc)

    story.append(EndOfTOC())

    if insert_blank_after_toc:

        story.append(PageBreak())

        story.append(NextPageTemplate("content_odd"))

        story.append(PageBreak())

    else:

        story.append(NextPageTemplate("content_odd"))

    # =====================================================
    # CHAPTERS
    # =====================================================

    chapters = sorted(p for p in ROOT_DIR.iterdir() if p.is_dir())

    for chapter_index, chapter in enumerate(chapters):

        group_file = chapter / "group.txt"

        chapter_name = (
            group_file.read_text(encoding="utf-8").strip()
            if group_file.exists()
            else chapter.name
        )

        description_file = chapter / "description.txt"

        chapter_description = (
            description_file.read_text(encoding="utf-8").strip()
            if description_file.exists()
            else ""
        )

        # -----------------------------
        # CHAPTER HEADER
        # -----------------------------

        story.append(Paragraph(chapter_name, chapter_style))

        if chapter_description:

            story.append(
                Paragraph(
                    chapter_description,
                    chapter_description_style,
                )
            )

        story.append(Spacer(1, 10))

        items = sorted(
            p for p in chapter.iterdir() if p.is_dir() and p.name.startswith("item")
        )

        # -----------------------------
        # ITEMS
        # -----------------------------

        for item_index, item in enumerate(items, start=1):

            title_file = item / "title.txt"

            title = (
                title_file.read_text(encoding="utf-8").strip()
                if title_file.exists()
                else item.name
            )

            note_file = item / "note.txt"

            note = (
                note_file.read_text(encoding="utf-8").strip()
                if note_file.exists()
                else ""
            )

            images = sorted((item / "cropped").glob("*.png"))

            block = []

            block.append(Paragraph(f"{item_index}. {title}", item_style))

            block.append(Spacer(1, 6))

            rows = []

            current_images = []

            current_labels = []

            for image_index, image_file in enumerate(images, start=1):

                current_images.append(
                    Image(str(image_file), width=IMAGE_SIZE, height=IMAGE_SIZE)
                )

                current_labels.append(Paragraph(f"{image_index}", image_number_style))

                if len(current_images) == 3:

                    rows.append(current_images)

                    rows.append(current_labels)

                    current_images = []

                    current_labels = []

            if current_images:

                while len(current_images) < 3:

                    current_images.append("")

                    current_labels.append("")

                rows.append(current_images)

                rows.append(current_labels)

            if rows:

                table = Table(
                    rows,
                    colWidths=[
                        IMAGE_SIZE + IMAGE_GAP,
                        IMAGE_SIZE + IMAGE_GAP,
                        IMAGE_SIZE + IMAGE_GAP,
                    ],
                )

                table.setStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        # Hàng ảnh
                        ("TOPPADDING", (0, 0), (-1, 0), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
                        # Hàng số
                        ("TOPPADDING", (0, 1), (-1, 1), 2),
                        ("BOTTOMPADDING", (0, 1), (-1, 1), 2),
                    ]
                )
                # table.canSplit = False

                block.append(table)

                if note:

                    block.append(Spacer(1, 4))

                    block.append(
                        Paragraph(
                            note,
                            note_style,
                        )
                    )

            block.append(Spacer(1, 12))

            # story.append(KeepTogether(block))
            story.extend(block)

        # chapter mới bắt đầu trang mới

        if chapter_index < len(chapters) - 1:

            story.append(PageBreak())
    return story


# =====================================================

# PASS 1

# =====================================================

temp_pdf = OUT_DIR / "_temp.pdf"

temp_doc = ChessWorkbookDoc(str(temp_pdf))

temp_story = build_story()

temp_doc.multiBuild(temp_story)

toc_last_page = temp_doc.toc_last_page

print("TOC ends at page", toc_last_page)

# =====================================================

# DECIDE BLANK PAGE

# =====================================================

insert_blank = toc_last_page % 2 == 1
content_start_page = toc_last_page + 1

if insert_blank:

    content_start_page += 1

# =====================================================

# PASS 2

# =====================================================

final_pdf = OUT_DIR / "Chess Workbook.pdf"

final_doc = ChessWorkbookDoc(str(final_pdf))
final_doc.content_start_page = content_start_page

final_story = build_story(insert_blank_after_toc=insert_blank)

final_doc.multiBuild(final_story)

# =====================================================

# CLEANUP

# =====================================================

if temp_pdf.exists():

    temp_pdf.unlink()

print(f"Created: {final_pdf}")
