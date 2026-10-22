#!/usr/bin/env python3
"""
Genera las guías en PDF a partir de Markdown.

    python docs/build_pdf.py docs/guia-app-movil.md docs/Guia_App_Movil_Biblioteca.pdf

Requisitos:  pip install reportlab   (fuentes DejaVu del sistema para acentos y símbolos)

Extensiones sobre Markdown:
  {{file:app:ruta/archivo.ts}}                      código completo del repositorio de la app
  {{file:api:ruta/archivo.ts|from=texto|to=texto}}  fragmento: desde la 1.ª línea que contiene `from`
                                                    hasta la 1.ª línea posterior que contiene `to` (inclusive) o `until` (exclusivo)
  {{create:app:ruta}}                               "Crea este archivo": código COMPLETO tomado del repositorio
  {{path:api:ruta}} + bloque ``` ... ```            "Crea este archivo" con el contenido escrito en la guía
  {{merge:app:package.json}} + bloque ```json```    "Agrega esto a" un JSON existente (fusión recursiva)
  {{append:api:.gitignore}} + bloque ```            "Agrega al final de" un archivo
  {{delete:app:ruta}}                               "Elimina este archivo"
  {{run:api}} + bloque ```bash```                   comandos de terminal (carpeta del proyecto indicado)
  {{checkpoint:api:nombre|comprobaciones}}          punto de control (lo ejecuta replay.py; no se dibuja)
  {{diagram:architecture}} / {{diagram:sync}}       diagramas dibujados con reportlab
  > [!NOTA] ... / [!OJO] / [!IDEA] / [!EVIDENCIA]   recuadros
  <<<PAGEBREAK>>>                                   salto de página
El código incluido se lee del repositorio en el momento de construir: el PDF nunca se desfasa del proyecto.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Flowable, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph,
    Spacer, Table, TableStyle, XPreformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = Path(__file__).resolve().parent
ROOTS = {"app": HERE.parent, "api": HERE.parent.parent / "library_api"}
FOLDERS = {"app": "library_app", "api": "library_api"}

# ───────────────────────────── Fuentes ─────────────────────────────
FONT_DIRS = [Path("/usr/share/fonts/truetype/dejavu"), Path("/mnt/wslg/distro/usr/share/fonts/truetype/dejavu")]


def font(name: str) -> str:
    for d in FONT_DIRS:
        if (d / name).exists():
            return str(d / name)
    sys.exit(f"No se encontró la fuente {name}. Instala fonts-dejavu-core.")


pdfmetrics.registerFont(TTFont("Sans", font("DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Sans-Bold", font("DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Sans-Italic", font("DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Sans-BoldItalic", font("DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Mono", font("DejaVuSansMono.ttf")))
pdfmetrics.registerFont(TTFont("Mono-Bold", font("DejaVuSansMono-Bold.ttf")))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans-Italic", boldItalic="Sans-BoldItalic")
pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-Bold", italic="Mono", boldItalic="Mono-Bold")

# ───────────────────────────── Estilos ─────────────────────────────
INK = colors.HexColor("#1F2430")
MUTED = colors.HexColor("#5B6475")
ACCENT = colors.HexColor("#2563EB")
LINE = colors.HexColor("#D5D9E2")
CODE_BG = colors.HexColor("#F4F6FA")

base = ParagraphStyle("base", fontName="Sans", fontSize=9.6, leading=14.2, textColor=INK, alignment=TA_LEFT)
S = {
    "p": ParagraphStyle("p", parent=base, spaceAfter=6),
    "h1": ParagraphStyle("h1", parent=base, fontName="Sans-Bold", fontSize=20, leading=25, textColor=ACCENT, spaceBefore=0, spaceAfter=12),
    "h2": ParagraphStyle("h2", parent=base, fontName="Sans-Bold", fontSize=13.5, leading=18, spaceBefore=14, spaceAfter=6, keepWithNext=1),
    "h3": ParagraphStyle("h3", parent=base, fontName="Sans-Bold", fontSize=11, leading=15, textColor=ACCENT, spaceBefore=10, spaceAfter=4, keepWithNext=1),
    "li": ParagraphStyle("li", parent=base, spaceAfter=2.5),
    "cell": ParagraphStyle("cell", parent=base, fontSize=8.4, leading=11.4),
    "cellh": ParagraphStyle("cellh", parent=base, fontName="Sans-Bold", fontSize=8.4, leading=11.4, textColor=colors.white),
    "cap": ParagraphStyle("cap", parent=base, fontName="Mono-Bold", fontSize=7.6, leading=10, textColor=MUTED, spaceBefore=6, spaceAfter=9),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=6.6, leading=9.0, textColor=INK, backColor=CODE_BG,
                           borderPadding=(5, 6, 5, 6), leftIndent=-6, rightIndent=-6, spaceAfter=10),
    "callout": ParagraphStyle("callout", parent=base, fontSize=9.2, leading=13.4),
    "cover_title": ParagraphStyle("ct", parent=base, fontName="Sans-Bold", fontSize=30, leading=36, textColor=ACCENT),
    "cover_sub": ParagraphStyle("cs", parent=base, fontSize=14, leading=20, textColor=MUTED),
    "toc_title": ParagraphStyle("tt", parent=base, fontName="Sans-Bold", fontSize=20, leading=25, textColor=ACCENT, spaceAfter=12),
}
TOC_STYLES = [
    ParagraphStyle("toc0", parent=base, fontName="Sans-Bold", fontSize=10.5, leading=16, spaceBefore=4),
    ParagraphStyle("toc1", parent=base, fontSize=9, leading=13, leftIndent=14, textColor=MUTED),
]

CALLOUTS = {
    "NOTA": ("Nota", "#E8F0FE", "#2563EB"),
    "OJO": ("Ojo", "#FFF4E5", "#D9730D"),
    "IDEA": ("Idea", "#E7F6EC", "#1A8F4C"),
    "EVIDENCIA": ("Evidencia para el docente", "#F1ECFB", "#6B46C1"),
}

# ───────────────────────────── Inline ─────────────────────────────
def inline(text: str, code_color: str = "#B4237B") -> str:
    """Markdown en línea → marcado de reportlab (con escape previo)."""
    codes: list[str] = []

    def stash(m: re.Match) -> str:
        codes.append(f'<font name="Mono" size="8.4" color="{code_color}">{escape(m.group(1))}</font>')
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" color="#2563EB">\1</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


# ───────────────────────────── Resaltado de código ─────────────────────────────
KEYWORDS = (
    "import export from const let var function async await return if else for while try catch finally throw new class "
    "interface type extends implements default as of in typeof null undefined true false void enum readonly private public "
    "static switch case break continue satisfies SELECT FROM WHERE INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE INDEX "
    "PRIMARY KEY NOT NULL DEFAULT CHECK ON CONFLICT DO ORDER BY LIMIT AND OR LIKE ESCAPE PRAGMA UNIQUE"
).split()
KW = re.compile(r"\b(" + "|".join(KEYWORDS) + r")\b")
STR = re.compile(r"""("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)""")
COLOR = {"comment": "#6A8759", "string": "#B45309", "kw": "#6D28D9"}
WRAP = 122


