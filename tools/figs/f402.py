"""ГОСТ 2.402-68 — условные изображения зубчатых колёс."""
import math

from draw import NOTE, Sheet

# m = 3, z = 18: d = 54, da = 60, df = 46.5
RA, RP, RF = 30, 27, 23.25
B = 20          # ширина венца
RB = 10         # отверстие


def gear_section(sh, x0, cy, root_main=True):
    """Разрез колеса плоскостью через ось (ось горизонтальна). x0 — левый торец."""
    x1 = x0 + B
    for sgn in (1, -1):
        # тело колеса заштриховано до линии впадин
        poly = [(x0, cy + sgn * RB), (x1, cy + sgn * RB), (x1, cy + sgn * RF), (x0, cy + sgn * RF)]
        sh.hatch_poly(poly, 45, 3)
        sh.seg(x0, cy + sgn * RA, x1, cy + sgn * RA)                      # вершины
        sh.seg(x0 - 3, cy + sgn * RP, x1 + 3, cy + sgn * RP, "center")    # делительная
        sh.seg(x0, cy + sgn * RF, x1, cy + sgn * RF, "main" if root_main else "thin")
        sh.seg(x0, cy + sgn * RB, x1, cy + sgn * RB)                      # отверстие
        sh.seg(x0, cy + sgn * RB, x0, cy + sgn * RA)
        sh.seg(x1, cy + sgn * RB, x1, cy + sgn * RA)
    sh.seg(x0 - 5, cy, x1 + 5, cy, "center")


def gear_view(sh, cx, cy, root="thin"):
    sh.circle(cx, cy, RA)
    sh.circle(cx, cy, RP, "center")
    if root:
        sh.circle(cx, cy, RF, root)
    sh.circle(cx, cy, RB)
    # шпоночный паз
    sh.line([(cx - 3, cy + math.sqrt(RB ** 2 - 9)), (cx - 3, cy + 13), (cx + 3, cy + 13),
             (cx + 3, cy + math.sqrt(RB ** 2 - 9))])
    sh.seg(cx - RA - 4, cy, cx + RA + 4, cy, "center")
    sh.seg(cx, cy - RA - 4, cx, cy + RA + 4, "center")


def gear_two_views(path):
    sh = Sheet(150, 80)
    cy = 40
    gear_section(sh, 25, cy)
    gear_view(sh, 100, cy)
    # метки
    sh.leader(30, cy + RA, 20, cy + RA + 6); sh.label(17, cy + RA + 7, "1", circle=True)
    sh.leader(48, cy + RP, 60, cy + RP + 9); sh.label(63, cy + RP + 10, "2", circle=True)
    sh.leader(40, cy - RF, 25, cy - RF - 8); sh.label(21, cy - RF - 10, "3", circle=True)
    a = math.radians(-35)
    sh.leader(100 + RF * math.cos(a), cy + RF * math.sin(a), 135, cy - 30)
    sh.label(138, cy - 32, "4", circle=True)
    sh.save(path)


def gear_helical(path):
    sh = Sheet(150, 75)
    cy, x0 = 37, 50
    x1 = x0 + B + 10
    for sgn in (1, -1):
        sh.seg(x0, cy + sgn * RA, x1, cy + sgn * RA)
        sh.seg(x0 - 3, cy + sgn * RP, x1 + 3, cy + sgn * RP, "center")
    sh.seg(x0, cy - RA, x0, cy + RA)
    sh.seg(x1, cy - RA, x1, cy + RA)
    sh.seg(x0 - 5, cy, x1 + 5, cy, "center")
    # три тонкие линии направления зубьев
    for k in (-6, 0, 6):
        sh.seg(x0 + 9 + k, cy - 12, x0 + 21 + k, cy + 12, "thin")
    sh.leader(x0 + 21 + 6, cy + 12, x1 + 25, cy + 22)
    sh.label(x1 + 28, cy + 24, "?", circle=True)
    sh.text(20, 70, "Вид колеса (без разреза)", size=3.4, color=NOTE, ha="left")
    sh.save(path)


