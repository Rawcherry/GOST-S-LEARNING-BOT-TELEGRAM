"""ГОСТ 2.305-2008 — изображения: виды, разрезы, сечения."""
import math

from draw import ACCENT, NOTE, S, THIN, Sheet, axis_sym

# ---------- шесть основных видов ----------
# Деталь: Г-образная (стойка слева 15 мм шириной, высота 30; основание 40×10), глубина 25,
# в основании вертикальное сквозное отверстие ⌀8 в точке x=28, y=12.5.
W, D, H, T, U = 40, 25, 30, 10, 15
HX, HY, HR = 28, 12.5, 4


def v_front(sh, ox, oy, mirror=False):
    def X(x):
        return ox + (W - x if mirror else x)
    sh.line([(X(0), oy), (X(W), oy), (X(W), oy + T), (X(U), oy + T), (X(U), oy + H), (X(0), oy + H)],
            closed=True)
    for dx in (-HR, HR):
        sh.seg(X(HX + dx), oy, X(HX + dx), oy + T, "hidden")
    sh.seg(X(HX), oy - 3, X(HX), oy + T + 3, "center")


def v_top(sh, ox, oy, show_hole=True, step_hidden=False):
    sh.rect(ox, oy, W, D)
    sh.seg(ox + U, oy, ox + U, oy + D, "hidden" if step_hidden else "main")
    if show_hole:
        sh.circle(ox + HX, oy + HY, HR)
    sh.seg(ox + HX - HR - 3, oy + HY, ox + HX + HR + 3, oy + HY, "center")
    sh.seg(ox + HX, oy + HY - HR - 3, ox + HX, oy + HY + HR + 3, "center")


def v_side(sh, ox, oy, from_left=True):
    sh.rect(ox, oy, D, H)
    # линия уступа (z = T): с левой стороны — невидима, с правой — видима
    sh.seg(ox, oy + T, ox + D, oy + T, "hidden" if from_left else "main")
    for dy in (-HR, HR):
        sh.seg(ox + HY + dy, oy, ox + HY + dy, oy + T, "hidden")
    sh.seg(ox + HY, oy - 3, ox + HY, oy + T + 3, "center")


def six_views(path):
    sh = Sheet(200, 125)
    gap = 12
    fx, fy = 50, 55                      # главный вид
    v_front(sh, fx, fy)                                  # вид спереди
    v_top(sh, fx, fy - gap - D)                          # вид сверху — под главным
    v_side(sh, fx + W + gap, fy, from_left=True)         # вид слева — справа от главного
    v_side(sh, fx - gap - D, fy, from_left=False)        # вид справа — слева от главного
    v_top(sh, fx, fy + H + gap, step_hidden=True)        # вид снизу — над главным
    v_front(sh, fx + W + gap + D + gap, fy, mirror=True)  # вид сзади — справа от вида слева
    labels = {  # номер: (x, y) — номера не по порядку стандарта
        "1": (fx + W / 2, fy + H + 4),
        "4": (fx + W + 8, fy - gap - D / 2),
        "2": (fx + W + gap + D / 2, fy + H + 4),
        "6": (fx - gap - D / 2, fy + H + 4),
        "5": (fx + W + 8, fy + H + gap + D / 2),
        "3": (fx + W + gap + D + gap + W / 2, fy + H + 4),
    }
    for k, (x, y) in labels.items():
        sh.label(x, y, k, circle=True, size=6)
    sh.save(path)


# ---------- сечения вала ----------
def shaft(sh, x0, y0, L=110, R=10):
    sh.rect(x0, y0 - R, L, 2 * R)
    sh.seg(x0 - 4, y0, x0 + L + 4, y0, "center")