def highlight_line(line: str, lang: str) -> str:
    stripped = line.lstrip()
    hash_comments = lang in {"sh", "bash", "env", "yaml", "python", "py"}
    if lang in {"sh", "bash", "env"} and not stripped.startswith("#"):
        pass
    if (not hash_comments and stripped.startswith(("//", "/*", "*", "*/"))) or (hash_comments and stripped.startswith("#")) or (lang == "sql" and stripped.startswith("--")):
        return f'<font color="{COLOR["comment"]}">{escape(line)}</font>'

    out, pos = [], 0
    comment_re = re.compile(r"(//.*$)" if not hash_comments else r"(\s#.*$)")
    tokens = [(m.start(), m.end(), "string") for m in STR.finditer(line)]
    cm_ = comment_re.search(line)
    if cm_ and not any(s <= cm_.start() < e for s, e, _ in tokens):
        tokens = [t for t in tokens if t[1] <= cm_.start()] + [(cm_.start(), len(line), "comment")]
    tokens.sort()
    for s, e, kind in tokens:
        out.append(_kw(line[pos:s]))
        out.append(f'<font color="{COLOR[kind]}">{escape(line[s:e])}</font>')
        pos = e
    out.append(_kw(line[pos:]))
    return "".join(out)


def _kw(chunk: str) -> str:
    res, pos = [], 0
    for m in KW.finditer(chunk):
        res.append(escape(chunk[pos:m.start()]))
        res.append(f'<font color="{COLOR["kw"]}">{escape(m.group(1))}</font>')
        pos = m.end()
    res.append(escape(chunk[pos:]))
    return "".join(res)


