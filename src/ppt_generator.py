"""PPTX creation engine — unified grid system, consistent typography, polished layouts."""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn
from io import BytesIO

from src.templates import (
    THEMES, FONT_FAMILIES, SLIDE_WIDTH, SLIDE_HEIGHT,
)
from src.models import PPTRequest

# ============================================================================
# UNIFIED GRID SYSTEM (16:9 slide = 13.333" x 7.5")
# ============================================================================
G = {
    "left": Inches(0.9),
    "right_margin": Inches(0.5),
    "content_w": Inches(11.9),
    "top": Inches(1.25),
    "bottom": Inches(7.05),
    "accent_h": Inches(0.05),
    "bottom_bar_h": Inches(0.02),
    "num_x": Inches(12.4),
    "num_y": Inches(7.1),
}
# Chart zones
CHART_W = Inches(7.0)
CHART_INSIGHT_GAP = Inches(0.35)
INSIGHT_W = Inches(4.1)
INSIGHT_X = G["left"] + CHART_W + CHART_INSIGHT_GAP

# ============================================================================
# TYPOGRAPHY HIERARCHY
# ============================================================================
F = {
    "h1": Pt(40),       # Cover title
    "h1_sub": Pt(20),   # Cover subtitle
    "h2": Pt(28),       # Slide title
    "h3": Pt(15),       # Slide subtitle / description
    "body": Pt(16),     # Bullet text
    "body_sm": Pt(14),  # Sub-bullet
    "quote": Pt(26),    # Quote text
    "big_num": Pt(80),  # Datapoint number
    "light": Pt(22),    # Light slide text
    "caption": Pt(8),   # Page number / labels
}


# ============================================================================
# MAIN ENTRY
# ============================================================================
def create_pptx(slide_data: dict, request: PPTRequest) -> BytesIO:
    theme = THEMES[request.style.value]
    fonts = FONT_FAMILIES.get(request.language.value, FONT_FAMILIES["english"])

    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    slides = slide_data.get("slides", [])

    for i, slide_info in enumerate(slides):
        st = slide_info.get("type", "content")
        depth = slide_info.get("depth", "medium")

        # Dispatch
        if st == "title":
            _title(prs, slide_info, theme, fonts)
        elif st == "section":
            _section(prs, slide_info, theme, fonts)
        elif st == "chart":
            _chart(prs, slide_info, theme, fonts)
        elif st == "two_column":
            _two_col(prs, slide_info, theme, fonts)
        elif st == "quote":
            _quote(prs, slide_info, theme, fonts)
        elif st == "datapoint":
            _datapoint(prs, slide_info, theme, fonts)
        elif st == "agenda":
            _agenda(prs, slide_info, theme, fonts)
        elif depth == "light" or slide_info.get("content_style") == "narrative":
            _light(prs, slide_info, theme, fonts)
        elif depth == "deep":
            _content(prs, slide_info, theme, fonts, deep=True)
        else:
            _content(prs, slide_info, theme, fonts, deep=False)

        # Slide number (skip title)
        if i > 0:
            _page_num(prs.slides[-1], i, theme)

        # Speaker notes
        _notes(prs.slides[-1], slide_info)

        # Bottom bar on content-type slides
        if st in ("content", "agenda", "summary", "chart", "two_column", "datapoint"):
            _bottom_bar(prs.slides[-1], theme)

    buffer = BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer


# ============================================================================
# SLIDE LAYOUTS
# ============================================================================