def sections2(path):
    """Вал с вынесенным сечением (1) и планка с наложенным сечением (2)."""
    sh = Sheet(160, 97)
    y0, x0, R = 66, 12, 10
    L = 120
    sh.line([(x0, y0 - R), (x0 + L, y0 - R)])
    sh.line([(x0, y0 + R), (x0 + L, y0 + R)])
    sh.seg(x0, y0 - R, x0, y0 + R)
    sh.seg(x0 + L, y0 - R, x0 + L, y0 + R)
    sh.seg(x0 - 4, y0, x0 + L + 4, y0, "center")
    # паз (вид сверху)
    px = x0 + 18
    sh.line([(px + 3, y0 + 3), (px + 19, y0 + 3)])
    sh.line([(px + 3, y0 - 3), (px + 19, y0 - 3)])
    sh.circle(px + 3, y0, 3, a1=90, a2=270)
    sh.circle(px + 19, y0, 3, a1=-90, a2=90)
    sx = px + 11
    for sg in (1, -1):
        sh.seg(sx, y0 + sg * (R + 3), sx, y0 + sg * (R + 13), "cut")
        ya = y0 + sg * (R + 11)
        sh.seg(sx, ya, sx + 7, ya, "thin", t=0.45)
        sh.arrow_head(sx + 7, ya, 0, L=3.5, W=1.2)
        sh.text(sx + 10.5, ya + 2.5 * sg + 0.5, "А", size=4)
    # вынесенное сечение А–А (паз сверху, т.к. взгляд справа налево по стрелкам → паз виден)
    cx, cy = sx + 6, 16
    sh.text(cx, cy + R + 4.5, "А–А", size=4)
    a0 = math.degrees(math.asin(3 / R))
    n = 60
    pts = []
    for i in range(n + 1):
        a = math.radians(90 + a0 + (360 - 2 * a0) * i / n)
        pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
    yk = cy + R - 4
    ys = cy + math.sqrt(R * R - 9)
    pts += [(cx + 3, ys), (cx + 3, yk), (cx - 3, yk)]
    sh.hatch_poly(pts, 45, 2.2)
    sh.line(pts, closed=True)
    axis_sym(sh, cx, cy, R + 3)
    axis_sym(sh, cx, cy, R + 3, vertical=True)
    sh.label(cx - R - 10, cy, "1", circle=True)
    # наложенное сечение: плоская планка 110×16 (толщина 5) ниже вала
    by, bh, bt = 46, 16, 5
    bx0, bx1 = x0 + 60, x0 + L
    sh.rect(bx0, by - bh / 2 - 22, bx1 - bx0, bh)
    yb = by - 22
    hx = bx0 + 30
    sec = [(hx - bt / 2, yb - bh / 2), (hx + bt / 2, yb - bh / 2), (hx + bt / 2, yb + bh / 2),
           (hx - bt / 2, yb + bh / 2)]
    sh.white_poly(sec, z=1)
    sh.hatch_poly(sec, 45, 1.6)
    sh.line(sec, "thin", closed=True)
    axis_sym(sh, hx, yb, bh / 2 + 4, vertical=True)
    sh.leader(hx + 1.5, yb - 4, hx + 18, yb - 14)
    sh.label(hx + 20, yb - 16, "2", circle=True)
    sh.save(path)


def half_section(path):
    """Втулка с буртом: половина вида и половина разреза."""
    sh = Sheet(120, 90)
    cx, yb = 60, 10
    Rb, Hb = 28, 10      # бурт
    Rs, Hs = 18, 55      # цилиндр
    Ri = 10              # отверстие
    top = yb + Hb + Hs
    # левая половина — вид
    sh.line([(cx, yb), (cx - Rb, yb), (cx - Rb, yb + Hb), (cx - Rs, yb + Hb), (cx - Rs, top), (cx, top)])
    # правая половина — разрез
    poly = [(cx + Ri, yb), (cx + Rb, yb), (cx + Rb, yb + Hb), (cx + Rs, yb + Hb), (cx + Rs, top),
            (cx + Ri, top)]
    sh.hatch_poly(poly, 45, 3)
    sh.line(poly, closed=True)
    axis_sym(sh, cx, (yb + top) / 2, (top - yb) / 2 + 5, vertical=True)
    sh.leader(cx, top - 8, cx - 22, top + 8); sh.label(cx - 25, top + 9, "?", circle=True)
    sh.save(path)


def local_section(path):
    """Вал с местным разрезом у глухого отверстия."""
    sh = Sheet(150, 60)
    y0, x0, R, L = 30, 15, 12, 115
    sh.rect(x0, y0 - R, L, 2 * R)
    sh.seg(x0 - 4, y0, x0 + L + 4, y0, "center")
    hx = x0 + 70
    # местный разрез: волнистая граница, штриховка вокруг глухого отверстия ⌀8 глубиной 9
    area = [(hx - 12, y0 + R), (hx + 12, y0 + R)]
    wav = []
    for i in range(41):
        t = i / 40
        x = hx + 12 - 24 * t
        y = y0 + R - 13 + 1.2 * math.sin(2 * math.pi * 1.5 * t)
        wav.append((x, y))
    sec = [(hx - 12, y0 + R), (hx - 4, y0 + R), (hx - 4, y0 + R - 9), (hx + 4, y0 + R - 9),
           (hx + 4, y0 + R), (hx + 12, y0 + R)] + wav
    sh.hatch_poly(sec, 45, 2.5)
    sh.line(wav, "thin")
    sh.line([(hx - 4, y0 + R), (hx - 4, y0 + R - 9), (hx + 4, y0 + R - 9), (hx + 4, y0 + R)])
    axis_sym(sh, hx, y0 + R - 3, 9, vertical=True)
    sh.leader(hx + 9, y0 + 0.5, hx + 25, y0 - 20); sh.label(hx + 27, y0 - 22, "?", circle=True)
    sh.save(path)


