import argparse
import logging
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
)
from reportlab.platypus.tableofcontents import TableOfContents

from workbook_io import (
    OUT_DIR,
    FONTS_DIR,
    ROOT_DIR,
    chapter_description,
    chapter_display_name,
    item_note,
    item_title,
    sorted_chapters,
    sorted_items,
)

PAGE_WIDTH, PAGE_HEIGHT = A4

INNER_MARGIN = 60
OUTER_MARGIN = 20
TOP_MARGIN = 40
BOTTOM_MARGIN = 30
IMAGE_SIZE = 160
IMAGE_GAP = 10


def register_fonts() -> None:
    for name, filename in (
        ("NotoSans", "NotoSans-Regular.ttf"),
        ("NotoSans-Bold", "NotoSans-Bold.ttf"),
        ("NotoSans-Italic", "NotoSans-Italic.ttf"),
        ("NotoSans-BoldItalic", "NotoSans-BoldItalic.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(FONTS_DIR / filename)))


def para(text: str, style) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


class EndOfTOC(Flowable):
    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        pass


class ChessWorkbookDoc(BaseDocTemplate):
    toc_last_page = None
    content_start_page = 1
    current_chapter = ""

    def __init__(self, filename, *, use_mirror_margin: bool = True):
        self.use_mirror_margin = use_mirror_margin

        super().__init__(
            filename,
            leftMargin=OUTER_MARGIN,
            rightMargin=OUTER_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
        )

        self.chapter_start_pages = set()
        self.page_chapters = {}

        content_width = PAGE_WIDTH - INNER_MARGIN - OUTER_MARGIN
        content_height = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN

        if use_mirror_margin:
            toc_odd_x = INNER_MARGIN
            toc_even_x = OUTER_MARGIN
            content_odd_x = INNER_MARGIN
            content_even_x = OUTER_MARGIN
        else:
            centered_x = (INNER_MARGIN + OUTER_MARGIN) / 2
            toc_odd_x = toc_even_x = content_odd_x = content_even_x = centered_x

        toc_odd_frame = Frame(
            toc_odd_x, BOTTOM_MARGIN, content_width, content_height, id="toc_odd"
        )
        toc_even_frame = Frame(
            toc_even_x, BOTTOM_MARGIN, content_width, content_height, id="toc_even"
        )
        content_odd_frame = Frame(
            content_odd_x, BOTTOM_MARGIN, content_width, content_height, id="content_odd"
        )
        content_even_frame = Frame(
            content_even_x,
            BOTTOM_MARGIN,
            content_width,
            content_height,
            id="content_even",
        )

        self.addPageTemplates(
            [
                PageTemplate(
                    id="toc_odd",
                    frames=[toc_odd_frame],
                    onPage=self.draw_header_footer,
                    autoNextPageTemplate="toc_even",
                ),
                PageTemplate(
                    id="toc_even",
                    frames=[toc_even_frame],
                    onPage=self.draw_header_footer,
                    autoNextPageTemplate="toc_odd",
                ),
                PageTemplate(
                    id="content_odd",
                    frames=[content_odd_frame],
                    onPage=self.draw_header_footer,
                    autoNextPageTemplate="content_even",
                ),
                PageTemplate(
                    id="content_even",
                    frames=[content_even_frame],
                    onPage=self.draw_header_footer,
                    autoNextPageTemplate="content_odd",
                ),
            ]
        )

    def chapter_for_page(self, page: int) -> str | None:
        if not self.chapter_start_pages:
            return None
        eligible = [p for p in self.chapter_start_pages if p <= page]
        if not eligible:
            return None
        return self.page_chapters.get(max(eligible))

    def draw_header_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("NotoSans", 9)

        page = canvas.getPageNumber()
        display_page = page - self.content_start_page + 1
        chapter_name = self.chapter_for_page(page)

        logging.debug(
            "HEADER page=%s chapter=%s start=%s",
            page,
            chapter_name,
            page in self.chapter_start_pages,
        )

        if display_page >= 1 and chapter_name and page not in self.chapter_start_pages:
            canvas.drawCentredString(
                PAGE_WIDTH / 2,
                PAGE_HEIGHT - 20,
                chapter_name,
            )

        canvas.drawString(PAGE_WIDTH / 2 - 40, 20, "Mỡ Mỡ Chess Workbook")

        if display_page >= 1:
            if not self.use_mirror_margin:
                canvas.drawRightString(
                    PAGE_WIDTH - OUTER_MARGIN, 20, str(display_page)
                )
            elif page % 2 == 1:
                canvas.drawRightString(
                    PAGE_WIDTH - OUTER_MARGIN, 20, str(display_page)
                )
            else:
                canvas.drawString(OUTER_MARGIN, 20, str(display_page))

        canvas.restoreState()

    def beforePage(self):
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
        logging.debug(
            "page=%s style=%s text=%s",
            self.page,
            style_name,
            text[:80],
        )

        if style_name != "Chapter":
            return

        self.current_chapter = text
        logging.debug("CHAPTER page=%s text=%s", self.page, text)

        header_text = text.split(". ", 1)[1] if ". " in text else text
        self.chapter_start_pages.add(self.page)
        self.page_chapters[self.page] = header_text

        key = "chapter_" + str(self.page) + "_" + text.replace(" ", "_")
        self.canv.bookmarkPage(key)

        display_page = self.page - self.content_start_page + 1
        if display_page < 1:
            display_page = 1

        self.notify("TOCEntry", (0, text, display_page, key))


def create_styles():
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
        spaceBefore=0,
        spaceAfter=0,
    )
    summary_style = ParagraphStyle(
        name="Summary",
        parent=styles["BodyText"],
        fontName="NotoSans-Italic",
        fontSize=9,
        textColor="#555555",
        leading=14,
        spaceBefore=0,
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
        alignment=1,
        fontName="NotoSans",
        fontSize=7,
        leading=10,
        spaceBefore=0,
        spaceAfter=0,
    )

    return {
        "chapter": chapter_style,
        "chapter_description": chapter_description_style,
        "item": item_style,
        "summary": summary_style,
        "toc": toc_style,
        "toc_title": toc_title_style,
        "image_number": image_number_style,
    }


def build_story(styles, *, insert_blank_after_toc: bool = False):
    from reportlab.platypus import NextPageTemplate

    story = [para("Mục lục", styles["toc_title"]), Spacer(1, 20)]

    toc = TableOfContents()
    toc.levelStyles = [styles["toc"]]
    story.extend([toc, EndOfTOC()])

    if insert_blank_after_toc:
        story.extend([PageBreak(), NextPageTemplate("content_odd"), PageBreak()])
    else:
        story.append(NextPageTemplate("content_odd"))

    chapters = sorted_chapters()
    if not chapters:
        logging.warning("No chapters found in %s", ROOT_DIR)

    for chapter_index, chapter in enumerate(chapters):
        chapter_name = chapter_display_name(chapter)
        description = chapter_description(chapter)

        story.append(
            para(f"{chapter_index + 1}. {chapter_name}", styles["chapter"])
        )

        if description:
            story.append(para(description, styles["chapter_description"]))

        story.append(Spacer(1, 10))

        for item_index, item in enumerate(sorted_items(chapter), start=1):
            title = item_title(item)
            note = item_note(item)
            images = sorted((item / "cropped").glob("*.png"))

            block = [
                para(
                    f"{chapter_index + 1}.{item_index}. {title}",
                    styles["item"],
                ),
                Spacer(1, 6),
            ]

            rows = []
            current_images = []
            current_labels = []

            for image_index, image_file in enumerate(images, start=1):
                current_images.append(
                    Image(str(image_file), width=IMAGE_SIZE, height=IMAGE_SIZE)
                )
                current_labels.append(
                    Paragraph(str(image_index), styles["image_number"])
                )

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
                    colWidths=[IMAGE_SIZE + IMAGE_GAP] * 3,
                )
                table.setStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, 0), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
                        ("TOPPADDING", (0, 1), (-1, 1), 2),
                        ("BOTTOMPADDING", (0, 1), (-1, 1), 2),
                    ]
                )
                block.append(table)

                if note:
                    summary = Table(
                        [[para(note, styles["summary"])]],
                        colWidths=["100%"],
                    )
                    summary.setStyle(
                        [
                            ("LINEBEFORE", (0, 0), (0, -1), 1, colors.grey),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 1),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                        ]
                    )
                    block.append(summary)

            block.append(Spacer(1, 12))
            story.extend(block)

        if chapter_index < len(chapters) - 1:
            story.append(PageBreak())

    return story