def wrap_code(line: str) -> list[str]:
    line = line.expandtabs(2).rstrip()
    if len(line) <= WRAP:
        return [line]
    indent = len(line) - len(line.lstrip())
    parts, first = [], True
    while len(line) > WRAP:
        cut = line.rfind(" ", indent + 20, WRAP)
        cut = cut if cut > 0 else WRAP
        parts.append(line[:cut].rstrip() if first else line[:cut])
        line = " " * (indent + 4) + "↪ " + line[cut:].lstrip()
        first = False
    parts.append(line)
    return parts


def code_flowable(code: str, lang: str):
    rows = []
    for raw in code.split("\n"):
        for seg in wrap_code(raw):
            rows.append(highlight_line(seg, lang))
    return XPreformatted("\n".join(rows) if rows else " ", S["code"])


# ───────────────────────────── Includes ─────────────────────────────
def read_include(spec: str) -> tuple[str, str, str]:
    parts = spec.split("|")
    key, _, rel = parts[0].partition(":")
    path = ROOTS[key] / rel
    if not path.exists():
        sys.exit(f"Include no encontrado: {path}")
    lines = path.read_text(encoding="utf8").rstrip("\n").split("\n")
    opts = dict(p.split("=", 1) for p in parts[1:])
    if "from" in opts:
        start = next((i for i, l in enumerate(lines) if opts["from"] in l), None)
        if start is None:
            sys.exit(f"'from={opts['from']}' no aparece en {path}")
        end = len(lines) - 1
        if "until" in opts:
            stop = next((i for i in range(start + 1, len(lines)) if opts["until"] in lines[i]), None)
            if stop is None:
                sys.exit(f"'until={opts['until']}' no aparece tras 'from' en {path}")
            end = stop - 1
            while end > start and not lines[end].strip():
                end -= 1
        elif "to" in opts:
            end = next((i for i in range(start + 1, len(lines)) if opts["to"] in lines[i]), None)
            if end is None:
                sys.exit(f"'to={opts['to']}' no aparece tras 'from' en {path}")
        lines = lines[start:end + 1]
        # Quita la sangría común para que el fragmento no aparezca corrido a la derecha.
        indents = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
        cut = min(indents) if indents else 0
        lines = [l[cut:] for l in lines]
    ext = path.suffix.lstrip(".")
    label = f"{'library_app' if key == 'app' else 'library_api'}/{rel}"
    return label, "\n".join(lines), {"mts": "ts", "tsx": "ts", "json": "ts"}.get(ext, ext)


# ───────────────────────────── Diagramas ─────────────────────────────
def _box(d, x, y, w, h, text, fill, stroke, size=8, bold=False, sub=None):
    d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=colors.HexColor(fill), strokeColor=colors.HexColor(stroke), strokeWidth=1))
    fn = "Sans-Bold" if bold else "Sans"
    ty = y + h / 2 + (3 if sub else -3)
    d.add(String(x + w / 2, ty, text, fontName=fn, fontSize=size, fillColor=INK, textAnchor="middle"))
    if sub:
        d.add(String(x + w / 2, y + h / 2 - 9, sub, fontName="Sans", fontSize=size - 1.5, fillColor=MUTED, textAnchor="middle"))