def rib(path):
    """Опора с ребром жёсткости в продольном разрезе: А — ребро не заштриховано, Б — заштриховано."""
    sh = Sheet(170, 70)
    for i, lab in enumerate("АБ"):
        ox = 12 + i * 85
        # основание и стойка (разрез по плоскости симметрии, проходит вдоль ребра)
        base = [(ox, 10), (ox + 70, 10), (ox + 70, 18), (ox, 18)]
        post = [(ox, 18), (ox + 10, 18), (ox + 10, 60), (ox, 60)]
        ribp = [(ox + 10, 18), (ox + 45, 18), (ox + 10, 50)]
        sh.hatch_poly(base, 45, 3)
        sh.hatch_poly(post, 45, 3)
        if lab == "Б":
            sh.hatch_poly(ribp, 45, 3)
        sh.line([(ox, 10), (ox + 70, 10), (ox + 70, 18), (ox + 45, 18), (ox + 10, 50), (ox + 10, 60),
                 (ox, 60)], closed=True)
        if lab == "А":
            sh.seg(ox + 10, 18, ox + 45, 18)      # граница ребра и основания
            sh.seg(ox + 10, 18, ox + 10, 50)      # граница ребра и стойки
        sh.label(ox + 35, 4, lab)
    sh.save(path)


def detail_element(path):
    """Выносной элемент: окружность на изображении и увеличенный фрагмент."""
    sh = Sheet(160, 75)
    # вал с канавкой
    y0, x0, R = 40, 10, 12
    sh.line([(x0, y0 + R), (x0 + 40, y0 + R), (x0 + 40, y0 + R - 2), (x0 + 44, y0 + R - 2),
             (x0 + 44, y0 + R), (x0 + 80, y0 + R)])
    sh.line([(x0, y0 - R), (x0 + 80, y0 - R)])
    sh.seg(x0, y0 - R, x0, y0 + R)
    sh.seg(x0 + 80, y0 - R, x0 + 80, y0 + R)
    sh.seg(x0 - 4, y0, x0 + 84, y0, "center")
    sh.circle(x0 + 42, y0 + R - 1, 6, "thin")
    a = math.radians(60)
    lx, ly = x0 + 42 + 6 * math.cos(a), y0 + R - 1 + 6 * math.sin(a)
    sh.seg(lx, ly, lx + 6, ly + 10, "thin")
    sh.seg(lx + 6, ly + 10, lx + 14, ly + 10, "thin")
    sh.text(lx + 10, ly + 13, "Б", size=4.2)
    # увеличенный фрагмент 4:1
    k = 4
    fx, fy = 112, 22
    sh.text(fx + 18, fy + 40, "Б (4:1)", size=4.2)
    pts = [(fx - 5, fy + 20), (fx + 10, fy + 20), (fx + 10, fy + 20 - 2 * k),
           (fx + 10 + 4 * k, fy + 20 - 2 * k), (fx + 10 + 4 * k, fy + 20), (fx + 40, fy + 20)]
    sh.line(pts)
    sh.wavy(fx - 5, fy + 20, fx - 5, fy + 4, amp=1, waves=1.5)
    sh.wavy(fx + 40, fy + 20, fx + 40, fy + 4, amp=1, waves=1.5)
    sh.wavy(fx - 5, fy + 4, fx + 40, fy + 4, amp=1, waves=3)
    sh.save(path)


def cut_designation(path):
    """Ступенчатый разрез: линия сечения с перегибами, стрелки, буквы."""
    sh = Sheet(150, 85)
    ox, oy, w, h = 25, 15, 100, 55
    sh.rect(ox, oy, w, h)
    holes = [(ox + 25, oy + 38), (ox + 75, oy + 17)]
    for (x, y) in holes:
        sh.circle(x, y, 6)
        axis_sym(sh, x, y, 9)
        axis_sym(sh, x, y, 9, vertical=True)
    # линия разреза: горизонтально через первое отверстие, перегиб, через второе
    y1, y2, xm = holes[0][1], holes[1][1], ox + 50
    sh.seg(ox - 13, y1, ox - 3, y1, "cut")
    sh.seg(ox + w + 3, y2, ox + w + 13, y2, "cut")
    sh.line([(xm - 5, y1), (xm, y1), (xm, y1 - 5)], "cut")
    sh.line([(xm, y2 + 5), (xm, y2), (xm + 5, y2)], "cut")
    for (x, y) in ((ox - 11, y1), (ox + w + 11, y2)):
        sh.seg(x, y, x, y - 8, "thin", t=0.45)
        sh.arrow_head(x, y - 8, 270, L=3.5, W=1.2)
    sh.text(ox - 15, y1 - 6, "В", size=4.2)
    sh.text(ox + w + 15, y2 - 6, "В", size=4.2)
    sh.save(path)


FIGS = {
    "305_six_views.png": six_views,
    "305_sections.png": sections2,
    "305_half.png": half_section,
    "305_local.png": local_section,
    "305_rib.png": rib,
    "305_detail.png": detail_element,
    "305_stepped.png": cut_designation,
}
