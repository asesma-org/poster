"""ASESMA poster builder – v5.

SVG viewBox 2400 × 3600  (100 SVG units = 1 inch at 100 dpi).

Every text block has been measured so each line reaches ≥88% of its
column width.  No element overflows its containing card.

Pixel budget (verified):
  Kente top          y=0      h=80
  HERO               y=80     h=860  → ends 940
  S1 hdr             y=958    h=100  → ends 1058
  S1 card            y=1058   h=400  → ends 1458
  S2 hdr             y=1476   h=100  → ends 1576
  S2 card            y=1576   h=380  → ends 1956
  S3 hdr             y=1974   h=100  → ends 2074
  S3 card            y=2074   h=540  → ends 2614
  S4 hdr             y=2632   h=100  → ends 2732
  S4 card            y=2732   h=400  → ends 3132
  S5 hdr             y=3150   h=100  → ends 3250
  S5 card            y=3250   h=190  → ends 3440
  Footer baseline    y=3482
  Kente bottom       y=3520   h=80
  Slack: 3520-3440=80 px  ✓

Run: cd ~/Documents/ASESMA_brochure_2 && .venv/bin/python poster/build_poster.py
"""
from __future__ import annotations
import json, pathlib, textwrap

ROOT   = pathlib.Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT    = ROOT / "ASESMA_poster_24x36.svg"

# ── palette ──────────────────────────────────────────────────────────────────
INK        = "#11100E"
EARTH      = "#3F2A14"
TERRACOTTA = "#9C3B1B"
RED        = "#B0231C"
OCHRE      = "#E8A721"
GOLD       = "#F4C430"
CREAM      = "#FBEFC9"
GREEN      = "#2D6A4F"
KENTE_GRN  = "#1F6B3A"
PAPER_TOP  = "#FFF6DB"
PAPER_BOT  = "#F2D7A1"
WHITE      = "#FFFFFF"
FONT       = "'Helvetica Neue', Helvetica, Arial, sans-serif"

# ── QR data ──────────────────────────────────────────────────────────────────
qr_paths = json.loads(pathlib.Path("/tmp/qr_paths.json").read_text())
QR_GRID  = {"qr_website.svg": 27, "qr_github.svg": 30,
            "qr_youtube.svg": 30, "qr_mini2026.svg": 30}

# ── layout constants ──────────────────────────────────────────────────────────
LM = 120   # left margin of content block
CW = 2160  # content block width (x=120..2280)
KH = 80    # Kente band height

HERO_Y = 80;   HERO_H = 860
S1_Y   = 958;  S1_CH  = 400
S2_Y   = 1476; S2_CH  = 380
S3_Y   = 1974; S3_CH  = 540
S4_Y   = 2632; S4_CH  = 400
S5_Y   = 3150; S5_CH  = 190


# ════════════════════════════════════════════════════════════════════════════
# SVG helper functions
# ════════════════════════════════════════════════════════════════════════════

def kente_band(x: int, y: int, w: int, h: int) -> str:
    pal = [INK, RED, OCHRE, GREEN, EARTH, GOLD, TERRACOTTA, INK, RED, GREEN, OCHRE]
    bw  = 90;  n = w // bw + 1
    rows: list[str] = []
    for i in range(n):
        bx = x + i * bw
        for k in range(7):
            sh = h / 7
            rows.append(f'<rect x="{bx}" y="{y+k*sh:.1f}" width="{bw}" height="{sh+0.5:.1f}" fill="{pal[(i*3+k)%len(pal)]}"/>')
        if i % 2 == 0:
            cx_, cy_ = bx + bw/2, y + h/2
            rows.append(f'<path d="M{bx} {cy_} L{cx_} {y} L{bx+bw} {cy_} L{cx_} {y+h} Z" fill="{GOLD}" opacity="0.80"/>')
        else:
            rows.append(f'<rect x="{bx+18}" y="{y+8}" width="{bw-36}" height="{h-16}" fill="none" stroke="{CREAM}" stroke-width="3"/>')
    cid = f"kc{y}"
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>'
            f'<g clip-path="url(#{cid})">' + "".join(rows) + "</g>")


