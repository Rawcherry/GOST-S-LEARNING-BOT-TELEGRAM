"""ГОСТ 2.315-68 — упрощённые и условные изображения крепёжных деталей."""
import math

from draw import NOTE, S, Sheet


def screw_slot(path):
    """Винт с цилиндрической головкой: главный вид и три варианта вида сверху."""
    sh = Sheet(170, 70)
    # главный вид
    cx, yb = 22, 8
    sh.rect(cx - 6, yb, 12, 30)                  # стержень
    sh.rect(cx - 11, yb + 30, 22, 9)             # головка
    sh.seg(cx, yb + 33, cx, yb + 39, t=S * 1.6)  # шлиц — по оси детали
    sh.seg(cx, yb - 4, cx, yb + 43, "center")
    sh.text(cx, 64, "Главный вид", size=3.2, color=NOTE)
    for i, (lab, ang) in enumerate((("А", 45), ("Б", 0), ("В", 90))):
        ox = 65 + i * 40
        oy = 32
        sh.circle(ox, oy, 11)
        a = math.radians(ang)
        dx, dy = 9.5 * math.cos(a), 9.5 * math.sin(a)
        sh.seg(ox - dx, oy - dy, ox + dx, oy + dy, t=S * 1.6)
        sh.seg(ox - 15, oy, ox + 15, oy, "center", t=0.3)
        sh.seg(ox, oy - 15, ox, oy + 15, "center", t=0.3)
        sh.label(ox, 10, lab)
    sh.text(105, 64, "Вид сверху — варианты", size=3.2, color=NOTE)
    sh.save(path)


def bolt_group(path):
    """Фланец с рядом однотипных болтовых соединений."""
    sh = Sheet(110, 90)
    cx, cy, R = 55, 45, 36
    sh.circle(cx, cy, R)
    sh.circle(cx, cy, 13)
    sh.circle(cx, cy, 26, "center")
    sh.seg(cx - R - 4, cy, cx + R + 4, cy, "center")
    sh.seg(cx, cy - R - 4, cx, cy + R + 4, "center")
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        px, py = cx + 26 * math.cos(a), cy + 26 * math.sin(a)
        if k in (0, 4):
            # упрощённое изображение гайки (вид сверху): шестигранник + окружность стержня
            hexr = 6.3
            pts = [(px + hexr * math.cos(math.radians(30 + 60 * j)),
                    py + hexr * math.sin(math.radians(30 + 60 * j))) for j in range(6)]
            sh.line(pts, closed=True)
            sh.circle(px, py, 5.4, "thin")
            sh.circle(px, py, 4)
        # осевые на каждом месте соединения
        ux, uy = math.cos(a), math.sin(a)
        sh.seg(px - 7 * ux, py - 7 * uy, px + 7 * ux, py + 7 * uy, "center", t=0.3)
    sh.save(path)


FIGS = {
    "315_slot.png": screw_slot,
    "315_bolt_group.png": bolt_group,
}