def gear_mesh(path):
    """Внешнее зацепление в разрезе через оси (увеличенный фрагмент зоны зацепления)."""
    sh = Sheet(100, 60)
    m = 6  # условный модуль на картинке (крупно, чтобы линии не сливались)
    yp = 30                                   # общая делительная линия
    g1 = dict(ra=yp - m, rf=yp + 1.25 * m)    # колесо 1 сверху: вершины ниже делительной
    g2 = dict(ra=yp + m, rf=yp - 1.25 * m)    # колесо 2 снизу: вершины выше делительной
    x0, x1 = 35, 60
    y_top, y_bot = 56, 4
    sh.hatch_poly([(x0, g1["rf"]), (x1, g1["rf"]), (x1, y_top), (x0, y_top)], 45, 3)
    sh.hatch_poly([(x0, y_bot), (x1, y_bot), (x1, g2["rf"]), (x0, g2["rf"])], -45, 3)
    sh.seg(x0, g1["ra"], x1, g1["ra"])                 # вершины ведущего — видимы
    sh.seg(x0, g1["rf"], x1, g1["rf"])
    sh.seg(x0, g2["ra"], x1, g2["ra"], "hidden")       # вершины ведомого — за зубом ведущего
    sh.seg(x0, g2["rf"], x1, g2["rf"])
    sh.seg(x0 - 6, yp, x1 + 6, yp, "center")
    sh.seg(x0, g1["ra"], x0, y_top); sh.seg(x1, g1["ra"], x1, y_top)
    sh.seg(x0, y_bot, x0, g2["ra"]); sh.seg(x1, y_bot, x1, g2["ra"])
    sh.wavy(x0 - 3, y_top, x1 + 3, y_top, amp=0.8, waves=2)
    sh.wavy(x0 - 3, y_bot, x1 + 3, y_bot, amp=0.8, waves=2)
    sh.text(x1 + 6, 48, "Колесо 1", size=3.2, ha="left", color=NOTE)
    sh.text(x1 + 6, 12, "Колесо 2", size=3.2, ha="left", color=NOTE)
    sh.leader(x0 + 4, g1["ra"], 15, 14); sh.label(12, 12, "1", circle=True)
    sh.leader(x0 + 12, g2["ra"], 15, 46); sh.label(12, 48, "2", circle=True)
    sh.save(path)


def chain_drive(path):
    sh = Sheet(160, 80)
    c1, r1 = (40, 40), 18
    c2, r2 = (120, 40), 26
    for (cx, cy), r in ((c1, r1), (c2, r2)):
        sh.circle(cx, cy, r + 3)
        sh.circle(cx, cy, r, "center")
        sh.circle(cx, cy, 6)
        sh.seg(cx - r - 7, cy, cx + r + 7, cy, "center", t=0.3)
        sh.seg(cx, cy - r - 7, cx, cy + r + 7, "center", t=0.3)
    # внешние касательные к делительным окружностям
    dx = c2[0] - c1[0]
    ang = math.asin((r2 - r1) / dx)
    for sgn in (1, -1):
        a = math.pi / 2 + ang if sgn > 0 else -math.pi / 2 - ang
        p1 = (c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a))
        p2 = (c2[0] + r2 * math.cos(a), c2[1] + r2 * math.sin(a))
        sh.line([p1, p2], "center", t=0.55)
    sh.leader(80, 40 + (r1 + r2) / 2 + 2.5, 85, 75)
    sh.label(88, 76, "?", circle=True)
    sh.save(path)


FIGS = {
    "402_gear_views.png": gear_two_views,
    "402_helical.png": gear_helical,
    "402_mesh.png": gear_mesh,
    "402_chain.png": chain_drive,
}