def _title(prs, info, theme, fonts):
    """Cover slide — full-bleed color, centered title + subtitle, elegant lines."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    # Background
    _rect(slide, 0, 0, 13.333, 7.5, theme.title_slide_bg)

    # Top decorative line
    _rect(slide, 3.5, 2.6, 6.333, 0.015, theme.accent_bar_color)

    # Title
    tb = _tb(slide, 1.5, 2.85, 10.333, 1.6)
    p = tb.text_frame.paragraphs[0]
    p.text = info.get("title", "")
    p.alignment = PP_ALIGN.CENTER
    _font(p, fonts["title"], F["h1"], "FFFFFF", bold=True)

    # Subtitle
    sub = info.get("subtitle", "")
    if sub:
        tb2 = _tb(slide, 2.5, 4.65, 8.333, 0.7)
        p2 = tb2.text_frame.paragraphs[0]
        p2.text = sub
        p2.alignment = PP_ALIGN.CENTER
        _font(p2, fonts["body"], F["h1_sub"], "B0C4DE")

    # Bottom decorative line
    _rect(slide, 4.5, 5.55, 4.333, 0.015, theme.accent_bar_color)


def _content(prs, info, theme, fonts, deep=False):
    """Content slide — accent bar, title with rule, bullets, optional highlight card."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    if theme.background_color not in ("FFFFFF", "FFFAF5", "FFF8F0"):
        _rect(slide, 0, 0, 13.333, 7.5, theme.background_color)

    # Top accent bar
    _rect(slide, 0, 0, 13.333, G["accent_h"], theme.accent_bar_color)

    # Title
    tb = _tb(slide, G["left"], 0.35, G["content_w"], 0.65)
    p = tb.text_frame.paragraphs[0]
    p.text = info.get("title", "")
    _font(p, fonts["title"], F["h2"], theme.title_color, bold=True)

    # Thin rule under title
    _rect(slide, G["left"], 1.02, 3.0, 0.025, theme.accent_bar_color)

    # Subtitle
    sub = info.get("subtitle", "")
    bullet_top_val = 1.25
    if sub:
        tb2 = _tb(slide, G["left"], 1.12, G["content_w"], 0.35)
        p2 = tb2.text_frame.paragraphs[0]
        p2.text = sub
        _font(p2, fonts["body"], F["h3"], theme.secondary_color, italic=True)
        bullet_top_val = 1.55

    # Highlight — now as a bottom card instead of right-side box
    highlight = info.get("highlight", "")
    if highlight and deep:
        _highlight_card(slide, highlight, theme, fonts)
        bullet_h = 4.3
    else:
        bullet_h = 5.3

    # Bullets
    bullets = info.get("bullets", [])
    if bullets:
        tb3 = _tb(slide, G["left"] + Inches(0.1), Inches(bullet_top_val), G["content_w"] - Inches(0.3), Inches(bullet_h))
        tf = tb3.text_frame
        tf.word_wrap = True
        first = True
        for item in bullets:
            if isinstance(item, dict):
                text = item.get("text", "")
                subs = item.get("sub_bullets", [])
            else:
                text = str(item)
                subs = []

            p = tf.paragraphs[0] if first else tf.add_paragraph()
            p.text = text
            p.level = 0
            p.space_after = Pt(4)
            p.space_before = Pt(4)
            _font(p, fonts["body"], F["body"], theme.text_color)
            _bullet(p, "•", theme.accent_bar_color)
            first = False

            for s_text in subs:
                sp = tf.add_paragraph()
                sp.text = str(s_text)
                sp.level = 1
                sp.space_after = Pt(2)
                sp.space_before = Pt(2)
                _font(sp, fonts["body"], F["body_sm"], theme.secondary_color)
                _bullet(sp, "–", theme.secondary_color)