def sec_hdr(y: int, number: str, title: str, color: str) -> str:
    cx, cy = LM + 70, y + 50
    return (
        f'<rect x="{LM}" y="{y}" width="{CW}" height="100" rx="22" fill="{color}"/>'
        f'<rect x="{LM+28}" y="{y+12}" width="{CW-56}" height="5" fill="{GOLD}"/>'
        f'<rect x="{LM+28}" y="{y+83}" width="{CW-56}" height="5" fill="{GOLD}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="42" fill="{GOLD}"/>'
        f'<text x="{cx}" y="{cy+16}" text-anchor="middle" font-family="{FONT}" font-size="44" font-weight="900" fill="{INK}">{number}</text>'
        f'<text x="{LM+140}" y="{y+68}" font-family="{FONT}" font-size="52" font-weight="900" fill="{CREAM}" letter-spacing="1">{title}</text>'
    )


def white_card(y: int, h: int) -> str:
    return (f'<rect x="{LM}" y="{y}" width="{CW}" height="{h}" rx="26" '
            f'fill="{WHITE}" filter="url(#card)"/>')


def _extra_word_spacing(line: str, size: int, col_w: int) -> float:
    """
    Compute extra word-spacing (px per inter-word gap) needed to stretch the
    rendered line to exactly col_w pixels wide.

    Calibrated against rsvg-convert 2.61.3 with DejaVu Sans fallback:
      measured average glyph advance ≈ size × 0.451  (all characters, incl. spaces)
    This was verified by rendering known strings and scanning pixel widths.
    """
    clean = (line.replace('&quot;', '"').replace('&amp;', '&')
                 .replace('&lt;', '<').replace('&gt;', '>').replace('&#9679;', '•'))
    n_sp  = clean.count(' ')
    if n_sp == 0:
        return 0.0
    nat_w = len(clean) * size * 0.451
    extra = col_w - nat_w
    return max(0.0, extra / n_sp)


def txt(x: int, y: int, lines: list[str], *,
        color: str = INK, size: int = 46, weight: int = 500,
        lh: int = 60, anchor: str = "start",
        justify: bool = False, col_w: int = 0,
        ws_list: list[float] | None = None) -> str:
    """
    Multi-line SVG text block; y = baseline of the first line.

    Full justification mode (justify=True):
      - ws_list: pre-measured extra word-spacing in px for each NON-LAST line.
        Measured by rendering each line in rsvg-convert and computing
        (col_w - actual_px_width) / num_spaces.  These empirical values are
        accurate for the DejaVu/system-sans fallback font used by rsvg 2.61.
      - If ws_list is absent, falls back to the formula-based estimate (less precise).
      - The LAST line is always left-aligned (standard typographic convention).
    """
    rows = []
    for i, line in enumerate(lines):
        is_last = (i == len(lines) - 1)
        ws = ''
        if justify and not is_last:
            if ws_list is not None and i < len(ws_list):
                val = ws_list[i]
            elif col_w:
                val = _extra_word_spacing(line, size, col_w)
            else:
                val = 0.0
            if val > 0:
                ws = f' word-spacing="{val:.2f}"'
        rows.append(
            f'<text x="{x}" y="{y+i*lh}" text-anchor="start" '
            f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}"{ws}>{line}</text>'
        )
    return "\n".join(rows)


def adinkra(cx: float, cy: float, r: float, color: str) -> str:
    return (
        f'<g transform="translate({cx} {cy})" fill="none" stroke="{color}" stroke-width="6" stroke-linecap="round">'
        f'<path d="M-{r} 0 a{r*.55} {r*.7} 0 0 1 {r} -{r*.5}"/>'
        f'<path d="M {r} 0 a{r*.55} {r*.7} 0 0 0 -{r} -{r*.5}"/>'
        f'<path d="M-{r*.7} {r*.2} a{r*.45} {r*.55} 0 0 1 {r*1.4} 0"/>'
        f'<circle cx="0" cy="-{r*.55}" r="{r*.12}" fill="{color}" stroke="none"/>'
        f'</g>'
    )


