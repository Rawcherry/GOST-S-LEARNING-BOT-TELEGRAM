"""Мини-библиотека чертёжных примитивов на matplotlib.

Координаты — миллиметры «чертежа». Толщины и штрихи линий заданы в мм по ГОСТ 2.303-68
и пересчитываются в пункты с учётом масштаба картинки, поэтому пропорции соблюдены.
"""
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Polygon, Rectangle
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch

S = 1.0           # толщина сплошной основной линии, мм (ГОСТ 2.303: 0,5…1,4)
THIN = 0.4        # тонкие линии: S/3…S/2
INK = "#111111"
ACCENT = "#c62828"   # красный — подписи вариантов
NOTE = "#1565c0"     # синий — пояснительные выноски (не элемент чертежа)
FONT = "DejaVu Sans"

# штрихи (длина штриха, промежуток), мм
DASH = {
    "hidden": (5, 1.5),          # штриховая: 2…8 / 1…2
    "center": (16, 4),           # штрихпунктирная тонкая: 5…30 / 3…5
    "thick_center": (6, 3.5),    # штрихпунктирная утолщённая: 3…8 / 3…4
    "phantom": (16, 5),          # с двумя точками: 5…30 / 4…6
}


class Sheet:
    def __init__(self, w, h, px_w=1200, dpi=150, margin=0, bg="white"):
        self.w, self.h = w, h
        px_h = int(px_w * h / w)
        self.fig = plt.figure(figsize=(px_w / dpi, px_h / dpi), dpi=dpi)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(-margin, w + margin)
        self.ax.set_ylim(-margin, h + margin)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.fig.patch.set_facecolor(bg)
        self.dpi = dpi
        # пунктов на мм чертежа
        self.pt_per_mm = (px_w / dpi * 72) / (w + 2 * margin)

    # ---------- линии ----------
    def _lw(self, t):
        return max(t * self.pt_per_mm, 0.5)

    def _dashes(self, kind, t):
        lw = self._lw(t)
        k = self.pt_per_mm / lw  # мм -> единицы толщины линии
        if kind == "hidden":
            d, g = DASH["hidden"]
            return (0, (d * k, g * k))
        if kind in ("center", "thick_center"):
            d, g = DASH[kind]
            dot = 1.0
            gg = (g - dot) / 2
            return (0, (d * k, gg * k, dot * k, gg * k))
        if kind == "phantom":
            d, g = DASH["phantom"]
            dot = 1.0
            gg = (g - 2 * dot) / 3
            return (0, (d * k, gg * k, dot * k, gg * k, dot * k, gg * k))
        return "solid"

    def line(self, pts, kind="main", t=None, color=INK, z=3, closed=False):
        if t is None:
            t = {"main": S, "thick_center": S * 0.6, "cut": S * 1.3}.get(kind, THIN)
        xs = [p[0] for p in pts] + ([pts[0][0]] if closed else [])
        ys = [p[1] for p in pts] + ([pts[0][1]] if closed else [])
        style = self._dashes(kind, t) if kind in ("hidden", "center", "thick_center", "phantom") else "solid"
        self.ax.plot(xs, ys, color=color, lw=self._lw(t), linestyle=style,
                     solid_capstyle="butt", dash_capstyle="butt", solid_joinstyle="miter", zorder=z)

    def seg(self, x1, y1, x2, y2, kind="main", **kw):
        self.line([(x1, y1), (x2, y2)], kind, **kw)

    def rect(self, x, y, w, h, kind="main", **kw):
        self.line([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], kind, closed=True, **kw)

    def circle(self, cx, cy, r, kind="main", t=None, color=INK, z=3, a1=0, a2=360):
        n = max(24, int(abs(a2 - a1) / 3))
        pts = [(cx + r * math.cos(math.radians(a1 + (a2 - a1) * i / n)),
                cy + r * math.sin(math.radians(a1 + (a2 - a1) * i / n))) for i in range(n + 1)]
        self.line(pts, kind, t=t, color=color, z=z)

    def wavy(self, x1, y1, x2, y2, amp=1.2, waves=3, t=THIN, color=INK):
        """Сплошная волнистая линия."""
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy, ux
        pts = []
        n = 80
        for i in range(n + 1):
            s = L * i / n
            o = amp * math.sin(2 * math.pi * waves * i / n)
            pts.append((x1 + ux * s + nx * o, y1 + uy * s + ny * o))
        self.line(pts, "thin", t=t, color=color)

    def zigzag(self, x1, y1, x2, y2, t=THIN, color=INK, n_breaks=1, h=4):
        """Сплошная тонкая с изломами."""
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy, ux
        pts = [(x1, y1)]
        for b in range(1, n_breaks + 1):
            s = L * b / (n_breaks + 1)
            for ds, o in ((-2, 0), (-1, h / 2), (1, -h / 2), (2, 0)):
                pts.append((x1 + ux * (s + ds) + nx * o, y1 + uy * (s + ds) + ny * o))
        pts.append((x2, y2))
        self.line(pts, "thin", t=t, color=color)

    # ---------- штриховка ----------
    def hatch_poly(self, poly, angle=45, step=2.5, t=THIN, color=INK, offset=0.0, z=2):
        """Штриховка многоугольника параллельными линиями (с отсечением по контуру)."""
        a = math.radians(angle)
        d = (math.cos(a), math.sin(a))
        n = (-d[1], d[0])
        proj = [p[0] * n[0] + p[1] * n[1] for p in poly]
        lo, hi = min(proj), max(proj)
        c = lo + (offset % step) if offset else lo + step / 2
        while c < hi:
            xs = []
            m = len(poly)
            for i in range(m):
                p, q = poly[i], poly[(i + 1) % m]
                pp = p[0] * n[0] + p[1] * n[1] - c
                qq = q[0] * n[0] + q[1] * n[1] - c
                if (pp < 0) != (qq < 0):
                    tt = pp / (pp - qq)
                    x = p[0] + (q[0] - p[0]) * tt
                    y = p[1] + (q[1] - p[1]) * tt
                    xs.append((x * d[0] + y * d[1], (x, y)))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.line([xs[i][1], xs[i + 1][1]], "thin", t=t, color=color, z=z)
            c += step

    def fill_poly(self, poly, color=INK, z=2):
        self.ax.add_patch(Polygon(poly, closed=True, facecolor=color, edgecolor="none", zorder=z))

    def white_poly(self, poly, z=2.5):
        self.ax.add_patch(Polygon(poly, closed=True, facecolor="white", edgecolor="none", zorder=z))

    # ---------- размеры и текст ----------
    def text(self, x, y, s, size=3.5, ha="center", va="center", color=INK, rot=0, bold=False,
             italic=False, z=6, bbox=False):
        fs = size * self.pt_per_mm * 1.0
        kw = {}
        if bbox:
            kw["bbox"] = dict(boxstyle="round,pad=0.25", fc="white", ec="none")
        self.ax.text(x, y, s, fontsize=fs, ha=ha, va=va, color=color, rotation=rot,
                     fontfamily=FONT, fontweight="bold" if bold else "normal",
                     fontstyle="italic" if italic else "normal", zorder=z, **kw)

    def arrow_head(self, x, y, ang, L=3.0, W=1.0, color=INK):
        """Стрелка размерной линии: остриё в (x, y), направлена по углу ang (градусы)."""
        a = math.radians(ang)
        bx, by = x - L * math.cos(a), y - L * math.sin(a)
        nx, ny = -math.sin(a) * W / 2, math.cos(a) * W / 2
        self.fill_poly([(x, y), (bx + nx, by + ny), (bx - nx, by - ny)], color=color, z=4)

    def dim_linear(self, p1, p2, off, label, orient="h", ext=2.0, size=3.5, color=INK,
                   arrows=True, text_pos=None):
        """Линейный размер. orient='h' — горизонтальный (размерная линия на y1+off),
        'v' — вертикальный (на x1+off). ext — выход выносных линий за размерную."""
        (x1, y1), (x2, y2) = p1, p2
        sgn = 1 if off > 0 else -1
        if orient == "h":
            yd = y1 + off
            self.seg(x1, y1, x1, yd + sgn * ext, "thin", color=color)
            self.seg(x2, y2, x2, yd + sgn * ext, "thin", color=color)
            self.seg(x1, yd, x2, yd, "thin", color=color)
            if arrows:
                a, b = (180, 0) if x2 > x1 else (0, 180)
                self.arrow_head(x1, yd, a, color=color)
                self.arrow_head(x2, yd, b, color=color)
            tx = text_pos if text_pos is not None else (x1 + x2) / 2
            self.text(tx, yd + size * 0.5 + 0.8, label, size=size, color=color)
        else:
            xd = x1 + off
            self.seg(x1, y1, xd + sgn * ext, y1, "thin", color=color)
            self.seg(x2, y2, xd + sgn * ext, y2, "thin", color=color)
            self.seg(xd, y1, xd, y2, "thin", color=color)
            if arrows:
                a, b = (270, 90) if y2 > y1 else (90, 270)
                self.arrow_head(xd, y1, a, color=color)
                self.arrow_head(xd, y2, b, color=color)
            ty = text_pos if text_pos is not None else (y1 + y2) / 2
            self.text(xd - size * 0.5 - 0.8, ty, label, size=size, rot=90, color=color)

    def label(self, x, y, s, size=5, color=ACCENT, circle=False):
        """Метка варианта/позиции (красная) — не элемент чертежа."""
        if circle:
            self.ax.add_patch(matplotlib.patches.Circle((x, y), size * 0.62, fc="white", ec=color,
                                                        lw=self._lw(0.35), zorder=7))
        self.text(x, y, s, size=size, color=color, bold=True, z=8)

    def leader(self, x1, y1, x2, y2, color=NOTE, t=0.3):
        self.line([(x1, y1), (x2, y2)], "thin", t=t, color=color, z=7)
        self.ax.add_patch(matplotlib.patches.Circle((x1, y1), 0.7, fc=color, ec="none", zorder=7))

    def save(self, path):
        self.fig.savefig(path, dpi=self.dpi, facecolor=self.fig.get_facecolor())
        plt.close(self.fig)