def _arrow(d, x1, y1, x2, y2, color="#475569", both=False):
    d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor(color), strokeWidth=1.3))
    import math
    def head(x, y, ang):
        a = 5
        d.add(Polygon([x, y, x - a * math.cos(ang - 0.4), y - a * math.sin(ang - 0.4), x - a * math.cos(ang + 0.4), y - a * math.sin(ang + 0.4)],
                      fillColor=colors.HexColor(color), strokeColor=colors.HexColor(color)))
    ang = math.atan2(y2 - y1, x2 - x1)
    head(x2, y2, ang)
    if both:
        head(x1, y1, ang + math.pi)


def diagram_architecture() -> Drawing:
    d = Drawing(480, 235)
    _box(d, 0, 20, 150, 195, "", "#EEF4FF", "#2563EB")
    d.add(String(75, 198, "App móvil", fontName="Sans-Bold", fontSize=10, fillColor=INK, textAnchor="middle"))
    d.add(String(75, 187, "React Native + Expo", fontName="Sans", fontSize=7.5, fillColor=MUTED, textAnchor="middle"))
    _box(d, 12, 140, 126, 34, "Pantallas (Expo Router)", "#FFFFFF", "#93B4F5", 7.5)
    _box(d, 12, 98, 126, 34, "SQLite (expo-sqlite)", "#FFFFFF", "#93B4F5", 7.5, sub="caché + cola offline")
    _box(d, 12, 56, 126, 34, "SecureStore", "#FFFFFF", "#93B4F5", 7.5, sub="tokens de sesión")
    _box(d, 12, 28, 126, 20, "Cliente HTTP + Sync", "#FFFFFF", "#93B4F5", 7.5)

    _box(d, 190, 20, 130, 195, "", "#F1ECFB", "#6B46C1")
    d.add(String(255, 198, "library_api", fontName="Sans-Bold", fontSize=10, fillColor=INK, textAnchor="middle"))
    d.add(String(255, 187, "Next.js 16", fontName="Sans", fontSize=7.5, fillColor=MUTED, textAnchor="middle"))
    _box(d, 200, 140, 110, 34, "Route Handlers", "#FFFFFF", "#B9A5E8", 7.5, sub="/api/auth /books /loans")
    _box(d, 200, 98, 110, 34, "Sitio web", "#FFFFFF", "#B9A5E8", 7.5, sub="Server Components")
    _box(d, 200, 56, 110, 34, "Reglas de dominio", "#FFFFFF", "#B9A5E8", 7.5, sub="préstamos, roles")
    _box(d, 200, 28, 110, 20, "Zod + guard", "#FFFFFF", "#B9A5E8", 7.5)

    _box(d, 360, 20, 120, 195, "", "#FFF4E5", "#D9730D")
    d.add(String(420, 198, "Firebase", fontName="Sans-Bold", fontSize=10, fillColor=INK, textAnchor="middle"))
    d.add(String(420, 187, "Admin SDK + REST", fontName="Sans", fontSize=7.5, fillColor=MUTED, textAnchor="middle"))
    _box(d, 370, 130, 100, 44, "Authentication", "#FFFFFF", "#F2B880", 7.5, sub="correo/contraseña + roles")
    _box(d, 370, 56, 100, 60, "Firestore", "#FFFFFF", "#F2B880", 7.5, sub="books · loans · users")

    _arrow(d, 150, 118, 190, 118, both=True)
    d.add(String(170, 124, "HTTPS", fontName="Sans-Bold", fontSize=7, fillColor=MUTED, textAnchor="middle"))
    d.add(String(170, 106, "JSON", fontName="Sans", fontSize=7, fillColor=MUTED, textAnchor="middle"))
    _arrow(d, 320, 118, 360, 118, both=True)
    d.add(String(340, 124, "SDK", fontName="Sans-Bold", fontSize=7, fillColor=MUTED, textAnchor="middle"))
    d.add(String(240, 4, "La app nunca habla con Firebase: todo pasa por la API.", fontName="Sans-Italic", fontSize=8, fillColor=MUTED, textAnchor="middle"))
    return d