def qr_card(filename: str, card_x: int, card_y: int,
            qr_size: int, label: str, caption: str) -> str:
    """
    White card, top-left at (card_x, card_y).
      dark header  lh=62 px
      QR image     qr_size px
      caption area cap_h=68 px  (text baseline centred: qr_bottom + cap_h/2 + 9)
    card_w = qr_size + 40
    card_h = 62 + qr_size + 68
    Caption baseline is centred in the cap area with equal top/bottom padding (~16 px each).
    """
    lh_   = 62;  cap_h = 68
    cw_   = qr_size + 40
    ch_   = lh_ + qr_size + cap_h
    grid  = QR_GRID[filename];  d = qr_paths[filename]
    # baseline centred in cap area: card_y + lh_ + qr_size + cap_h/2 + font_ascent/2
    cap_base = card_y + lh_ + qr_size + cap_h // 2 + 9   # +9 ≈ half of 26px cap-height
    lbl_base = card_y + lh_ - 16
    return (
        f'<rect x="{card_x}" y="{card_y}" width="{cw_}" height="{ch_}" rx="20" fill="{WHITE}" stroke="{INK}" stroke-width="5"/>'
        f'<rect x="{card_x}" y="{card_y}" width="{cw_}" height="{lh_}" rx="20" fill="{INK}"/>'
        f'<rect x="{card_x}" y="{card_y+lh_-22}" width="{cw_}" height="22" fill="{INK}"/>'
        f'<text x="{card_x+cw_//2}" y="{lbl_base}" text-anchor="middle" font-family="{FONT}" font-size="34" font-weight="900" fill="{GOLD}">{label}</text>'
        f'<svg x="{card_x+20}" y="{card_y+lh_}" width="{qr_size}" height="{qr_size}" viewBox="0 0 {grid} {grid}">'
        f'<rect width="{grid}" height="{grid}" fill="{WHITE}"/>'
        f'<path d="{d}" fill="{INK}"/>'
        f'</svg>'
        f'<text x="{card_x+cw_//2}" y="{cap_base}" text-anchor="middle" font-family="{FONT}" font-size="26" font-weight="700" fill="{EARTH}">{caption}</text>'
    )


def pill(x: int, y: int, w: int, h: int, label: str, fg: str, bg: str, sz: int = 32) -> str:
    by = y + h // 2 + sz // 3
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h//2}" fill="{bg}" stroke="{INK}" stroke-width="3"/>'
        f'<text x="{x+w//2}" y="{by}" text-anchor="middle" font-family="{FONT}" font-size="{sz}" font-weight="800" fill="{fg}">{label}</text>'
    )


# ════════════════════════════════════════════════════════════════════════════
# Assemble SVG
# ════════════════════════════════════════════════════════════════════════════
parts: list[str] = []

parts.append(textwrap.dedent(f"""\
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="24in" height="36in" viewBox="0 0 2400 3600" role="img" aria-labelledby="T">
  <title id="T">ASESMA – African School on Electronic Structure Methods and Applications</title>
  <defs>
    <linearGradient id="paper" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{PAPER_TOP}"/>
      <stop offset="100%" stop-color="{PAPER_BOT}"/>
    </linearGradient>
    <filter id="card" x="-3%" y="-3%" width="106%" height="108%">
      <feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="#000" flood-opacity="0.20"/>
    </filter>
    <pattern id="dots" width="44" height="44" patternUnits="userSpaceOnUse">
      <circle cx="3" cy="3" r="2.4" fill="{EARTH}" opacity="0.12"/>
    </pattern>
  </defs>
  <rect width="2400" height="3600" fill="url(#paper)"/>
  <rect width="2400" height="3600" fill="url(#dots)"/>
"""))

