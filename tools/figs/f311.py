"""ГОСТ 2.311-68 — изображение резьбы."""
import math

from draw import ACCENT, NOTE, S, THIN, Sheet


def rod(sh, x0, y0, L=70, tl=40, R=12, r=10.2, ch=2.0, end_view_x=None, arc_ok=True,
        arc_main=False, full_circle=False, show_chamfer_circle=False, labels=False):
    """Стержень с наружной резьбой; правый торец с фаской. Ось по y0."""
    xe = x0 + L
    # контур
    sh.line([(x0, y0 - R), (xe - ch, y0 - R), (xe, y0 - R + ch), (xe, y0 + R - ch),
             (xe - ch, y0 + R), (x0, y0 + R)])
    sh.seg(x0, y0 - R, x0, y0 + R)
    sh.seg(xe - ch, y0 - R, xe - ch, y0 + R)          # граница фаски
    xb = xe - tl
    sh.seg(xb, y0 - R, xb, y0 + R)                     # граница резьбы
    sh.seg(xb, y0 + r, xe, y0 + r, "thin")             # внутренний диаметр — тонкая
    sh.seg(xb, y0 - r, xe, y0 - r, "thin")
    sh.seg(x0 - 4, y0, xe + 4, y0, "center")
    if end_view_x is not None:
        cx = end_view_x
        sh.circle(cx, y0, R)
        if full_circle:
            sh.circle(cx, y0, r, "thin")
        elif arc_ok:
            sh.circle(cx, y0, r, "main" if arc_main else "thin", a1=110, a2=380)
        if show_chamfer_circle:
            sh.circle(cx, y0, R - ch)
        sh.seg(cx - R - 4, y0, cx + R + 4, y0, "center")
        sh.seg(cx, y0 - R - 4, cx, y0 + R + 4, "center")
    if labels:
        sh.leader(x0 + 15, y0 + R, x0 + 10, y0 + R + 10)
        sh.label(x0 + 10, y0 + R + 13, "1", circle=True)
        sh.leader(xb + 22, y0 + r, xb + 18, y0 + R + 10)
        sh.label(xb + 18, y0 + R + 13, "2", circle=True)
        sh.leader(xb, y0 - R + 3, xb - 8, y0 - R - 9)
        sh.label(xb - 8, y0 - R - 12, "3", circle=True)
        sh.leader(xe - ch, y0 - R + 2, xe - ch + 6, y0 - R - 9)
        sh.label(xe - ch + 6, y0 - R - 12, "4", circle=True)
        if end_view_x is not None:
            a = math.radians(45)
            sh.leader(end_view_x + r * math.cos(a), y0 + r * math.sin(a), end_view_x + 18, y0 + 20)
            sh.label(end_view_x + 20, y0 + 22, "5", circle=True)


def thread_rod_labeled(path):
    sh = Sheet(150, 70)
    rod(sh, 10, 33, end_view_x=120, labels=True)
    sh.save(path)


def thread_end_variants(path):
    sh = Sheet(170, 55)
    R, r = 12, 10.2
    for i, (lab, kw) in enumerate([("А", dict(full=True)), ("Б", dict(arc=True)),
                                   ("В", dict(arc=True, main=True)), ("Г", dict(swap=True))]):
        cx, cy = 22 + i * 42, 26
        if kw.get("swap"):  # перепутаны линии: наружный — тонкая, внутренний — основная дуга
            sh.circle(cx, cy, R, "thin")
            sh.circle(cx, cy, r, a1=110, a2=380)
            sh.seg(cx - R - 4, cy, cx + R + 4, cy, "center")
            sh.seg(cx, cy - R - 4, cx, cy + R + 4, "center")
            sh.label(cx, 6, lab)
            continue
        sh.circle(cx, cy, R)
        if kw.get("full"):
            sh.circle(cx, cy, r, "thin")
        else:
            sh.circle(cx, cy, r, "main" if kw.get("main") else "thin", a1=110, a2=380)
        if kw.get("chamf"):
            sh.circle(cx, cy, R - 2)
        sh.seg(cx - R - 4, cy, cx + R + 4, cy, "center")
        sh.seg(cx, cy - R - 4, cx, cy + R + 4, "center")
        sh.label(cx, 6, lab)
    sh.text(85, 50, "Резьба на стержне, вид с торца (фаска 2×45°)", size=3.6, color=NOTE)
    sh.save(path)


