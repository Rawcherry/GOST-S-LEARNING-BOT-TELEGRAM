"""ГОСТ 2.307-2011 — нанесение размеров и предельных отклонений."""
import math

from draw import ACCENT, INK, NOTE, Sheet, axis_sym


def brace_v(sh, x, y1, y2, lab):
    """Синяя пояснительная скобка с буквой (не элемент чертежа)."""
    sh.seg(x, y1, x, y2, "thin", t=0.3, color=NOTE)
    sh.seg(x - 1.2, y1, x + 1.2, y1, "thin", t=0.3, color=NOTE)
    sh.seg(x - 1.2, y2, x + 1.2, y2, "thin", t=0.3, color=NOTE)
    sh.label(x + 5, (y1 + y2) / 2, lab, size=4.5)


def layout(path):
    sh = Sheet(150, 85)
    x0, y0, w, h = 30, 45, 80, 30
    sh.rect(x0, y0, w, h)
    sh.circle(x0 + 55, y0 + 15, 6)
    axis_sym(sh, x0 + 55, y0 + 15, 9)
    axis_sym(sh, x0 + 55, y0 + 15, 9, vertical=True)
    # первая размерная линия (до отверстия), вторая — габарит
    sh.dim_linear((x0, y0), (x0 + 55, y0 + 6), -12, "55", ext=3)
    sh.dim_linear((x0, y0), (x0 + w, y0), -24, "80", ext=3)
    # пояснения
    brace_v(sh, x0 + w + 8, y0 - 12, y0, "а")
    brace_v(sh, x0 + w + 8, y0 - 24, y0 - 12, "б")
    sh.seg(x0 - 6, y0 - 27, x0 - 6, y0 - 24, "thin", t=0.3, color=NOTE)
    sh.label(x0 - 11, y0 - 25.5, "в", size=4.5)
    sh.seg(x0 + w, y0, x0 + w + 9, y0, "thin", t=0.25, color=NOTE)
    sh.seg(x0 + 55, y0 - 12, x0 + w + 9, y0 - 12, "thin", t=0.25, color=NOTE)
    sh.seg(x0 + w, y0 - 24, x0 + w + 9, y0 - 24, "thin", t=0.25, color=NOTE)
    sh.seg(x0, y0 - 27, x0 - 7, y0 - 27, "thin", t=0.25, color=NOTE)
    sh.seg(x0, y0 - 24, x0 - 7, y0 - 24, "thin", t=0.25, color=NOTE)
    sh.save(path)


def tol_text(sh, x, y, nom, up=None, lo=None, sym=None, size=4.5, extra=None):
    """Размер с отклонениями: nom, верхнее/нижнее (строки) или sym='±0,23'."""
    sh.text(x, y, nom, size=size, ha="right")
    if sym:
        sh.text(x + 0.3, y, sym, size=size, ha="left")
    elif up is not None or lo is not None:
        if up is not None:
            sh.text(x + 0.5, y + size * 0.55, up, size=size * 0.75, ha="left")
        if lo is not None:
            sh.text(x + 0.5, y - size * 0.45, lo, size=size * 0.75, ha="left")
    if extra:
        sh.text(x + 0.3, y, extra, size=size, ha="left")


def tolerances(path):
    sh = Sheet(150, 50)
    items = [("А", dict(nom="60", sym="±0,23")),
             ("Б", dict(nom="60", up="+0,19", lo="0")),
             ("В", dict(nom="60", up="+0,19")),
             ("Г", dict(nom="18", extra="H7(+0,018)", size=4.0))]
    for i, (lab, kw) in enumerate(items):
        x = 16 + i * 33
        y = 30
        sh.seg(x - 12, y - 4, x + 14, y - 4, "thin")
        sh.arrow_head(x - 12, y - 4, 180)
        sh.arrow_head(x + 14, y - 4, 0)
        tol_text(sh, x, y + 0.5, **kw)
        sh.label(x, 12, lab)
    sh.save(path)


def closed_chain(path):
    sh = Sheet(150, 60)
    x0, y0 = 15, 35
    segs = [25, 40, 30]
    xs = [x0]
    for s_ in segs:
        xs.append(xs[-1] + s_)
    # ступенчатая деталь
    hs = [12, 18, 10]
    pts = [(x0, y0)]
    for i, s_ in enumerate(segs):
        pts += [(xs[i], y0 + hs[i]), (xs[i + 1], y0 + hs[i])]
    pts += [(xs[-1], y0)]
    sh.line(pts, closed=True)
    for i, s_ in enumerate(segs):
        sh.dim_linear((xs[i], y0), (xs[i + 1], y0), -8, str(s_ * 1), ext=2)
    sh.dim_linear((xs[0], y0), (xs[-1], y0), -18, str(sum(segs)), ext=2)
    sh.save(path)


def holes(path):
    sh = Sheet(110, 85)
    cx, cy = 50, 42
    sh.circle(cx, cy, 32)
    sh.circle(cx, cy, 10)
    sh.circle(cx, cy, 22, "center", t=0.35)
    axis_sym(sh, cx, cy, 36)
    axis_sym(sh, cx, cy, 36, vertical=True)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        px, py = cx + 22 * math.cos(a), cy + 22 * math.sin(a)
        sh.circle(px, py, 4)
        sh.seg(px - 6.5 * math.cos(a), py - 6.5 * math.sin(a), px + 6.5 * math.cos(a),
               py + 6.5 * math.sin(a), "thin", t=0.3)
    # выноска от отверстия в I четверти
    a = math.radians(45)
    px, py = cx + 22 * math.cos(a) + 4 * math.cos(a), cy + 22 * math.sin(a) + 4 * math.sin(a)
    sh.seg(px, py, px + 10, py + 10, "thin")
    sh.arrow_head(px, py, 225)
    sh.seg(px + 10, py + 10, px + 34, py + 10, "thin")
    sh.text(px + 22, py + 13, "4 отв. ⌀8", size=3.8)
    sh.save(path)