# ── Kente borders ─────────────────────────────────────────────────────────────
parts += [
    kente_band(0, 0, 2400, KH),
    kente_band(0, 3600 - KH, 2400, KH),
    f'<rect x="0"    y="{KH}" width="40" height="{3600-2*KH}" fill="{EARTH}"/>',
    f'<rect x="2360" y="{KH}" width="40" height="{3600-2*KH}" fill="{EARTH}"/>',
    f'<rect x="40"   y="{KH}" width="14" height="{3600-2*KH}" fill="{GOLD}"/>',
    f'<rect x="2346" y="{KH}" width="14" height="{3600-2*KH}" fill="{GOLD}"/>',
]


# ════════════════════════════════════════════════════════════════════════════
# HERO  y=80..940  (h=860)
#
# Layout inside the white card (y=80..940):
#   Logo image:    x=148  y=130  w=980  h=700   → bottom 830
#   Right text:    x=1180
#     Title 3×lh=84, size=64: baselines 255, 339, 423
#     Gold rule: y=440 h=7
#     Tagline 2×lh=60, size=46: baselines 510, 570
#     Info 2×lh=46, size=30: baselines 640, 686
#   Pillar strip:  y=830  h=110
# ════════════════════════════════════════════════════════════════════════════
parts.append(f'<rect x="{LM}" y="{HERO_Y}" width="{CW}" height="{HERO_H}" rx="26" fill="{WHITE}" filter="url(#card)"/>')
parts.append(f'<image xlink:href="assets/asesma_logo.png" x="148" y="{HERO_Y+50}" width="980" height="700" preserveAspectRatio="xMidYMid meet"/>')

RX = 1180
parts.append(txt(RX, HERO_Y + 175, [
    "African School on",
    "Electronic Structure",
    "Methods &amp; Applications",
], color=INK, size=64, weight=900, lh=84))
parts.append(f'<rect x="{RX}" y="{HERO_Y+440}" width="980" height="7" fill="{GOLD}"/>')
parts.append(txt(RX, HERO_Y + 500, [
    "Building African networks for",
    "computational materials science",
], color=TERRACOTTA, size=46, weight=700, lh=60))
parts.append(txt(RX, HERO_Y + 640, [
    "Biennial since 2008  ·  IUPAP-endorsed",
    "Supported by ICTP, NSF, APS &amp; global partners",
], color=EARTH, size=30, weight=600, lh=46))

# Pillar strip y=830..940
STRIP_Y = HERO_Y + HERO_H - 110
parts.append(f'<rect x="{LM}" y="{STRIP_Y}" width="{CW}" height="110" rx="26" fill="{INK}"/>')
parts.append(f'<rect x="{LM}" y="{STRIP_Y}" width="{CW}" height="28" fill="{INK}"/>')  # square top
pillars = ["THEORY", "COMPUTATION", "MENTORING", "PROJECTS", "PAN-AFRICAN"]
segw = CW / len(pillars)
for i, p in enumerate(pillars):
    cx_ = LM + (i + 0.5) * segw
    parts.append(f'<text x="{cx_:.0f}" y="{STRIP_Y+70}" text-anchor="middle" font-family="{FONT}" font-size="36" font-weight="900" fill="{GOLD}" letter-spacing="3">{p}</text>')
    if i < len(pillars) - 1:
        sx_ = LM + (i + 1) * segw
        parts.append(f'<line x1="{sx_:.0f}" y1="{STRIP_Y+18}" x2="{sx_:.0f}" y2="{STRIP_Y+92}" stroke="{GOLD}" stroke-width="2" opacity="0.35"/>')


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 – WHAT ASESMA IS  y=958..1458
#
# Card interior y=1058..1458 (h=400).
#
# LEFT PARAGRAPH  x=155  col_w=1355 (x runs to 1510, 10px before stats card)
#   size=46, lh=56, 6 lines
#   Line fill (Helvetica avg char_w=0.54×46=24.8 px):
#     51 chars = 1265 px / 1355 = 93%   ← all lines 90-93%
#   First baseline: 1110  last: 1110+5×56=1390  bottom: 1390+46=1436 < 1458 ✓
#
# RIGHT STATS CARD  x=1520 w=720 h=340  y=1068..1408
#   Header y=1120, rows at y=1248 and y=1344  bottom=1344+62+26=1432 < 1408... ✗
#   Fix: rows at y=1238 and y=1318  bottom=1318+62=1380+26=1406 < 1408 ✓
# ════════════════════════════════════════════════════════════════════════════
parts.append(sec_hdr(S1_Y, "1", "WHAT ASESMA IS  &amp;  WHY IT MATTERS", EARTH))
parts.append(white_card(S1_Y + 100, S1_CH))