def _light(prs, info, theme, fonts):
    """Light/breather slide — large text, lots of whitespace, minimal decoration."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    if theme.background_color not in ("FFFFFF", "FFFAF5", "FFF8F0"):
        _rect(slide, 0, 0, 13.333, 7.5, theme.background_color)

    # Thin top bar
    _rect(slide, 0, 0, 13.333, G["accent_h"], theme.accent_bar_color)

    narrative = info.get("narrative", "")
    bullets = info.get("bullets", [])
    title = info.get("title", "")

    y_start = Inches(1.6)

    if narrative:
        tb = _tb(slide, Inches(1.8), y_start, Inches(9.733), Inches(3.5))
        tb.text_frame.word_wrap = True
        p = tb.text_frame.paragraphs[0]
        p.text = narrative
        p.alignment = PP_ALIGN.LEFT
        _font(p, fonts["body"], F["light"], theme.text_color)
    elif bullets:
        tb = _tb(slide, Inches(1.8), y_start, Inches(9.733), Inches(4.0))
        tb.text_frame.word_wrap = True
        for i, item in enumerate(bullets):
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            p = tb.text_frame.paragraphs[0] if i == 0 else tb.text_frame.add_paragraph()
            p.text = text
            p.space_after = Pt(14)
            p.space_before = Pt(6)
            _font(p, fonts["body"], F["light"], theme.text_color)
            _bullet(p, "•", theme.accent_bar_color)

    # Title at bottom as anchor
    if title:
        tb2 = _tb(slide, Inches(1.8), Inches(5.8), Inches(9.733), Inches(0.7))
        p2 = tb2.text_frame.paragraphs[0]
        p2.text = title
        _font(p2, fonts["title"], F["h2"], theme.title_color, bold=True)


def _chart(prs, info, theme, fonts):
    """Chart slide — 60% chart + 35% insight panel, with title."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    if theme.background_color not in ("FFFFFF", "FFFAF5", "FFF8F0"):
        _rect(slide, 0, 0, 13.333, 7.5, theme.background_color)

    _rect(slide, 0, 0, 13.333, G["accent_h"], theme.accent_bar_color)

    # Title + rule
    tb = _tb(slide, G["left"], 0.35, G["content_w"], 0.6)
    p = tb.text_frame.paragraphs[0]
    p.text = info.get("title", "")
    _font(p, fonts["title"], F["h2"], theme.title_color, bold=True)
    _rect(slide, G["left"], 0.98, 3.0, 0.025, theme.accent_bar_color)

    # Subtitle
    sub = info.get("subtitle", "")
    chart_y = Inches(1.2) if sub else Inches(1.15)
    if sub:
        tb2 = _tb(slide, G["left"], 1.1, G["content_w"], 0.3)
        p2 = tb2.text_frame.paragraphs[0]
        p2.text = sub
        _font(p2, fonts["body"], F["h3"], theme.secondary_color, italic=True)
        chart_y = Inches(1.5)

    # Chart
    chart_h = Inches(5.2)
    ct_str = info.get("chart_type", "column")
    xl_type = _CHART_MAP.get(ct_str, XL_CHART_TYPE.COLUMN_CLUSTERED)
    cats = info.get("categories", [])
    series_list = info.get("series", [])
    colors = _chart_colors(theme)

    cd = CategoryChartData()
    cd.categories = cats
    for idx, s in enumerate(series_list):
        cd.add_series(s.get("name", f"S{idx+1}"), s.get("values", []))

    chart_frame = slide.shapes.add_chart(xl_type, G["left"], chart_y, CHART_W, chart_h, cd)
    _style_chart(chart_frame.chart, theme, colors, ct_str)

    # Insight panel
    insight = info.get("insight", "")
    if insight:
        # Subtle background card
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            INSIGHT_X, Inches(2.4), INSIGHT_W, Inches(3.8),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = _hex(theme.primary_color)
        card.line.fill.background()

        # Label
        lb = _tb(slide, INSIGHT_X + Inches(0.35), Inches(2.6), INSIGHT_W - Inches(0.7), Inches(0.3))
        pl = lb.text_frame.paragraphs[0]
        pl.text = "KEY INSIGHT"
        _font(pl, fonts["body"], Pt(9), "B0C4DE", bold=True)

        # Insight text
        ib = _tb(slide, INSIGHT_X + Inches(0.35), Inches(3.0), INSIGHT_W - Inches(0.7), Inches(3.0))
        ib.text_frame.word_wrap = True
        pi = ib.text_frame.paragraphs[0]
        pi.text = insight
        _font(pi, fonts["body"], F["body_sm"], "FFFFFF")