def chamfer(path):
    sh = Sheet(130, 60)
    y0, x0, R, L, c = 28, 15, 14, 80, 3
    xe = x0 + L
    sh.line([(x0, y0 - R), (xe - c, y0 - R), (xe, y0 - R + c), (xe, y0 + R - c), (xe - c, y0 + R),
             (x0, y0 + R)])
    sh.seg(x0, y0 - R, x0, y0 + R)
    sh.seg(xe - c, y0 - R, xe - c, y0 + R)
    sh.seg(x0 - 4, y0, xe + 4, y0, "center")
    # размер фаски
    sh.seg(xe - c, y0 + R, xe - c, y0 + R + 10, "thin")
    sh.seg(xe - c - 12, y0 + R + 8, xe + 18, y0 + R + 8, "thin")
    sh.arrow_head(xe - c, y0 + R + 8, 0)
    sh.seg(xe, y0 + R - c, xe, y0 + R + 10, "thin")
    sh.arrow_head(xe, y0 + R + 8, 180)
    sh.text(xe + 10, y0 + R + 10.5, "?", size=4.5, color=ACCENT, bold=True)
    sh.text(65, 6, "Фаска 3 мм под углом 45° на валу", size=3.2, color=NOTE)
    sh.save(path)


def signs(path):
    """Условные знаки при размерных числах: 1 — квадрат, 2 — конусность, 3 — сфера/радиус."""
    sh = Sheet(160, 60)
    # 1: конец вала квадратного сечения (вид), размер с □
    x0 = 12
    sh.rect(x0, 18, 40, 16)
    sh.seg(x0, 18, x0 + 40, 34, "thin")      # диагонали — плоская поверхность
    sh.seg(x0, 34, x0 + 40, 18, "thin")
    sh.dim_linear((x0 + 40, 18), (x0 + 40, 34), 9, "□16", orient="v", size=3.6)
    sh.label(x0 + 20, 8, "1", circle=True)
    # 2: конус с конусностью
    cx0 = 72
    sh.line([(cx0, 16), (cx0 + 40, 21), (cx0 + 40, 31), (cx0, 36)], closed=True)
    sh.seg(cx0 - 4, 26, cx0 + 44, 26, "center")
    # знак конусности над осью на полке: треугольник остриём к вершине (вправо)
    tx, ty = cx0 + 12, 44
    sh.line([(tx, ty - 1.6), (tx + 6, ty), (tx, ty + 1.6)], "thin", closed=True)
    sh.text(tx + 12, ty + 0.3, "1:4", size=3.6)
    sh.seg(tx - 3, ty - 3, tx + 18, ty - 3, "thin")
    sh.seg(tx + 5, ty - 3, cx0 + 22, 33.5, "thin")
    sh.label(cx0 + 20, 8, "2", circle=True)
    # 3: сфера (шаровой конец)
    sx = 140
    sh.circle(sx, 26, 11)
    axis_sym(sh, sx, 26, 14)
    axis_sym(sh, sx, 26, 14, vertical=True)
    a = math.radians(40)
    sh.seg(sx, 26, sx + 11 * math.cos(a), 26 + 11 * math.sin(a), "thin")
    sh.arrow_head(sx + 11 * math.cos(a), 26 + 11 * math.sin(a), 40)
    sh.seg(sx + 11 * math.cos(a), 26 + 11 * math.sin(a), sx + 14, 46, "thin")
    sh.text(sx + 11, 49, "R11", size=3.6)
    sh.label(sx, 8, "3", circle=True)
    sh.save(path)


def ticks(path):
    """Цепочка мелких размеров: стрелки заменены засечками под 45° и точками."""
    sh = Sheet(140, 50)
    x0, y0 = 20, 15
    xs = [x0, x0 + 4, x0 + 8, x0 + 12, x0 + 50, x0 + 54, x0 + 58, x0 + 62]
    sh.rect(x0, y0, 100, 10)
    yd = y0 + 20
    for x in xs[:4]:
        sh.seg(x, y0 + 10, x, yd + 2, "thin")
        sh.seg(x - 1.2, yd - 1.2, x + 1.2, yd + 1.2, "thin", t=0.6)
    sh.seg(xs[0] - 3, yd, xs[3] + 3, yd, "thin")
    for x in xs[4:]:
        sh.seg(x, y0 + 10, x, yd + 2, "thin")
        sh.ax.add_patch(__import__("matplotlib").patches.Circle((x, yd), 0.6, fc=INK, ec="none", zorder=5))
    sh.seg(xs[4] - 3, yd, xs[7] + 3, yd, "thin")
    for i in range(3):
        sh.text(xs[i] + 2, yd + 2.4, "4", size=2.8)
        sh.text(xs[4 + i] + 2, yd + 2.4, "4", size=2.8)
    sh.label(x0 + 6, 8, "А", size=4.5)
    sh.label(x0 + 56, 8, "Б", size=4.5)
    sh.save(path)


FIGS = {
    "307_layout.png": layout,
    "307_tol.png": tolerances,
    "307_chain.png": closed_chain,
    "307_holes.png": holes,
    "307_chamfer.png": chamfer,
    "307_signs.png": signs,
    "307_ticks.png": ticks,
}