def diagram_sync() -> Drawing:
    d = Drawing(480, 250)
    steps = [
        (0, 185, "1. Solicitar libro", "sin conexión", "#EEF4FF", "#2563EB"),
        (165, 185, "2. Guardar en SQLite", "loans (pending) + outbox", "#EEF4FF", "#2563EB"),
        (330, 185, "3. Vuelve la red", "NetInfo / app activa", "#FFF4E5", "#D9730D"),
    ]
    for x, y, t, s, f, st in steps:
        _box(d, x, y, 150, 44, t, f, st, 8.5, bold=True, sub=s)
    _arrow(d, 150, 207, 165, 207)
    _arrow(d, 315, 207, 330, 207)
    _box(d, 330, 115, 150, 44, "4. POST /api/loans", "#F1ECFB", "#6B46C1", 8.5, bold=True, sub="clientRequestId (idempotente)")
    _arrow(d, 405, 185, 405, 159)
    _box(d, 165, 40, 150, 52, "5a. 200 / 201", "#E7F6EC", "#1A8F4C", 8.5, bold=True, sub="reemplazar la copia local")
    _box(d, 330, 40, 150, 52, "5b. 409 (conflicto)", "#FDECEC", "#C0392B", 8.5, bold=True, sub="marcar 'conflict' · gana el servidor")
    _arrow(d, 380, 115, 260, 92, "#1A8F4C")
    _arrow(d, 430, 115, 430, 92, "#C0392B")
    _box(d, 0, 40, 150, 52, "5c. Sin red / 5xx", "#FFF4E5", "#D9730D", 8.5, bold=True, sub="se conserva en la cola y se reintenta")
    _arrow(d, 345, 125, 75, 92, "#D9730D")
    d.add(String(240, 12, "Después se descargan los cambios del servidor: libros desde el cursor updatedSince y los préstamos.",
                 fontName="Sans-Italic", fontSize=7.8, fillColor=MUTED, textAnchor="middle"))
    return d


DIAGRAMS = {"architecture": diagram_architecture, "sync": diagram_sync}