def _two_col(prs, info, theme, fonts):
    """Two-column comparison — equal halves with center divider."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    if theme.background_color not in ("FFFFFF", "FFFAF5", "FFF8F0"):
        _rect(slide, 0, 0, 13.333, 7.5, theme.background_color)

    _rect(slide, 0, 0, 13.333, G["accent_h"], theme.accent_bar_color)

    # Title
    tb = _tb(slide, G["left"], 0.35, G["content_w"], 0.6)
    p = tb.text_frame.paragraphs[0]
    p.text = info.get("title", "")
    _font(p, fonts["title"], F["h2"], theme.title_color, bold=True)
    _rect(slide, G["left"], 0.98, 3.0, 0.025, theme.accent_bar_color)

    col_y = Inches(1.25)
    half_w = Inches(5.5)
    gap_c = Inches(6.65)

    # Left column
    left_items = info.get("left_bullets", [])
    if left_items:
        lb = _tb(slide, G["left"], col_y, half_w, Inches(5.2))
        _fill_col(lb, left_items, fonts, theme)

    # Center divider
    _rect(slide, gap_c, Inches(1.3), Inches(0.015), Inches(5.0), theme.accent_bar_color)

    # Right column
    right_items = info.get("right_bullets", [])
    if right_items:
        rb = _tb(slide, Inches(6.9), col_y, half_w, Inches(5.2))
        _fill_col(rb, right_items, fonts, theme)


def _quote(prs, info, theme, fonts):
    """Quote slide — large watermark quote mark, elegant text, attribution."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    _rect(slide, 0, 0, 13.333, 7.5, theme.primary_color)

    # Large watermark quote mark
    qb = _tb(slide, Inches(1.0), Inches(-0.5), Inches(3.0), Inches(3.0))
    pq = qb.text_frame.paragraphs[0]
    pq.text = "“"
    _font(pq, fonts["title"], Pt(120), "FFFFFF", bold=True)
    # Make semi-transparent (approximate with lighter color)
    pq.runs[0].font.color.rgb = _hex("FFFFFF")

    # Top & bottom decorative lines
    _rect(slide, Inches(2.0), Inches(1.7), Inches(9.333), Inches(0.01), theme.accent_bar_color)

    # Quote text
    tb = _tb(slide, Inches(2.0), Inches(2.0), Inches(9.333), Inches(3.2))
    tb.text_frame.word_wrap = True
    p = tb.text_frame.paragraphs[0]
    p.text = info.get("quote", "")
    p.alignment = PP_ALIGN.LEFT
    _font(p, fonts["title"], F["quote"], "FFFFFF", italic=True)

    # Attribution
    attr = info.get("attribution", "")
    if attr:
        _rect(slide, Inches(2.0), Inches(5.35), Inches(9.333), Inches(0.01), theme.accent_bar_color)
        ab = _tb(slide, Inches(2.0), Inches(5.55), Inches(9.333), Inches(0.5))
        pa = ab.text_frame.paragraphs[0]
        pa.text = f"— {attr}"
        pa.alignment = PP_ALIGN.RIGHT
        _font(pa, fonts["body"], F["body_sm"], "B0C4DE")