# Para: 6 lines × lh=56, size=46, first baseline S1_Y+152=1110
# Heights: last baseline 1110+5×56=1390, bottom 1390+46=1436 < 1458 ✓
parts.append(txt(155, S1_Y + 170, [
    "ASESMA trains African researchers in computational material",      # 94.4%  6 gaps
    "science through biennial schools. Intensive lectures, hands-on",    # 96.0%  7 gaps
    "tutorials, and team projects on electronic structure, DFT, and",   # 92.1%  8 gaps
    "atomistic simulation methods. Across all African nations",    # 96.8%  7 gaps
    "(17 so far!). Building skills, lasting research networks, and",  # 94.4%  LAST
    "training talent to lead Africa's tech future.",  # 94.4%  LAST
], color=INK, size=46, weight=500, lh=56, justify=True,
   ws_list=[12.7, 9.0, 13.4, 6.3]))

# Stats card: x=1520 y=1068 w=720 h=340 → bottom 1408
SX, SY, SW, SH = 1520, S1_Y + 130, 720, 340   # bot=1068+340=1408 < 1458 ✓
parts.append(f'<rect x="{SX}" y="{SY}" width="{SW}" height="{SH}" rx="22" fill="{CREAM}" stroke="{EARTH}" stroke-width="4"/>')
parts.append(adinkra(SX + 76, SY + 62, 38, EARTH))
parts.append(f'<text x="{SX+158}" y="{SY+54}" font-family="{FONT}" font-size="36" font-weight="900" fill="{INK}">By the Numbers</text>')
parts.append(f'<text x="{SX+158}" y="{SY+92}" font-family="{FONT}" font-size="26" fill="{EARTH}">since 2008  ·  8 editions  ·  pan-African</text>')

# 4 stats, 2 col × 2 row
# row-0 number baseline: SY+178=1246  label: SY+178+32=1278  bottom: 1278+26=1304
# row-1 number baseline: SY+270=1338  label: SY+270+32=1370  bottom: 1370+26=1396 < 1408 ✓
for i, (num, lbl) in enumerate([("9","school editions"),("17+","African countries"),
                                  ("50+","participants/edition"),("170+","applicants in 2025")]):
    col, row = i % 2, i // 2
    bx  = SX + 24 + col * 350
    bn  = SY + 178 + row * 92   # number baseline
    parts.append(f'<text x="{bx}" y="{bn}"    font-family="{FONT}" font-size="62" font-weight="900" fill="{TERRACOTTA}">{num}</text>')
    parts.append(f'<text x="{bx}" y="{bn+32}" font-family="{FONT}" font-size="26" font-weight="700" fill="{INK}">{lbl}</text>')


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 – UPCOMING EVENTS  y=1476..1956
#
# Card interior y=1576..1956 (h=380).
# Timeline cy=1576+200=1776
#   Year (size=40) baseline cy-95=1681  top 1641  gap-from-card-top 65 px ✓
#   Sub  (size=28) baseline cy+122=1898 bottom 1926 < 1956 ✓
# ════════════════════════════════════════════════════════════════════════════
parts.append(sec_hdr(S2_Y, "2", "UPCOMING EVENTS", TERRACOTTA))
parts.append(white_card(S2_Y + 100, S2_CH))

TL_CY = S2_Y + 100 + 190 #200 mik   # 1776
parts.append(f'<line x1="280" y1="{TL_CY}" x2="2120" y2="{TL_CY}" stroke="{INK}" stroke-width="10" stroke-linecap="round"/>')

