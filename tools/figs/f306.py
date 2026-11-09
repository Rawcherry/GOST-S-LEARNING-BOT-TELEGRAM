"""ГОСТ 2.306-68 — обозначения материалов (штриховка)."""
from draw import NOTE, Sheet, axis_sym


def rubber_metal(path):
    """Резинометаллический шарнир (сайлентблок), продольный разрез верхней половины."""
    sh = Sheet(150, 70)
    x0, x1 = 30, 110
    cy = 12
    r_in, r1, r2, r3 = 8, 13, 24, 29     # внутренняя втулка 8–13, резина 13–24, наружная 24–29
    inner = [(x0 - 6, cy + r_in), (x1 + 6, cy + r_in), (x1 + 6, cy + r1), (x0 - 6, cy + r1)]
    rubber = [(x0 + 4, cy + r1), (x1 - 4, cy + r1), (x1 - 4, cy + r2), (x0 + 4, cy + r2)]
    outer = [(x0, cy + r2), (x1, cy + r2), (x1, cy + r3), (x0, cy + r3)]
    sh.hatch_poly(inner, 45, 2.0)
    sh.hatch_poly(rubber, 45, 3.2)
    sh.hatch_poly(rubber, -45, 3.2)
    sh.hatch_poly(outer, -45, 2.0)
    for p in (inner, rubber, outer):
        sh.line(p, closed=True)
    sh.seg(x0 - 12, cy, x1 + 12, cy, "center")
    sh.leader(x1 + 2, cy + 10.5, x1 + 18, cy + 4); sh.label(x1 + 21, cy + 4, "1", circle=True)
    sh.leader(x1 - 10, cy + 18, x1 + 18, cy + 22); sh.label(x1 + 21, cy + 22, "2", circle=True)
    sh.leader(x1 - 5, cy + 27, x1 + 18, cy + 40); sh.label(x1 + 21, cy + 40, "3", circle=True)
    sh.text(70, 64, "Резинометаллический шарнир, разрез (половина)", size=3.3, color=NOTE)
    sh.save(path)


def materials(path):
    sh = Sheet(120, 50)
    for i, lab in enumerate("АБ"):
        ox = 15 + i * 55
        sq = [(ox, 10), (ox + 35, 10), (ox + 35, 40), (ox, 40)]
        sh.hatch_poly(sq, 45, 3)
        if lab == "Б":
            sh.hatch_poly(sq, -45, 3)
        sh.line(sq, closed=True)
        sh.label(ox + 17.5, 4, lab)
    sh.save(path)


def adjacent(path):
    """Смежные сечения двух деталей: А — одинаковая штриховка, Б — встречная, В — другой шаг."""
    sh = Sheet(170, 55)
    for i, lab in enumerate("АБВ"):
        ox = 10 + i * 55
        p1 = [(ox, 12), (ox + 22, 12), (ox + 22, 42), (ox, 42)]
        p2 = [(ox + 22, 12), (ox + 44, 12), (ox + 44, 42), (ox + 22, 42)]
        sh.hatch_poly(p1, 45, 3)
        if lab == "А":
            sh.hatch_poly(p2, 45, 3)
        elif lab == "Б":
            sh.hatch_poly(p2, -45, 3)
        else:
            sh.hatch_poly(p2, 45, 1.5)
        sh.line(p1, closed=True)
        sh.line(p2, closed=True)
        sh.label(ox + 22, 5, lab)
    sh.text(85, 51, "Сечения двух разных металлических деталей", size=3.3, color=NOTE)
    sh.save(path)


def angle45(path):
    """Деталь с контуром под 45°: штриховка 45° (А) и 60° (Б)."""
    sh = Sheet(150, 60)
    for i, (lab, ang) in enumerate((("А", 45), ("Б", 60))):
        ox = 15 + i * 70
        poly = [(ox, 10), (ox + 30, 10), (ox + 60, 40), (ox + 30, 40)]   # стороны под 45°
        sh.hatch_poly(poly, ang, 3)
        sh.line(poly, closed=True)
        sh.label(ox + 30, 4, lab)
    sh.text(75, 53, "Сечение детали, боковые стороны контура — под 45° к рамке", size=3.2, color=NOTE)
    sh.save(path)


def narrow(path):
    """Узкие сечения (менее 2 мм) зачернены с просветом."""
    sh = Sheet(140, 60)
    x0, x1 = 20, 120
    # две тонкие пластины (1,5 мм) друг на друге с просветом
    sh.fill_poly([(x0, 30), (x1, 30), (x1, 31.5), (x0, 31.5)])
    sh.fill_poly([(x0, 32.5), (x1, 32.5), (x1, 34), (x0, 34)])
    # выноска к просвету
    sh.leader(80, 32, 95, 48); sh.label(97, 50, "?", circle=True)
    sh.text(70, 14, "Две прокладки толщиной 1,5 мм в разрезе (масштаб 1:1)", size=3.2, color=NOTE)
    sh.save(path)


def big_area(path):
    sh = Sheet(150, 70)
    ox, oy, w, h = 20, 10, 110, 50
    poly = [(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)]
    inner = [(ox + 6, oy + 6), (ox + w - 6, oy + 6), (ox + w - 6, oy + h - 6), (ox + 6, oy + h - 6)]
    sh.hatch_poly(poly, 45, 3)
    sh.white_poly(inner, z=2.4)
    sh.line(poly, closed=True)
    axis_sym(sh, ox + w / 2, oy + h / 2, w / 2 + 5)
    sh.save(path)


FIGS = {
    "306_rubber_metal.png": rubber_metal,
    "306_materials.png": materials,
    "306_adjacent.png": adjacent,
    "306_angle.png": angle45,
    "306_narrow.png": narrow,
    "306_big.png": big_area,
}
