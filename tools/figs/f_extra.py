"""Дополнительные чертежи (вторая партия вопросов)."""
import math

from draw import ACCENT, INK, NOTE, S, Sheet, axis_sym


# ---------- 2.301 ----------
def formats_compare(path):
    k = 0.075
    sh = Sheet(160, 60)
    items = [("1", 420, 297), ("2", 630, 297), ("3", 594, 420)]
    x = 8
    for lab, w, h in items:
        W, H = w * k, h * k
        sh.rect(x, 12, W, H, t=0.7)
        sh.text(x + W / 2, 12 + H / 2, f"{w}×{h}", size=3.4)
        sh.label(x + W / 2, 5, lab, circle=True, size=4.5)
        x += W + 6
    sh.text(80, 56, "Листы в одном масштабе, размеры в мм", size=3.1, color=NOTE)
    sh.save(path)


# ---------- 2.305 ----------
def shaft_break(path):
    """Длинный вал с разрывом: граница — сплошная тонкая с изломом, выходит за контур."""
    sh = Sheet(150, 55)
    y0, R = 28, 9
    xa, xb = 70, 80  # разрыв
    sh.line([(15, y0 - R), (xa, y0 - R)])
    sh.line([(15, y0 + R), (xa, y0 + R)])
    sh.seg(15, y0 - R, 15, y0 + R)
    sh.line([(xb, y0 - R), (135, y0 - R)])
    sh.line([(xb, y0 + R), (135, y0 + R)])
    sh.seg(135, y0 - R, 135, y0 + R)
    for x in (xa, xb):
        pts = [(x, y0 - R - 3), (x, y0 - 2), (x - 1.5, y0 - 0.5), (x + 1.5, y0 + 0.5), (x, y0 + 2),
               (x, y0 + R + 3)]
        sh.line(pts, "thin")
    axis_sym(sh, 75, y0, 64)
    sh.text(110, y0 - R - 6, "Вал длиной 1200 мм", size=3.2, color=NOTE)
    sh.leader(xb, y0 + R + 2.2, xb + 14, y0 + R + 14)
    sh.label(xb + 17, y0 + R + 15, "?", circle=True)
    sh.leader(xa, y0 - 4, xa - 20, y0 - R - 12)
    sh.label(xa - 23, y0 - R - 13, "1", circle=True)
    sh.save(path)


def shaft_in_bush(path):
    """Продольный разрез узла: втулка рассечена; вал — А заштрихован (неверно), Б нет (верно)."""
    sh = Sheet(160, 60)
    for i, lab in enumerate("АБ"):
        ox = 10 + i * 78
        cy = 30
        L, Rs, Rb = 64, 6, 16
        # втулка (корпус) — разрез, две половины
        top = [(ox + 12, cy + Rs), (ox + L - 12, cy + Rs), (ox + L - 12, cy + Rb), (ox + 12, cy + Rb)]
        bot = [(ox + 12, cy - Rb), (ox + L - 12, cy - Rb), (ox + L - 12, cy - Rs), (ox + 12, cy - Rs)]
        for p in (top, bot):
            sh.hatch_poly(p, 45, 2.5)
            sh.line(p, closed=True)
        # вал сплошной
        shaft = [(ox, cy - Rs), (ox + L, cy - Rs), (ox + L, cy + Rs), (ox, cy + Rs)]
        if lab == "А":
            sh.hatch_poly(shaft, -45, 2.5)
        sh.line(shaft, closed=True)
        axis_sym(sh, ox + L / 2, cy, L / 2 + 4)
        sh.label(ox + L / 2, 6, lab)
    sh.text(80, 56, "Вал (сплошной) во втулке, продольный разрез", size=3.1, color=NOTE)
    sh.save(path)


def half_view(path):
    """Фланец, вычерченный наполовину (симметричный вид)."""
    sh = Sheet(120, 70)
    cx, cy, R = 60, 15, 40
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in range(0, 181, 3)]
    sh.line(pts)
    sh.line([(cx - 14 * math.cos(math.radians(a)), cy + 14 * math.sin(math.radians(a))) for a in range(0, 181, 3)])
    sh.circle(cx, cy, 28, "center", t=0.35, a1=0, a2=180)
    for a in (45, 135):
        px, py = cx + 28 * math.cos(math.radians(a)), cy + 28 * math.sin(math.radians(a))
        sh.circle(px, py, 4)
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        sh.seg(px - 7 * ux, py - 7 * uy, px + 7 * ux, py + 7 * uy, "center", t=0.3)
        sh.seg(px - 7 * uy, py + 7 * ux, px + 7 * uy, py - 7 * ux, "center", t=0.3)
    axis_sym(sh, cx, cy, R + 6)
    axis_sym(sh, cx, cy + (R + 4) / 2, (R + 4) / 2 + 2, vertical=True)
    sh.save(path)


