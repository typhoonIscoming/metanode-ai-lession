"""
build_lessonN_slides.py —— 课件 PPTX 构建脚手架。

用法：
    1. cp 本文件到 /tmp/build_lessonN_slides.py
    2. 修改下方 OUT、TITLE、SUBTITLE、PALETTE 三处
    3. 仿照 build() 函数里的样例 slide 结构，按 README 章节扩展更多页
    4. python /tmp/build_lessonN_slides.py

设计约定：
    - 16:9 13.333 × 7.5 英寸
    - 总页数 ≈ 28：封面 1 + 议程 1 + 每个主题 4-6 页 + 收束 1
    - 字号下限：正文 ≥ 14pt，代码块 ≥ 12pt
    - 中文 Microsoft YaHei，等宽 Consolas，数字 Bahnschrift（可选）
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ============== 在这里改三处 ==============
OUT      = "/mnt/d/培训/ai_lesson/lessonN/lessonN.pptx"   # ← 改课号
TITLE    = "第 N 课：<TOPIC>"                              # ← 改课题
SUBTITLE = "AI 驱动的软件开发提效实战课"

# ============== 调色板（每课换一个，避免视觉雷同） ==============
# 已用：lesson3=Slate, lesson4=Forest, lesson5=Ocean
# 推荐再加：Sunset / Lavender / Graphite

# Ocean Gradient（深海蓝）
OCEAN = dict(
    primary  = RGBColor(0x06, 0x5A, 0x82),   # 深海蓝
    accent   = RGBColor(0x1C, 0x72, 0x93),   # 青绿
    midnight = RGBColor(0x21, 0x29, 0x5C),   # 午夜
    cream    = RGBColor(0xF6, 0xF7, 0xF9),
    cream_2  = RGBColor(0xE2, 0xE8, 0xEE),
    line     = RGBColor(0xCB, 0xD5, 0xDF),
)

# Sunset（夕阳）
SUNSET = dict(
    primary  = RGBColor(0xC0, 0x4A, 0x3E),
    accent   = RGBColor(0xE0, 0x80, 0x4A),
    midnight = RGBColor(0x4A, 0x29, 0x21),
    cream    = RGBColor(0xFA, 0xF6, 0xEE),
    cream_2  = RGBColor(0xF1, 0xE5, 0xD0),
    line     = RGBColor(0xE0, 0xC8, 0xA8),
)

# Forest（森林绿）
FOREST = dict(
    primary  = RGBColor(0x2F, 0x5D, 0x3F),
    accent   = RGBColor(0x4A, 0x80, 0x55),
    midnight = RGBColor(0x1F, 0x2F, 0x24),
    cream    = RGBColor(0xF5, 0xF8, 0xF3),
    cream_2  = RGBColor(0xDE, 0xE8, 0xD4),
    line     = RGBColor(0xC0, 0xCF, 0xB6),
)

# 选一个：
PALETTE = OCEAN

# ============== 通用色与字体 ==============
INK   = RGBColor(0x22, 0x2A, 0x36)
MUTED = RGBColor(0x55, 0x6E, 0x82)
DIM   = RGBColor(0x80, 0x8E, 0x9E)
RED   = RGBColor(0xC0, 0x4A, 0x3E)
GREEN = RGBColor(0x3F, 0x7A, 0x55)
GOLD  = RGBColor(0xE0, 0xB0, 0x4A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

F_HAN   = "Microsoft YaHei"
F_LATIN = "Calibri"
F_MONO  = "Consolas"


# ============== 字体工具 ==============
def set_font(run, *, name=F_LATIN, size=14, bold=False, italic=False,
             color=INK, mono=False):
    """统一设置 run 的字体；中文走 east-asian fallback (F_HAN)。"""
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = F_MONO if mono else name
    rpr = run._r.get_or_add_rPr()
    ea = rpr.find(qn('a:ea'))
    if ea is None:
        ea = etree.SubElement(rpr, qn('a:ea'))
    ea.set('typeface', F_MONO if mono else F_HAN)


# ============== 形状工具 ==============
def add_text(slide, left, top, width, height, text, *,
             size=14, bold=False, italic=False, color=INK,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             mono=False, line_spacing=1.15):
    box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    r = p.add_run()
    r.text = text
    set_font(r, size=size, bold=bold, italic=italic, color=color, mono=mono)
    return box


def add_multi(slide, left, top, width, height, runs, *,
              align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.2):
    """runs: list of dict; {"text": ..., "size": ..., "bold": ..., "color": ..., "mono": ..., "br": True}"""
    box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    for run_def in runs:
        if run_def.get("br"):
            p = tf.add_paragraph()
            p.alignment = run_def.get("align", align)
            p.line_spacing = line_spacing
            if run_def.get("space_before"):
                p.space_before = Pt(run_def["space_before"])
            continue
        r = p.add_run()
        r.text = run_def["text"]
        set_font(r,
                 size=run_def.get("size", 14),
                 bold=run_def.get("bold", False),
                 italic=run_def.get("italic", False),
                 color=run_def.get("color", INK),
                 mono=run_def.get("mono", False))
    return box


def add_rect(slide, left, top, width, height, *, fill=None, line=None):
    fill = fill or PALETTE["cream_2"]
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                Inches(left), Inches(top),
                                Inches(width), Inches(height))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    return sh


# ============== 通用页底栏 / 页码 ==============
def add_footer(slide, page_num, total):
    add_rect(slide, 0, 7.30, 13.333, 0.20, fill=PALETTE["primary"])
    add_text(slide, 0.5, 7.05, 6, 0.25, SUBTITLE,
             size=10, color=DIM)
    add_text(slide, 12.0, 7.05, 1.0, 0.25, f"{page_num} / {total}",
             size=10, color=DIM, align=PP_ALIGN.RIGHT)


# ============== 单页构造器 ==============
def slide_cover(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(s, 0, 0, 13.333, 7.5, fill=PALETTE["midnight"])
    add_rect(s, 0, 6.0, 13.333, 0.08, fill=PALETTE["accent"])
    add_text(s, 0.8, 1.8, 11.7, 1.4, TITLE,
             size=44, bold=True, color=WHITE)
    add_text(s, 0.8, 3.4, 11.7, 0.6, SUBTITLE,
             size=18, color=PALETTE["cream_2"])
    add_text(s, 0.8, 6.6, 11.7, 0.4,
             "Lesson N · Speaker Name · Date",
             size=12, color=PALETTE["line"])
    return s


def slide_agenda(prs, total, items):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_text(s, 0.6, 0.5, 12, 0.7, "议程",
             size=32, bold=True, color=PALETTE["primary"])
    add_rect(s, 0.6, 1.25, 0.5, 0.04, fill=PALETTE["accent"])
    for i, t in enumerate(items):
        add_text(s, 0.9, 1.8 + i * 0.7, 11.5, 0.5,
                 f"{i+1}.  {t}", size=20, color=INK)
    add_footer(s, 2, total)
    return s


def slide_section(prs, total, page_num, *, kicker, title, body_runs):
    """通用主题页：左上 kicker（小标）、大标题、若干段正文 runs。"""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_text(s, 0.6, 0.5, 12, 0.35, kicker,
             size=12, bold=True, color=PALETTE["accent"])
    add_text(s, 0.6, 0.85, 12, 0.7, title,
             size=28, bold=True, color=PALETTE["primary"])
    add_rect(s, 0.6, 1.55, 0.5, 0.04, fill=PALETTE["accent"])
    add_multi(s, 0.6, 1.85, 12.1, 5.0, body_runs)
    add_footer(s, page_num, total)
    return s


def slide_code(prs, total, page_num, *, title, code, caption=None):
    """代码展示页：浅底背景 + 等宽。"""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_text(s, 0.6, 0.5, 12, 0.7, title,
             size=24, bold=True, color=PALETTE["primary"])
    add_rect(s, 0.6, 1.4, 12.1, 4.6, fill=PALETTE["cream"])
    add_text(s, 0.85, 1.55, 11.7, 4.3, code,
             size=14, color=PALETTE["midnight"], mono=True,
             line_spacing=1.35)
    if caption:
        add_text(s, 0.6, 6.15, 12.1, 0.5, caption,
                 size=12, color=MUTED, italic=False)
    add_footer(s, page_num, total)
    return s


def slide_closing(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(s, 0, 0, 13.333, 7.5, fill=PALETTE["midnight"])
    add_text(s, 0.8, 2.5, 11.7, 1.0, "学完这课你能做什么",
             size=32, bold=True, color=WHITE)
    add_rect(s, 0.8, 3.55, 0.5, 0.04, fill=PALETTE["accent"])
    add_multi(s, 0.8, 3.9, 11.7, 3.0, [
        {"text": "·  能力点 1", "size": 18, "color": PALETTE["cream"]},
        {"br": True},
        {"text": "·  能力点 2", "size": 18, "color": PALETTE["cream"]},
        {"br": True},
        {"text": "·  能力点 3", "size": 18, "color": PALETTE["cream"]},
        {"br": True},
        {"text": "·  能力点 4", "size": 18, "color": PALETTE["cream"]},
    ])
    return s


# ============== 主组装 ==============
def build():
    prs = Presentation()
    prs.slide_width  = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 先估页数（先写完再回填会更准；此处用 28 页占位）
    TOTAL = 28

    # ---- 封面 + 议程 ----
    slide_cover(prs, TOTAL)
    slide_agenda(prs, TOTAL, [
        "主题 1（4-6 页）",
        "主题 2（4-6 页）",
        "主题 3（4-6 页）",
        "反模式 + 作业",
    ])

    # ---- §一  概念页（4-6 页） ----
    slide_section(prs, TOTAL, 3,
        kicker="§ 一 · 概念",
        title="标题",
        body_runs=[
            {"text": "核心一句话总结。", "size": 20, "bold": True, "color": INK},
            {"br": True}, {"br": True},
            {"text": "展开第二段：用类比把概念点透。", "size": 16, "color": MUTED},
            {"br": True}, {"br": True},
            {"text": "对比 / 与上一课能力的关系。", "size": 16, "color": MUTED},
        ])
    # ... 复制上式继续添加到 §一 完整 ...

    # ---- §二  动手做（4-6 页，含至少一张代码页） ----
    slide_section(prs, TOTAL, 8,
        kicker="§ 二 · 动手做",
        title="装上 / 接入 / 启动 X",
        body_runs=[
            {"text": "前置：cwd 应在 lessonN/project/", "size": 16, "color": MUTED},
            {"br": True},
            {"text": "步骤 1 / 2 / 3 / 4 概述", "size": 16, "color": INK},
        ])
    slide_code(prs, TOTAL, 9,
        title="步骤 1：…",
        code=("$ cd lessonN/project\n"
              "$ python seed_db.py\n"
              "[seed] BTCUSDT: 写入 N 行\n"
              "[seed] 完成，N 行落库到 .../prices.db"),
        caption="期望 stderr 输出（行数随 LIMIT 不同）")

    # ---- §三  关键认知 / §四  反模式 / §作业 / 收束 ----
    # ... 按 README 章节继续填 ...

    slide_closing(prs, TOTAL)

    prs.save(OUT)
    print(f"[build] 写入 {OUT}（slides={len(prs.slides)}/{TOTAL}）")


if __name__ == "__main__":
    build()