def _datapoint(prs, info, theme, fonts):
    """Big number/metric slide — striking number on left, context on right."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    if theme.background_color not in ("FFFFFF", "FFFAF5", "FFF8F0"):
        _rect(slide, 0, 0, 13.333, 7.5, theme.background_color)

    _rect(slide, 0, 0, 13.333, G["accent_h"], theme.accent_bar_color)

    # Big number
    big = info.get("big_number", "")
    if big:
        nb = _tb(slide, G["left"], Inches(1.0), Inches(5.5), Inches(2.2))
        pn = nb.text_frame.paragraphs[0]
        pn.text = big
        _font(pn, fonts["title"], F["big_num"], theme.accent_bar_color, bold=True)

    # Title
    title = info.get("title", "")
    if title:
        tb = _tb(slide, G["left"], Inches(3.2), Inches(5.5), Inches(0.7))
        pt = tb.text_frame.paragraphs[0]
        pt.text = title
        _font(pt, fonts["title"], F["h2"], theme.title_color, bold=True)

    # Description
    desc = info.get("description", "")
    if desc:
        db = _tb(slide, G["left"], Inches(3.95), Inches(5.8), Inches(2.2))
        db.text_frame.word_wrap = True
        pd = db.text_frame.paragraphs[0]
        pd.text = desc
        _font(pd, fonts["body"], F["body"], theme.text_color)

    # Right color block + context
    ctx = info.get("context", "")
    block = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(8.0), Inches(1.2), Inches(4.8), Inches(5.2),
    )
    block.fill.solid()
    block.fill.fore_color.rgb = _hex(theme.primary_color)
    block.line.fill.background()

    if ctx:
        cb = _tb(slide, Inches(8.4), Inches(1.5), Inches(4.0), Inches(4.6))
        cb.text_frame.word_wrap = True
        pc = cb.text_frame.paragraphs[0]
        pc.text = ctx
        _font(pc, fonts["body"], F["body_sm"], "FFFFFF")


def _agenda(prs, info, theme, fonts):
    """Agenda/overview — numbered items with clean spacing."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    if theme.background_color not in ("FFFFFF", "FFFAF5", "FFF8F0"):
        _rect(slide, 0, 0, 13.333, 7.5, theme.background_color)

    _rect(slide, 0, 0, 13.333, G["accent_h"], theme.accent_bar_color)

    # Title
    tb = _tb(slide, G["left"], 0.35, G["content_w"], 0.6)
    p = tb.text_frame.paragraphs[0]
    p.text = info.get("title", "Agenda")
    _font(p, fonts["title"], F["h2"], theme.title_color, bold=True)
    _rect(slide, G["left"], 0.98, 3.0, 0.025, theme.accent_bar_color)

    bullets = info.get("bullets", [])
    if not bullets:
        return

    ab = _tb(slide, G["left"] + Inches(0.2), Inches(1.4), Inches(10.5), Inches(5.0))
    ab.text_frame.word_wrap = True

    for i, item in enumerate(bullets):
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        p = ab.text_frame.paragraphs[0] if i == 0 else ab.text_frame.add_paragraph()

        # Number badge
        num = f"{i + 1:02d}"
        p.text = f"{num}    {text}"
        p.space_after = Pt(14)
        p.space_before = Pt(6)
        _font(p, fonts["body"], F["body"], theme.text_color)
        # Color the number
        if p.runs:
            p.runs[0].font.color.rgb = _hex(theme.accent_bar_color)
            p.runs[0].font.bold = True


def _section(prs, info, theme, fonts):
    """Section divider — full color background, large title, elegant lines."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    _rect(slide, 0, 0, 13.333, 7.5, theme.primary_color)

    # Top line
    _rect(slide, 5.0, 3.0, 3.333, 0.012, theme.accent_bar_color)

    # Title
    tb = _tb(slide, 2.0, 3.2, 9.333, 1.8)
    tb.text_frame.word_wrap = True
    p = tb.text_frame.paragraphs[0]
    p.text = info.get("title", "")
    p.alignment = PP_ALIGN.CENTER
    _font(p, fonts["title"], Pt(36), "FFFFFF", bold=True)

    # Bottom line
    _rect(slide, 5.0, 5.2, 3.333, 0.012, theme.accent_bar_color)


# ============================================================================
# HELPERS
# ============================================================================

def _highlight_card(slide, text, theme, fonts):
    """A subtle highlight card at the bottom of deep content slides."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        G["left"], Inches(5.8), G["content_w"], Inches(0.9),
    )
    card.fill.solid()
    card.fill.fore_color.rgb = _hex(theme.accent_bar_color)
    card.line.fill.background()

    hb = _tb(slide, G["left"] + Inches(0.3), Inches(5.9), G["content_w"] - Inches(0.6), Inches(0.7))
    hb.text_frame.word_wrap = True
    ph = hb.text_frame.paragraphs[0]
    ph.text = f"☆  {text}"  # ☆
    _font(ph, fonts["body"], F["body_sm"], theme.title_color, bold=True)


def _page_num(slide, num, theme):
    """Slide number at consistent bottom-right position."""
    nb = _tb(slide, G["num_x"], G["num_y"], Inches(0.8), Inches(0.25))
    p = nb.text_frame.paragraphs[0]
    p.text = str(num)
    p.alignment = PP_ALIGN.RIGHT
    _font(p, "Calibri", F["caption"], theme.secondary_color)