def hole_block(sh, x0, y0, W=36, H=50, R=12, r=10.2, depth=50, hatch_to="minor", labels=False):
    """Деталь с резьбовым сквозным отверстием, продольный разрез. Ось отверстия вертикальна."""
    cx = x0 + W / 2 + 15
    left = [(x0, y0), (cx - r, y0), (cx - r, y0 + H), (x0, y0 + H)]
    right = [(cx + r, y0), (x0 + W + 30, y0), (x0 + W + 30, y0 + H), (cx + r, y0 + H)]
    bound = r if hatch_to == "minor" else R
    for poly, sgn in ((left, -1), (right, 1)):
        hp = [(cx + sgn * bound if abs(p[0] - (cx + sgn * r)) < 1e-6 else p[0], p[1]) for p in poly]
        sh.hatch_poly(hp, 45, 3)
        sh.line(poly, closed=True)
    sh.seg(cx - R, y0, cx - R, y0 + H, "thin")
    sh.seg(cx + R, y0, cx + R, y0 + H, "thin")
    sh.seg(cx, y0 - 4, cx, y0 + H + 4, "center")
    return cx


def thread_hole_variants(path):
    sh = Sheet(170, 75)
    for i, (lab, mode) in enumerate((("А", "minor"), ("Б", "major"))):
        x0 = 8 + i * 84
        hole_block(sh, x0, 14, hatch_to=mode)
        sh.label(x0 + 33, 5, lab)
    sh.text(85, 70, "Резьбовое отверстие в разрезе", size=3.6, color=NOTE)
    sh.save(path)


def thread_hole_end(path):
    """Резьбовое отверстие с торца: верно и неверно."""
    sh = Sheet(150, 55)
    R, r = 12, 10.2
    variants = [("А", "main_minor"), ("Б", "main_major"), ("В", "both_main")]
    for i, (lab, mode) in enumerate(variants):
        cx, cy = 28 + i * 47, 28
        sh.rect(cx - 20, cy - 20, 40, 40)
        if mode == "main_minor":
            sh.circle(cx, cy, r)
            sh.circle(cx, cy, R, "thin", a1=110, a2=380)
        elif mode == "main_major":
            sh.circle(cx, cy, R)
            sh.circle(cx, cy, r, "thin", a1=110, a2=380)
        else:
            sh.circle(cx, cy, r)
            sh.circle(cx, cy, R)
        sh.seg(cx - R - 4, cy, cx + R + 4, cy, "center")
        sh.seg(cx, cy - R - 4, cx, cy + R + 4, "center")
        sh.label(cx, 3.5, lab)
    sh.text(75, 52, "Резьбовое отверстие, вид вдоль оси", size=3.6, color=NOTE)
    sh.save(path)


