"""ГОСТ 2.303-68 — линии."""
from draw import NOTE, S, THIN, Sheet, axis_sym

# Порядок на картинке намеренно не совпадает с таблицей 1 стандарта
TYPES_ORDER = [
    ("hidden", "Штриховая"),
    ("main", "Сплошная толстая основная"),
    ("phantom", "Штрихпунктирная с двумя точками тонкая"),
    ("wavy", "Сплошная волнистая"),
    ("center", "Штрихпунктирная тонкая"),
    ("cut", "Разомкнутая"),
    ("thin", "Сплошная тонкая"),
    ("thick_center", "Штрихпунктирная утолщённая"),
    ("zigzag", "Сплошная тонкая с изломами"),
]


def line_types(path):
    sh = Sheet(150, 112)
    y = 104
    for i, (kind, _) in enumerate(TYPES_ORDER, 1):
        sh.label(12, y, str(i), circle=True, size=4.5)
        if kind == "wavy":
            sh.wavy(25, y, 140, y, amp=1.3, waves=4)
        elif kind == "zigzag":
            sh.zigzag(25, y, 140, y, n_breaks=2, h=5)
        elif kind == "cut":
            sh.seg(25, y, 41, y, "cut")
            sh.seg(124, y, 140, y, "cut")
        else:
            sh.seg(25, y, 140, y, kind)
        y -= 12
    sh.save(path)


def part_lines(path):
    """Деталь с разными линиями и выносками-номерами."""
    sh = Sheet(150, 90)
    x0, y0, w, h = 25, 22, 85, 36
    xb = x0 + w  # линия обрыва справа
    sh.line([(xb, y0), (x0, y0), (x0, y0 + h), (xb, y0 + h)])
    sh.wavy(xb, y0, xb, y0 + h, amp=1.2, waves=2)
    hx = x0 + 30
    sh.seg(hx - 7, y0 + h, hx - 7, y0 + 12, "hidden")
    sh.seg(hx + 7, y0 + h, hx + 7, y0 + 12, "hidden")
    sh.seg(hx - 7, y0 + 12, hx + 7, y0 + 12, "hidden")
    axis_sym(sh, hx, y0 + 23, 18, vertical=True)
    sh.dim_linear((x0, y0), (hx, y0), -11, "30", ext=2)
    # выноски
    sh.leader(x0, y0 + 25, x0 - 13, y0 + 45); sh.label(x0 - 15, y0 + 48, "1", circle=True)
    sh.leader(hx - 7, y0 + 28, hx - 18, y0 + 52); sh.label(hx - 20, y0 + 55, "2", circle=True)
    sh.leader(hx, y0 + h + 4, hx + 12, y0 + 55); sh.label(hx + 14, y0 + 58, "3", circle=True)
    sh.leader(xb + 1, y0 + 12, xb + 14, y0 + 30); sh.label(xb + 16, y0 + 33, "4", circle=True)
    sh.leader(x0 + 20, y0 - 11, x0 + 45, y0 - 17); sh.label(x0 + 48, y0 - 17, "5", circle=True)
    sh.leader(hx, y0 - 5, hx + 30, y0 - 7); sh.label(hx + 33, y0 - 7, "6", circle=True)
    sh.save(path)


def centers_big(path):
    """Центровые линии окружности ⌀28: верный вариант и ошибки (п. 10, 11)."""
    sh = Sheet(130, 55)
    R = 14
    for i, lab in enumerate("АБВ"):
        cx, cy = 22 + i * 43, 30
        sh.circle(cx, cy, R)
        if lab == "А":    # пересекаются и заканчиваются штрихами
            axis_sym(sh, cx, cy, R + 4)
            axis_sym(sh, cx, cy, R + 4, vertical=True)
        elif lab == "Б":  # пересекаются промежутками — в центре пусто
            for vert in (False, True):
                for sg in (1, -1):
                    a0, a1 = 2.0, 9.0
                    b0, b1 = 12.0, R + 4
                    for (u, v) in ((a0, a1), (b0, b1)):
                        if vert:
                            sh.seg(cx, cy + sg * u, cx, cy + sg * v, "thin")
                        else:
                            sh.seg(cx + sg * u, cy, cx + sg * v, cy, "thin")
                    d = 10.5
                    if vert:
                        sh.seg(cx, cy + sg * (d - 0.5), cx, cy + sg * (d + 0.5), "thin")
                    else:
                        sh.seg(cx + sg * (d - 0.5), cy, cx + sg * (d + 0.5), cy, "thin")
        else:             # сплошные тонкие у большой окружности
            sh.seg(cx - R - 4, cy, cx + R + 4, cy, "thin")
            sh.seg(cx, cy - R - 4, cx, cy + R + 4, "thin")
        sh.label(cx, 5, lab)
    sh.text(65, 52, "Окружность ⌀28 в масштабе 1:1", size=3.3, color=NOTE)
    sh.save(path)


def centers_small(path):
    """Окружность диаметром менее 12 мм: какими линиями центровые."""
    sh = Sheet(140, 45)
    r = 4
    for i, (lab, kind) in enumerate((("А", "center"), ("Б", "thin"), ("В", "main"))):
        cx, cy = 25 + i * 45, 25
        sh.circle(cx, cy, r)
        sh.seg(cx - r - 4, cy, cx + r + 4, cy, kind)
        sh.seg(cx, cy - r - 4, cx, cy + r + 4, kind)
        sh.label(cx, 6, lab)
    sh.text(70, 41, "Отверстие ⌀8 в масштабе 1:1", size=3.3, color=NOTE)
    sh.save(path)


def cut_line(path):
    """Линия сечения: разомкнутая со стрелками и буквами."""
    sh = Sheet(150, 70)
    # вал
    sh.rect(20, 25, 110, 20)
    sh.seg(15, 35, 135, 35, "center")
    x = 75
    sh.seg(x, 49, x, 61, "cut")
    sh.seg(x, 21, x, 9, "cut")
    for (y, d) in ((59, 1), (11, -1)):
        sh.seg(x, y, x - 9, y, "thin", t=0.45)
        sh.arrow_head(x - 9, y, 180, L=4, W=1.4)
        sh.text(x - 13, y + 3.5 * d * 0 + 3.5, "А", size=4.5)
    sh.leader(x + 0.5, 56, x + 18, 64); sh.label(x + 21, 65, "?", circle=True)
    sh.save(path)


FIGS = {
    "303_types.png": line_types,
    "303_part.png": part_lines,
    "303_centers.png": centers_big,
    "303_centers_small.png": centers_small,
    "303_cut.png": cut_line,
}