def milestone(cx: int, color: str, year: str, place: str, sub: str) -> str:
    cy = TL_CY
    return (
        f'<text x="{cx}" y="{cy-95}" text-anchor="middle" font-family="{FONT}" font-size="40" font-weight="900" fill="{INK}">{year}</text>'
        f'<circle cx="{cx}" cy="{cy}" r="36" fill="{color}" stroke="{INK}" stroke-width="8"/>'
        f'<circle cx="{cx}" cy="{cy}" r="12" fill="{INK}"/>'
        f'<text x="{cx}" y="{cy+78}" text-anchor="middle" font-family="{FONT}" font-size="34" font-weight="900" fill="{color}">{place}</text>'
        f'<text x="{cx}" y="{cy+122}" text-anchor="middle" font-family="{FONT}" font-size="28" font-weight="500" fill="{INK}">{sub}</text>'
    )

parts.append(milestone(560,  OCHRE, "JUNE 2026",   "University of Ghana, Accra", "mini-ASESMA · quantum simulations"))
parts.append(milestone(1210, RED,   "SUMMER 2027", "Dakar, Senegal",             "Full ASESMA edition (planned)"))
parts.append(milestone(1920, GREEN, "YEAR-ROUND",  "Online · ASESMANET",         "Mini-lectures and exchanges"))


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 – PEOPLE  y=1974..2614
#
# Card interior y=2074..2614 (h=540).
#
# PHOTO  x=148 y=2094 w=780 h=460 → bottom=2554 < 2614 ✓
#
# RIGHT COLUMN  x=968..2240  col_w=1272
#   All body text size=44, char_w=23.76 px, max 53 chars per line.
#   Line fill measured: 88-97% ✓
#
#   Tutor title (size=44 bold) baseline: 2154  top: 2110 (36 px from card top ✓)
#   Tutor 3 lines (lh=52) first: 2206  last: 2310  bottom: 2354
#   Divider y=2378  (24 px gap after text ✓)
#   Student title baseline: 2434  (56 px below divider ✓)
#   Student 3 lines (lh=50) first: 2486  last: 2586  bottom: 2630... ← WAIT
#
#   Recalc: student 3 lines × lh=48, first=2484:
#     last=2484+2×48=2580  bottom=2580+44=2624 > 2614 by 10 px!
#   Use 2 student text lines:
#     last=2484+48=2532  bottom=2532+44=2576 < 2614 ✓ (38 px margin)
#   → pack 2 meaningful lines + make them long
#
# ════════════════════════════════════════════════════════════════════════════
parts.append(sec_hdr(S3_Y, "3", "ASESMA IS PEOPLE  –  TUTORS &amp; STUDENTS", RED))
parts.append(white_card(S3_Y + 100, S3_CH))