def _bottom_bar(slide, theme):
    """Subtle bottom decorative line."""
    _rect(slide, G["left"], G["bottom"], G["content_w"], G["bottom_bar_h"], theme.accent_bar_color)


def _notes(slide, info):
    """Speaker notes — with safe fallback."""
    txt = info.get("notes", "")
    if not txt:
        return
    try:
        if slide.has_notes_slide:
            slide.notes_slide.notes_text_frame.text = txt
    except Exception:
        pass  # Notes slide creation can fail in some edge cases


# ============================================================================
# CHART SUPPORT
# ============================================================================

_CHART_MAP = {
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "pie": XL_CHART_TYPE.PIE,
    "stacked_bar": XL_CHART_TYPE.BAR_STACKED,
    "area": XL_CHART_TYPE.AREA,
}


def _chart_colors(theme):
    return [_hex(theme.accent_bar_color), _hex(theme.primary_color),
            _hex(theme.secondary_color), _hex(theme.title_color)]


def _style_chart(chart, theme, colors, ct_str):
    chart.chart_style = 3

    for idx, series in enumerate(chart.series):
        color = colors[idx % len(colors)]
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = color
        if ct_str in ("line", "area"):
            series.format.line.color.rgb = color
            series.format.line.width = Pt(2.5)
        if ct_str in ("bar", "column", "stacked_bar"):
            try:
                chart.plots[0].gap_width = 80
            except Exception:
                pass

    # Data labels
    if ct_str in ("bar", "column", "stacked_bar", "pie"):
        try:
            plot = chart.plots[0]
            plot.has_data_labels = True
            plot.data_labels.font.size = Pt(8)
            plot.data_labels.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        except Exception:
            pass

    # Pie borders
    if ct_str == "pie":
        for idx, series in enumerate(chart.series):
            try:
                for pi in range(len(series.values)):
                    series.points(pi).format.line.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    series.points(pi).format.line.width = Pt(1.5)
            except Exception:
                pass

    # Legend
    if chart.has_legend:
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(9)
        try:
            from pptx.enum.chart import XL_LEGEND_POSITION
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        except ImportError:
            pass

    # Axes
    if ct_str != "pie":
        if chart.category_axis:
            chart.category_axis.tick_labels.font.size = Pt(8)
            chart.category_axis.tick_labels.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        if chart.value_axis:
            chart.value_axis.tick_labels.font.size = Pt(8)
            chart.value_axis.tick_labels.font.color.rgb = RGBColor(0x66, 0x66, 0x66)


def _fill_col(box, items, fonts, theme):
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.space_after = Pt(6)
        p.space_before = Pt(3)
        _font(p, fonts["body"], F["body"], theme.text_color)
        _bullet(p, "•", theme.accent_bar_color)


# ============================================================================
# ATOMIC HELPERS
# ============================================================================

def _rect(slide, x, y, w, h, color):
    """Add a filled rectangle (no border). Accepts hex string or RGBColor."""
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = color if isinstance(color, RGBColor) else _hex(color)
    s.line.fill.background()
    return s


def _tb(slide, x, y, w, h):
    """Add a text box."""
    return slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))


def _font(paragraph, font_name, size, color_hex, bold=False, italic=False):
    """Set font properties. Does NOT set font name to avoid missing-font warnings."""
    if not paragraph.runs:
        paragraph.add_run()
    r = paragraph.runs[0]
    r.font.size = size
    r.font.color.rgb = _hex(color_hex)
    r.font.bold = bold
    r.font.italic = italic


def _bullet(paragraph, char, color_hex):
    """Add a bullet character to a paragraph. Safe XML manipulation."""
    pPr = paragraph._p.get_or_add_pPr()
    # Remove only bullet-related children
    to_remove = []
    for child in pPr:
        if child.tag in [qn("a:buChar"), qn("a:buNone"), qn("a:buAutoNum")]:
            to_remove.append(child)
    for child in to_remove:
        pPr.remove(child)
    # Add new bullet character
    buChar = pPr.makeelement(qn("a:buChar"), {"char": char})
    pPr.append(buChar)


def _hex(h: str) -> RGBColor:
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


