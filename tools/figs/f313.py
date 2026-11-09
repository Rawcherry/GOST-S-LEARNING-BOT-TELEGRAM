"""ГОСТ 2.313-82 — неразъёмные соединения (пайка, склеивание, клёпка)."""
import math

from draw import NOTE, S, Sheet


def lap_joint(sh, y0=30, x0=15, x1=125, ov=(55, 95), t=4):
    """Две пластины внахлёстку (вид сбоку). Возвращает y линии соединения."""
    sh.rect(x0, y0, ov[1] - x0, t)                 # нижняя пластина
    sh.rect(ov[0], y0 + t, x1 - ov[0], t)          # верхняя пластина
    return y0 + t


def joint_with_leader(sh, sign, x_lead=75, labels=True, closed=True, shelf_text="3"):
    yj = lap_joint(sh)
    sh.seg(55, yj, 95, yj, t=2 * S)                     # место соединения — линия 2s
    # линия-выноска: от шва вверх-вправо, затем полка
    xa, ya = x_lead, yj
    xb, yb = x_lead + 22, yj + 28
    sh.line([(xa, ya), (xb, yb)], "thin")
    sh.arrow_head(xa, ya, math.degrees(math.atan2(ya - yb, xa - xb)), L=3, W=1)
    sh.seg(xb, yb, xb + 22, yb, "thin")                 # полка
    sh.text(xb + 11, yb + 3, shelf_text, size=3.8)
    # окружность 3–5 мм на изломе — шов по замкнутой линии
    if closed:
        sh.circle(xb, yb, 2, "thin")
    # условный знак на выноске
    tx = xa + (xb - xa) * 0.55
    ty = ya + (yb - ya) * 0.55
    ang = math.atan2(yb - ya, xb - xa)
    if sign == "solder":
        # полуокружность на линии-выноске
        r = 2.4
        pts = [(tx + r * math.cos(ang + math.pi / 2 + math.pi * i / 20) ,
                ty + r * math.sin(ang + math.pi / 2 + math.pi * i / 20)) for i in range(21)]
        sh.line(pts, "main")
    elif sign == "glue":
        sh.text(tx - 3.2, ty + 0.5, "К", size=4.2, bold=False)
    if labels:
        sh.leader(65, yj, 50, yj + 18); sh.label(47, yj + 21, "1", circle=True)
        sh.leader(tx - 1, ty + 1, tx - 15, ty + 14); sh.label(tx - 18, ty + 16, "2", circle=True)
        if closed:
            sh.leader(xb - 1.4, yb + 1.4, xb - 10, yb + 12); sh.label(xb - 12, yb + 14, "3", circle=True)
        sh.leader(xb + 13, yb + 5, xb + 26, yb + 14); sh.label(xb + 28, yb + 16, "4", circle=True)


def solder(path):
    sh = Sheet(150, 88)
    joint_with_leader(sh, "solder")
    sh.text(75, 8, "Паяное соединение (пластины внахлёстку, вид сбоку)", size=3.3, color=NOTE)
    sh.save(path)


def glue(path):
    sh = Sheet(150, 80)
    joint_with_leader(sh, "glue", labels=False, closed=False, shelf_text="2")
    sh.leader(97, 62, 110, 72); sh.label(113, 74, "?", circle=True)
    sh.text(75, 8, "Соединение двух пластин (вид сбоку)", size=3.3, color=NOTE)
    sh.save(path)


def rivet_row(path):
    sh = Sheet(150, 60)
    sh.rect(10, 15, 130, 30)       # верхняя пластина (вид сверху)
    sh.seg(10, 25, 140, 25, "hidden")  # край нижней пластины (невидим)
    yr = 33
    sh.seg(14, yr, 136, yr, "center")
    for i in range(9):
        x = 22 + i * 13.3
        if i in (0, 1):
            sh.circle(x, yr, 3.5)
        sh.seg(x, yr - 6, x, yr + 6, "center", t=0.3)
    sh.text(75, 54, "Заклёпочный шов (вид сверху)", size=3.3, color=NOTE)
    sh.save(path)


FIGS = {
    "313_solder.png": solder,
    "313_glue.png": glue,
    "313_rivets.png": rivet_row,
}