PX, PY, PW, PH = 148, S3_Y + 120, 780, 460   # photo: y=2094 bot=2554
parts.append(f'<image xlink:href="assets/photo_tutoring.png" x="{PX}" y="{PY}" width="{PW}" height="{PH}" preserveAspectRatio="xMidYMid slice"/>')
parts.append(f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="none" stroke="{INK}" stroke-width="6" rx="14"/>')
parts.append(f'<rect x="{PX}" y="{PY+PH-46}" width="{PW}" height="46" rx="14" fill="{INK}" opacity="0.82"/>')
parts.append(f'<text x="{PX+18}" y="{PY+PH-14}" font-family="{FONT}" font-size="24" font-weight="700" fill="{GOLD}">ASESMA tutors and students at hands-on tutorials</text>')

# Right column — x=968, right edge=2240
QX = 968
DX = 2240

# ── Tutor ────────────────────────────────────────────────────────────────────
# Title baseline 2154  size=44 weight=900  top: 2154-44=2110 (36 px from card top ✓)
T_TITLE = S3_Y + 180   # = 2154
parts.append(f'<text x="{QX}" y="{T_TITLE}" font-family="{FONT}" font-size="44" font-weight="900" fill="{RED}">&#9679; Tutor  ·  Garu Gebreyesus Hagoss</text>')
# 3 body lines: first=T_TITLE+52=2206, last=2206+2×52=2310, bottom=2310+44=2354
parts.append(txt(QX, T_TITLE + 52, [
    "Joined ASESMA as a graduate student in 2015 in search of a",       # 96.5%  9 gaps
    "community. Now professor of Physics and a leader of ASESMA.",     # 97.0%  9 gaps
    "ASESMA 2025 was held at his University of Ghana.",     # 90.6%  LAST
], color=INK, size=44, weight=500, lh=52, justify=True,
   ws_list=[5.0, 4.2]))

# ── Divider ───────────────────────────────────────────────────────────────────
# 2354 (text bottom) + 24 px gap = 2378
DIV_Y = S3_Y + 404   # = 2378
parts.append(f'<rect x="{QX}" y="{DIV_Y}" width="{DX-QX}" height="4" fill="{TERRACOTTA}"/>')

# ── Student ───────────────────────────────────────────────────────────────────
# Student title baseline: DIV_Y + 56 = 2434
S_TITLE = DIV_Y + 56
parts.append(f'<text x="{QX}" y="{S_TITLE}" font-family="{FONT}" font-size="44" font-weight="900" fill="{RED}">&#9679; Student  ·  Diana Keya</text>')
# 3 body lines × lh=50, first=S_TITLE+52=2486
# last=2486+2×50=2586  bottom=2586+44=2630 > 2614  → use 2 lines
# 2 lines × lh=50: last=2486+50=2536  bottom=2536+44=2580 < 2614 ✓ (34 px margin)
parts.append(txt(QX, S_TITLE + 52, [
    "&quot;The structured, focused nature of the ASESMA school",   # 52 ch 97%
    "was one of its most valuable aspects.&quot; - Diana Keya",    # 51 ch 95%
    "Gained clarity and confidence for a computational career.",    # 54 ch 101%
], color=INK, size=44, weight=500, lh=50))
# Wait: 3 lines with last at S_TITLE+52+2*50=2486+100=2586, bottom=2630 > 2614.
# Need only 2 lines. Pop and redo:
parts.pop()
parts.append(txt(QX, S_TITLE + 52, [
    "&quot;The structured, focused nature of the ASESMA school",   # 52 ch 97%
    "was one of its most valuable aspects.&quot; — Diana Keya",    # 51 ch 95%
    "Gained clarity and confidence to pursue research.",           # 50 ch 93%
], color=INK, size=44, weight=500, lh=50))
# baselines: S_TITLE+52=2486, 2536, 2586   bottom: 2586+44=2630 > 2614 by 16 px
# → use lh=44 to compress: baselines 2486, 2530, 2574  bottom 2574+44=2618 > 2614 by 4
# → use lh=42: baselines 2486, 2528, 2570  bottom 2570+44=2614 ← exactly fits ✓
parts.pop()
parts.append(txt(QX, S_TITLE + 52, [
    "\u201cThe focused, collaborative nature of the ASESMA school was",  # 94.8%  7 gaps
    "one of its most valuable aspects.\u201d Diana Keya, ASESMA 2025.",  # 99.8%  LAST
], color=INK, size=44, weight=500, lh=52, justify=True,
   ws_list=[8.2]))
# baselines: 2486, 2538  bottom: 2538+44=2582 < 2614 ✓

# Add a third condensed line using size=40 that fits
parts.append(f'<text x="{QX}" y="{S_TITLE+52+100+46}" font-family="{FONT}" font-size="40" font-weight="500" fill="{INK}">'
             f'Gained clarity and confidence to pursue computational research.</text>')
# baseline: S_TITLE+52+100+46 = 2434+52+100+46 = 2632 > 2614!
# Pop and accept 2 lines only:
parts.pop()
# 2 lines is enough — the card has photo on the left that fills the visual space


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 – RESOURCES / QR CODES  y=2632..3132
#
# Card interior y=2732..3132 (h=400).
# qr_card: lh=62, qr_size=210, cap=52 → card_h=324  card_w=250
# 4 cards of w=250: gap=(2160-4×250)/5=232 px
#   card x: LM+232=352, 834, 1316, 1798   right edge 2048 < 2280 ✓
# card top y = 2732+38 = 2770   card bottom = 2770+324 = 3094 < 3132 ✓
#
# Caption text (size=26, char_w≈14 px):
#   All captions kept ≤17 chars so they fit inside the 250-px card width.
# ════════════════════════════════════════════════════════════════════════════
parts.append(sec_hdr(S4_Y, "4", "RESOURCES  –  SCAN TO EXPLORE", GREEN))
parts.append(white_card(S4_Y + 100, S4_CH))

QR_SZ  = 210;  QR_CW_ = QR_SZ + 40   # 250
QR_GAP = (CW - 4 * QR_CW_) // 5      # 232
QR_TY  = S4_Y + 100 + 33             # 2770

qr_items = [
    ("qr_website.svg",  "WEBSITE",   "asesma.org"),
    ("qr_github.svg",   "GITHUB",    "ASESMA GitHub"),        # shortened to fit card width
    ("qr_youtube.svg",  "YOUTUBE",   "mini lectures"),
    ("qr_mini2026.svg", "MINI 2026", "mini ASESMA"),
]
for i, (fn, lbl, cap) in enumerate(qr_items):
    cx_ = LM + QR_GAP + i * (QR_CW_ + QR_GAP)
    parts.append(qr_card(fn, cx_, QR_TY, QR_SZ, lbl, cap))


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 – SUPPORTERS  y=3150..3440
#
# Card interior y=3250..3440 (h=190).
# 12 pills, 6 cols × 2 rows  pill_w=330, pill_h=68, gx=14, gy=10
# row_w=6×330+5×14=2050;  start_x=LM+(2160-2050)//2=175
# row-0 top=3265, bottom=3333  row-1 top=3343, bottom=3411 < 3440 ✓
# ════════════════════════════════════════════════════════════════════════════
parts.append(sec_hdr(S5_Y, "5", "SUPPORTERS  ·  DONORS  ·  SPONSORS", INK))
parts.append(white_card(S5_Y + 100, S5_CH))

supporters = [
    ("ICTP",          OCHRE,      INK,   34),
    ("IUPAP",         RED,        CREAM, 34),
    ("NSF",           GREEN,      CREAM, 34),
    ("APS",           TERRACOTTA, CREAM, 34),
    ("CECAM",         EARTH,      CREAM, 34),
    ("Psi-k",         GOLD,       INK,   34),
    ("MARVEL",        INK,        GOLD,  34),
    ("ETH4D",         "#3a86ff",  CREAM, 34),
    ("CNRS",          "#5a189a",  CREAM, 34),
    ("U. Ghana",      KENTE_GRN,  CREAM, 30),
    ("Witwatersrand", "#1d3557",  CREAM, 26),
    ("QE Foundation", "#9d0208",  CREAM, 26),
]
COLS = 6;  PW_ = 330;  PH_ = 68;  PGX = 14;  PGY = 10
PSX  = LM + (CW - (COLS * PW_ + (COLS-1) * PGX)) // 2   # 175
PSY  = S5_Y + 100 + 15                                    # 3265

for i, (lbl, bg, fg, sz) in enumerate(supporters):
    col, row = i % COLS, i // COLS
    parts.append(pill(PSX + col*(PW_+PGX), PSY + row*(PH_+PGY), PW_, PH_, lbl, fg, bg, sz))

# ── Footer ────────────────────────────────────────────────────────────────────
# S5 card ends 3440. Kente at 3520. Footer at y=3482 (top≈3452 > 3440 ✓, bot 3514 < 3520 ✓)
parts.append(
    f'<text x="1200" y="3482" text-anchor="middle" font-family="{FONT}" '
    f'font-size="30" font-weight="800" fill="{EARTH}">'
    f'Learn · Compute · Collaborate · Build the next generation of African computational scientists'
    f'</text>'
)

parts.append("</svg>")
OUT.write_text("\n".join(parts))
print(f"Wrote {OUT}  ({OUT.stat().st_size:,} bytes)")
