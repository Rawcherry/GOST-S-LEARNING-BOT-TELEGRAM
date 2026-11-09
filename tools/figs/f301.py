"""ГОСТ 2.301-68 — форматы."""
from draw import ACCENT, INK, NOTE, Sheet


def nesting(path):
    """Формат A0, разбитый на A1…A4 (размеры в масштабе)."""
    k = 0.1  # 1189 мм -> 118.9 «мм» картинки
    sh = Sheet(150, 100)
    x0, y0 = 8, 8
    W, H = 1189 * k, 841 * k
    sh.rect(x0, y0, W, H, t=0.8)
    # A1 — левая половина
    sh.seg(x0 + W / 2, y0, x0 + W / 2, y0 + H, t=0.6)
    # A2 — верхняя половина правой части
    sh.seg(x0 + W / 2, y0 + H / 2, x0 + W, y0 + H / 2, t=0.6)
    # A3 — левая половина нижней правой четверти
    sh.seg(x0 + W * 3 / 4, y0, x0 + W * 3 / 4, y0 + H / 2, t=0.6)
    # A4 — верхняя половина оставшейся восьмой части
    sh.seg(x0 + W * 3 / 4, y0 + H / 4, x0 + W, y0 + H / 4, t=0.6)
    cells = [("1", x0 + W / 4, y0 + H / 2), ("2", x0 + W * 3 / 4, y0 + H * 3 / 4),
             ("3", x0 + W * 5 / 8, y0 + H / 4), ("4", x0 + W * 7 / 8, y0 + H * 3 / 8),
             ("5", x0 + W * 7 / 8, y0 + H / 8)]
    for lab, cx, cy in cells:
        sh.label(cx, cy, lab, circle=True, size=5)
    sh.text(x0 + W / 2, y0 + H + 4, "Формат A0  1189 × 841", size=3.4, color=NOTE)
    sh.save(path)


def a4x3(path):
    """Дополнительный формат A4×3: сторона 297 и кратная сторона."""
    k = 0.11
    sh = Sheet(110, 90)
    x0, y0 = 15, 12
    w, h = 630 * k, 297 * k
    sh.rect(x0, y0, w, h, t=0.8)
    for i in (1, 2):
        sh.seg(x0 + 210 * k * i, y0, x0 + 210 * k * i, y0 + h, "hidden", t=0.35, color=NOTE)
    sh.dim_linear((x0, y0 + h), (x0 + w, y0 + h), 10, "?", size=4.5, color=ACCENT)
    sh.dim_linear((x0, y0), (x0, y0 + h), -6, "297", orient="v", size=3.8)
    sh.text(x0 + w / 2, y0 + h / 2, "A4×3", size=6, bold=True)
    sh.text(55, 6, "Пунктир — границы трёх листов A4 (для наглядности)", size=3, color=NOTE)
    sh.save(path)


FIGS = {
    "301_nesting.png": nesting,
    "301_a4x3.png": a4x3,
}