# ---------- 2.306 ----------
def boot(path):
    """Пыльник (гофр) на втулке, разрез верхней половины: стенка 1,5 мм зачернена."""
    sh = Sheet(150, 62)
    y0 = 8
    # металлическая втулка
    sleeve = [(10, y0), (60, y0), (60, y0 + 8), (10, y0 + 8)]
    sh.hatch_poly(sleeve, 45, 2.2)
    sh.line(sleeve, closed=True)
    # стенка пыльника: шейка на втулке, затем гофры
    t = 1.5
    mid = [(18, y0 + 8 + t / 2), (34, y0 + 8 + t / 2)]
    x, up = 34, True
    while x < 128:
        mid.append((x + 6, y0 + (40 if up else 22)))
        x += 12
        up = not up
    outer = [(p[0], p[1] + t / 2) for p in mid]
    inner = [(p[0], p[1] - t / 2) for p in mid]
    sh.fill_poly(outer + inner[::-1])
    # хомут
    clamp = [(22, y0 + 8 + t + 0.8), (30, y0 + 8 + t + 0.8), (30, y0 + 15), (22, y0 + 15)]
    sh.hatch_poly(clamp, -45, 1.6)
    sh.line(clamp, closed=True)
    axis_sym(sh, 70, y0 - 3, 64)
    sh.leader(76, 34, 92, 54); sh.label(95, 55, "1", circle=True)
    sh.leader(45, y0 + 4, 45, y0 + 25); sh.label(45, y0 + 28, "2", circle=True)
    sh.leader(26, y0 + 13, 14, y0 + 30); sh.label(12, y0 + 33, "3", circle=True)
    sh.text(118, 58, "Масштаб 1:1", size=3, color=NOTE)
    sh.save(path)


# ---------- 2.307 ----------
def ref_chain(path):
    sh = Sheet(150, 66)
    x0, y0 = 15, 40
    segs, hs = [25, 40, 30], [12, 18, 10]
    xs = [x0]
    for s_ in segs:
        xs.append(xs[-1] + s_)
    pts = [(x0, y0)]
    for i in range(3):
        pts += [(xs[i], y0 + hs[i]), (xs[i + 1], y0 + hs[i])]
    pts += [(xs[-1], y0)]
    sh.line(pts, closed=True)
    labels = ["25", "40*", "30"]
    for i in range(3):
        sh.dim_linear((xs[i], y0), (xs[i + 1], y0), -8, labels[i], ext=2)
    sh.dim_linear((xs[0], y0), (xs[-1], y0), -18, "95", ext=2)
    sh.text(x0, 8, "*Размеры для справок", size=3.3, ha="left")
    sh.leader(xs[1] + 26, y0 - 6, xs[1] + 40, y0 + 14)
    sh.label(xs[1] + 43, y0 + 16, "?", circle=True)
    sh.save(path)


def radius_break(path):
    sh = Sheet(150, 70)
    # дуга большого радиуса (центр далеко внизу), показана фрагментом
    Rr = 160
    cx, cy = 75, 60 - Rr
    pts = [(cx + Rr * math.cos(math.radians(a)), cy + Rr * math.sin(math.radians(a)))
           for a in [90 + d / 4 for d in range(-80, 81)]]
    sh.line(pts)
    # размерная линия радиуса с изломом под 90°: участок по радиусу, перпендикулярный участок,
    # участок, параллельный радиусу, до «приближённого» центра
    a = math.radians(105)
    px, py = cx + Rr * math.cos(a), cy + Rr * math.sin(a)
    ux, uy = -math.cos(a), -math.sin(a)          # направление к центру
    nx, ny = -uy, ux                              # перпендикуляр
    q1 = (px + ux * 16, py + uy * 16)
    q2 = (q1[0] + nx * 9, q1[1] + ny * 9)
    q3 = (q2[0] + ux * 16, q2[1] + uy * 16)
    sh.line([(px, py), q1, q2, q3], "thin")
    sh.arrow_head(px, py, math.degrees(a))
    sh.text(px + 8, py - 8, "R160", size=3.8)
    mx, my = (q1[0] + q2[0]) / 2, (q1[1] + q2[1]) / 2
    sh.leader(mx, my, mx + 30, my - 6)
    sh.label(mx + 33, my - 6, "?", circle=True)
    sh.save(path)


FIGS = {
    "301_compare.png": formats_compare,
    "305_break.png": shaft_break,
    "305_shaft_bush.png": shaft_in_bush,
    "305_half_view.png": half_view,
    "306_boot.png": boot,
    "307_ref_chain.png": ref_chain,
    "307_radius_break.png": radius_break,
}