def thread_joint(path):
    """Шпилька, ввёрнутая в деталь, разрез: верно (А) и неверно (Б)."""
    sh = Sheet(170, 90)
    R, r = 10, 8.5
    for i, lab in enumerate("АБ"):
        x0 = 10 + i * 84
        cx = x0 + 34
        yb, yt = 10, 55       # деталь
        hole_bot = yb + 8      # дно резьбы в отверстии (сквозное — до низа)
        stud_bot = 28          # конец шпильки в отверстии
        # деталь (корпус) — разрез, отверстие сквозное
        left = [(x0, yb), (cx - r, yb), (cx - r, yt), (x0, yt)]
        right = [(cx + r, yb), (x0 + 68, yb), (x0 + 68, yt), (cx + r, yt)]
        for poly, sg in ((left, -1), (right, 1)):
            sh.hatch_poly(poly, 45, 3)
            sh.line(poly, closed=True)
        # шпилька (не рассекается): стержень от stud_bot до верха
        top = 80
        sh.white_poly([(cx - R, stud_bot), (cx + R, stud_bot), (cx + R, top), (cx - R, top)], z=3.5)
        sh.line([(cx - R, stud_bot), (cx + R, stud_bot), (cx + R, top), (cx - R, top)],
                closed=True, z=4)
        sh.seg(cx - r, stud_bot, cx - r, top, "thin", z=4)
        sh.seg(cx + r, stud_bot, cx + r, top, "thin", z=4)
        # граница резьбы шпильки на ввинчиваемом конце (ниже верха детали — резьба по всей длине здесь)
        # резьба в отверстии ниже шпильки: внутренний — основная (контур отверстия), наружный — тонкая
        sh.seg(cx - R, yb, cx - R, stud_bot, "thin", z=4)
        sh.seg(cx + R, yb, cx + R, stud_bot, "thin", z=4)
        if lab == "Б":  # ошибка: резьба отверстия поверх шпильки
            sh.seg(cx - r, stud_bot, cx - r, yt, "main", z=5)
            sh.seg(cx + r, stud_bot, cx + r, yt, "main", z=5)
            sh.seg(cx - R, stud_bot, cx - R, yt, "thin", z=5)
            sh.seg(cx + R, stud_bot, cx + R, yt, "thin", z=5)
        sh.seg(cx, yb - 4, cx, top + 4, "center", z=5)
        sh.label(cx, 3, lab)
    sh.save(path)


def thread_hidden(path):
    sh = Sheet(150, 60)
    # вид детали без разреза: невидимое резьбовое отверстие
    x0, y0 = 20, 10
    sh.rect(x0, y0, 60, 40)
    cx = x0 + 30
    for d in (10.2, 12):
        sh.seg(cx - d, y0, cx - d, y0 + 40, "hidden")
        sh.seg(cx + d, y0, cx + d, y0 + 40, "hidden")
    sh.seg(cx, y0 - 4, cx, y0 + 44, "center")
    sh.text(118, 30, "Деталь показана\nбез разреза:\nрезьбовое отверстие\nневидимо", size=3.4,
            color=NOTE)
    sh.save(path)


def thread_boundary(path):
    """Граница резьбы и сбег."""
    sh = Sheet(150, 60)
    y0, x0, xe, R, r = 32, 15, 95, 12, 10.2
    sh.line([(x0, y0 - R), (xe, y0 - R), (xe, y0 + R), (x0, y0 + R)])
    sh.seg(x0, y0 - R, x0, y0 + R)
    xb = xe - 40
    sh.seg(xb, y0 - R, xb, y0 + R)                 # граница
    sh.seg(xb, y0 + r, xe, y0 + r, "thin")
    sh.seg(xb, y0 - r, xe, y0 - r, "thin")
    sh.seg(xb, y0 + r, xb - 5, y0 + R, "thin")     # сбег
    sh.seg(xb, y0 - r, xb - 5, y0 - R, "thin")
    sh.seg(x0 - 4, y0, xe + 4, y0, "center")
    sh.leader(xb, y0 + 3, xb + 18, y0 + 22)
    sh.label(xb + 20, y0 + 24, "1", circle=True)
    sh.leader(xb - 2.5, y0 - r - 1, xb - 15, y0 - R - 10)
    sh.label(xb - 17, y0 - R - 12, "2", circle=True)
    sh.save(path)


FIGS = {
    "311_rod_labeled.png": thread_rod_labeled,
    "311_end_variants.png": thread_end_variants,
    "311_hole_hatch.png": thread_hole_variants,
    "311_hole_end.png": thread_hole_end,
    "311_joint.png": thread_joint,
    "311_hidden.png": thread_hidden,
    "311_boundary.png": thread_boundary,
}