def probe_toc_last_page(styles, *, use_mirror_margin: bool) -> int:
    """Build TOC only to learn how many pages it occupies."""
    chapters = sorted_chapters()
    probe_pdf = OUT_DIR / "_toc_probe.pdf"

    doc = ChessWorkbookDoc(str(probe_pdf), use_mirror_margin=use_mirror_margin)

    toc = TableOfContents()
    toc.levelStyles = [styles["toc"]]
    for index, chapter in enumerate(chapters, start=1):
        toc.addEntry(
            0,
            f"{index}. {chapter_display_name(chapter)}",
            1,
            f"probe_{index}",
        )

    story = [
        para("Mục lục", styles["toc_title"]),
        Spacer(1, 20),
        toc,
        EndOfTOC(),
    ]
    doc.multiBuild(story)

    toc_last_page = doc.toc_last_page
    if probe_pdf.exists():
        probe_pdf.unlink()

    if toc_last_page is None:
        raise RuntimeError("Could not determine TOC length")

    logging.debug("toc_last_page=%s (probe)", toc_last_page)
    return toc_last_page


def build_pdf(*, use_mirror_margin: bool = True) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    styles = create_styles()

    toc_last_page = probe_toc_last_page(styles, use_mirror_margin=use_mirror_margin)
    insert_blank = toc_last_page % 2 == 1
    content_start_page = toc_last_page + 1 + (1 if insert_blank else 0)

    logging.debug(
        "insert_blank=%s content_start_page=%s",
        insert_blank,
        content_start_page,
    )

    final_pdf = OUT_DIR / "Chess Workbook.pdf"
    doc = ChessWorkbookDoc(str(final_pdf), use_mirror_margin=use_mirror_margin)
    doc.content_start_page = content_start_page
    doc.multiBuild(build_story(styles, insert_blank_after_toc=insert_blank))

    return final_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Build chess workbook PDF")
    parser.add_argument(
        "--single-margin",
        action="store_true",
        help="Use centered margins instead of mirror margins",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print debug information while building",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    if not ROOT_DIR.is_dir():
        raise SystemExit(f"Chapter directory not found: {ROOT_DIR}")

    register_fonts()
    final_pdf = build_pdf(use_mirror_margin=not args.single_margin)
    print(f"Created: {final_pdf}")


if __name__ == "__main__":
    main()