def axis_sym(sh, cx, cy, half, vertical=False, t=THIN, color=INK, dash=10, gap=3.5, dot=1.0,
             center_on="dash"):
    """Штрихпунктирная линия, симметричная относительно (cx, cy): в центре — штрих
    (center_on='dot' — нарочно точка, для «неверного» варианта), на концах — штрихи."""
    segs = []  # отрезки вдоль оси от центра, s in [-half, half]
    if center_on == "dash":
        segs.append((-dash / 2, dash / 2))
        s = dash / 2
    else:
        segs.append((-dot / 2, dot / 2))
        s = dot / 2
    side = []
    while s < half:
        # промежуток, точка, промежуток, штрих
        g1 = s + (gap - dot) / 2
        if center_on == "dash":
            side.append((g1, g1 + dot))
            d0 = g1 + dot + (gap - dot) / 2
        else:
            d0 = s + (gap - dot) / 2
        d1 = min(d0 + dash, half)
        if d0 >= half:
            # конец должен быть штрихом: продлеваем последний штрих
            break
        side.append((d0, d1))
        s = d1
        center_on = "dash"
    segs += side + [(-b, -a) for a, b in side]
    for a, b in segs:
        if vertical:
            sh.seg(cx, cy + a, cx, cy + b, "thin", t=t, color=color)
        else:
            sh.seg(cx + a, cy, cx + b, cy, "thin", t=t, color=color)