# ───────────────────────────── Bloques ─────────────────────────────
def callout(kind: str, body: str):
    label, bg, fg = CALLOUTS[kind]
    paras = [Paragraph(f'<font color="{fg}"><b>{label}.</b></font> ' + inline(body.split("\n")[0]), S["callout"])]
    for extra in body.split("\n")[1:]:
        if extra.strip():
            paras.append(Paragraph(inline(extra), S["callout"]))
    t = Table([[paras]], colWidths=[17 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(fg)),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [t, Spacer(1, 8)]


def table_flowable(rows: list[list[str]]):
    ncols = len(rows[0])
    data = [[Paragraph(inline(c, "#FFFFFF"), S["cellh"]) for c in rows[0]]]
    for r in rows[1:]:
        r = (r + [""] * ncols)[:ncols]
        data.append([Paragraph(inline(c), S["cell"]) for c in r])
    weights = []
    for i in range(ncols):
        longest = max(len(re.sub(r"[`*]", "", r[i])) if i < len(r) else 0 for r in rows)
        weights.append(max(6, min(longest, 46)) ** 0.8)
    total = sum(weights)
    widths = [17 * cm * w / total for w in weights]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8FB")]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return [t, Spacer(1, 9)]


def parse(md: str):
    """Devuelve (metadatos, lista de flowables)."""
    meta: dict[str, str] = {}
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    if m:
        for line in m.group(1).split("\n"):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        md = md[m.end():]

    lines = md.split("\n")
    flow: list = []
    i = 0
    para: list[str] = []
    pending_caption: str | None = None

    def flush():
        nonlocal para
        if para:
            flow.append(Paragraph(inline(" ".join(s.strip() for s in para)), S["p"]))
            para = []

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush(); i += 1; continue
        if line.strip() == "<<<PAGEBREAK>>>":
            flush(); flow.append(PageBreak()); i += 1; continue

        d = re.fullmatch(r"\{\{(create|path|merge|append|delete|run|checkpoint):([^}]*)\}\}", line.strip())
        if d:
            flush()
            kind, arg = d.group(1), d.group(2)
            if kind == "checkpoint":
                i += 1; continue
            key, _, rel = arg.partition(":")
            rel = rel.split("|")[0]
            folder = FOLDERS.get(key, key)
            if kind == "create":
                path = ROOTS[key] / rel
                if not path.exists():
                    sys.exit(f"create: no existe {path}")
                ext = path.suffix.lstrip(".")
                lang = {"mts": "ts", "tsx": "ts", "json": "ts", "js": "ts"}.get(ext, ext)
                flow.append(CondPageBreak(4 * cm))
                flow.append(Paragraph(f"▸ <font color=\"#1A8F4C\">CREAR</font> · {escape(folder)}/{escape(rel)}", S["cap"]))
                flow.append(code_flowable(path.read_text(encoding="utf8").rstrip("\n"), lang))
            elif kind == "delete":
                flow.append(Paragraph(f"▸ <font color=\"#C0392B\">ELIMINAR</font> · <font name=\"Mono\" size=\"8.4\">{escape(folder)}/{escape(rel)}</font>", S["p"]))
            else:  # path / merge / append / run → el bloque de código que sigue
                labels = {"path": ("CREAR", "#1A8F4C"), "merge": ("AGREGAR A", "#B45309"),
                          "append": ("AGREGAR AL FINAL DE", "#B45309"), "run": ("TERMINAL", "#2563EB")}
                word, color = labels[kind]
                where = f"{folder}" if kind == "run" else f"{folder}/{rel}"
                pending_caption = f"▸ <font color=\"{color}\">{word}</font> · {escape(where)}"
            i += 1
            continue

        if line.startswith("```"):
            flush()
            lang = line[3:].strip()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            if pending_caption:
                flow.append(CondPageBreak(4 * cm))
                flow.append(Paragraph(pending_caption, S["cap"]))
                pending_caption = None
            flow.append(code_flowable("\n".join(buf), lang))
            continue

        inc = re.fullmatch(r"\{\{file:(.+)\}\}", line.strip())
        if inc:
            flush()
            label, code, lang = read_include(inc.group(1))
            flow.append(CondPageBreak(4 * cm))  # no dejar el nombre del archivo solo al final de la página
            flow.append(Paragraph(f"▸ {escape(label)}", S["cap"]))
            flow.append(code_flowable(code, lang))
            i += 1; continue

        dg = re.fullmatch(r"\{\{diagram:(\w+)\}\}", line.strip())
        if dg:
            flush(); flow += [DIAGRAMS[dg.group(1)](), Spacer(1, 10)]; i += 1; continue

        h = re.match(r"^(#{1,3}) (.+)$", line)
        if h:
            flush()
            level = len(h.group(1))
            if level == 1 and flow:
                flow.append(PageBreak())
            flow.append(Paragraph(inline(h.group(2)), S[f"h{level}"]))
            i += 1; continue

        if line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            flow += table_flowable(rows)
            continue

        cm_ = re.match(r"^> \[!(\w+)\] ?(.*)$", line)
        if cm_ and cm_.group(1) in CALLOUTS:
            flush()
            body = [cm_.group(2)]
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                body.append(lines[i][1:].strip()); i += 1
            flow += callout(cm_.group(1), "\n".join(body))
            continue

        lm = re.match(r"^(\s*)([-*]|\d+\.) (.*)$", line)
        if lm:
            flush()
            items = []
            while i < len(lines):
                m2 = re.match(r"^(\s*)([-*]|\d+\.) (.*)$", lines[i])
                if m2:
                    items.append([len(m2.group(1)) // 2, m2.group(2), m2.group(3)])
                elif lines[i].startswith("   ") and lines[i].strip() and items:
                    items[-1][2] += " " + lines[i].strip()
                else:
                    break
                i += 1
            for depth, marker, text in items:
                text = re.sub(r"^\[ \] ", "☐ ", text)
                text = re.sub(r"^\[x\] ", "☑ ", text)
                bullet = marker if marker[0].isdigit() else ("•" if depth == 0 else "–")
                st = ParagraphStyle("li", parent=S["li"], leftIndent=16 + depth * 14, bulletIndent=4 + depth * 14, bulletFontName="Sans-Bold")
                flow.append(Paragraph(inline(text), st, bulletText=bullet))
            flow.append(Spacer(1, 5))
            continue

        para.append(line); i += 1
    flush()
    return meta, flow


# ───────────────────────────── Documento ─────────────────────────────
class Doc(BaseDocTemplate):
    def __init__(self, filename: str, meta: dict[str, str]):
        super().__init__(filename, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2.2 * cm, bottomMargin=2 * cm,
                         title=meta.get("title", ""), author=meta.get("author", "Proyecto Biblioteca"), subject=meta.get("subtitle", ""))
        self.meta = meta
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=lambda c, d: None),
                               PageTemplate(id="body", frames=[frame], onPage=self.decorate)])

    def decorate(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(LINE); canv.setLineWidth(0.5)
        canv.line(2 * cm, A4[1] - 1.6 * cm, A4[0] - 2 * cm, A4[1] - 1.6 * cm)
        canv.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
        canv.setFont("Sans", 7.5); canv.setFillColor(MUTED)
        canv.drawString(2 * cm, A4[1] - 1.35 * cm, self.meta.get("header", ""))
        canv.drawRightString(A4[0] - 2 * cm, A4[1] - 1.35 * cm, "Desarrollo Móvil · Unidad 03")
        canv.drawString(2 * cm, 1.0 * cm, "Proyecto Biblioteca")
        canv.drawRightString(A4[0] - 2 * cm, 1.0 * cm, f"Página {doc.page}")
        canv.restoreState()

    def beforeDocument(self):
        self._n = 0  # claves de marcador estables entre las pasadas de multiBuild

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("h1", "h2"):
            level = 0 if flowable.style.name == "h1" else 1
            text = flowable.getPlainText()
            self._n = getattr(self, "_n", 0) + 1
            key = f"h-{self._n}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=level == 0)
            self.notify("TOCEntry", (level, text, self.page, key))


class Next(Flowable):
    """Cambia a la plantilla de páginas del cuerpo."""
    def wrap(self, *a): return (0, 0)
    def draw(self): pass


def cover(meta: dict[str, str]):
    items = [Spacer(1, 3.2 * cm),
             Paragraph(escape(meta.get("kicker", "")).upper(), ParagraphStyle("k", parent=base, fontName="Sans-Bold", fontSize=10, textColor=MUTED, spaceAfter=10)),
             Paragraph(escape(meta["title"]), S["cover_title"]), Spacer(1, 10),
             Paragraph(escape(meta.get("subtitle", "")), S["cover_sub"]), Spacer(1, 1.4 * cm)]
    rows = [[Paragraph(f"<b>{escape(k)}</b>", S["cell"]), Paragraph(inline(v), S["cell"])]
            for k, v in (kv.split("=", 1) for kv in meta.get("facts", "").split(";;") if kv)]
    if rows:
        t = Table(rows, colWidths=[4.2 * cm, 12.8 * cm])
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        items.append(t)
    return items


def build(src: Path, out: Path):
    meta, flow = parse(src.read_text(encoding="utf8"))
    doc = Doc(str(out), meta)
    toc = TableOfContents()
    toc.levelStyles = TOC_STYLES
    toc.dotsMinLevel = 0

    story = cover(meta)
    story += [PageBreak(), Paragraph("Contenido", S["toc_title"]), toc, PageBreak()]
    story += flow
    # La portada usa la plantilla sin encabezado; el resto, la del cuerpo.
    from reportlab.platypus.doctemplate import NextPageTemplate
    story.insert(0, NextPageTemplate("body"))
    # La primera página (portada) usa "cover" por ser la primera plantilla registrada.
    doc.multiBuild(story)
    print(f"✓ {out}  ({doc.page} páginas)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
