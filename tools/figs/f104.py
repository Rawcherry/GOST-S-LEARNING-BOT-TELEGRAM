"""ГОСТ Р 2.104-2023 — основные надписи. Геометрия формы 1 — общеизвестная (185×55)."""
from draw import ACCENT, NOTE, S, Sheet

CELLS_NUM = {  # графа: центр (x, y) в мм от левого нижнего угла надписи
    "1": (100, 27.5), "2": (125, 47.5), "3": (100, 7.5), "4": (142.5, 27.5), "5": (158.5, 27.5),
    "6": (176, 27.5), "7": (145, 17.5), "8": (170, 17.5), "9": (160, 7.5),
    "10": (8.5, 12.5), "11": (28.5, 12.5), "12": (47.5, 12.5), "13": (60, 12.5),
    "14": (3.5, 42.5), "15": (12, 42.5), "16": (28.5, 42.5), "17": (47.5, 42.5), "18": (60, 42.5),
}


def form1(sh, ox, oy, numbers=True, headers=True, highlight=None):
    def R(x, y, w, h, t=S):
        sh.rect(ox + x, oy + y, w, h, t=t)

    def H(x1, x2, y, t=S):
        sh.seg(ox + x1, oy + y, ox + x2, oy + y, t=t)

    def V(x, y1, y2, t=S):
        sh.seg(ox + x, oy + y1, ox + x, oy + y2, t=t)

    if highlight:
        x, y, w, h = highlight
        sh.fill_poly([(ox + x, oy + y), (ox + x + w, oy + y), (ox + x + w, oy + y + h),
                      (ox + x, oy + y + h)], color="#fde68a", z=1)
    R(0, 0, 185, 55)
    # левая часть
    for x in (7, 17, 40, 55, 65):
        V(x, 30 if x == 7 else 0, 55)
    for y in range(5, 55, 5):
        H(0, 65, y, t=S if y in (30, 35) else 0.4)
    # правая часть
    H(65, 185, 40)
    H(65, 185, 15)
    V(135, 0, 40)
    H(135, 185, 35, t=0.4)
    H(135, 185, 20)
    for x in (150, 167):
        V(x, 20, 40)
    for x in (140, 145):
        V(x, 20, 35, t=0.4)
    V(155, 15, 20)
    if headers:
        for x, txt in ((3.5, "Изм."), (12, "Лист"), (28.5, "№ докум."), (47.5, "Подп."), (60, "Дата")):
            sh.text(ox + x, oy + 32.5, txt, size=2.0, italic=True)
    if numbers:
        for k, (x, y) in CELLS_NUM.items():
            sh.label(ox + x, oy + y, k, size=2.6, circle=True)


def form1_numbered(path):
    sh = Sheet(200, 70)
    form1(sh, 7, 7)
    sh.text(100, 66, "Основная надпись, форма 1 (номера граф)", size=3.2, color=NOTE)
    sh.save(path)


def a3_sheet(path):
    k = 0.3
    sh = Sheet(150, 105)
    ox, oy = 12, 10
    W, H = 420 * k, 297 * k
    sh.rect(ox, oy, W, H, t=0.3)                                    # граница формата (тонкая)
    sh.rect(ox + 20 * k, oy + 5 * k, W - 25 * k, H - 10 * k, t=0.8)  # рамка
    # основная надпись 185×55
    bx, by = ox + W - 5 * k - 185 * k, oy + 5 * k
    sh.rect(bx, by, 185 * k, 55 * k, t=0.8)
    sh.seg(bx + 65 * k, by, bx + 65 * k, by + 55 * k, t=0.4)
    sh.seg(bx + 65 * k, by + 40 * k, bx + 185 * k, by + 40 * k, t=0.4)
    sh.seg(bx + 65 * k, by + 15 * k, bx + 185 * k, by + 15 * k, t=0.4)
    # графа 26 — в левом верхнем углу рамки, 70×14
    gx, gy = ox + 20 * k, oy + H - 5 * k - 14 * k
    sh.rect(gx, gy, 70 * k, 14 * k, t=0.5)
    sh.text(gx + 35 * k, gy + 7 * k, "АБВГ.123456.001", size=2.2, rot=180)
    # графа 32 «Формат» под рамкой справа
    sh.text(ox + W - 30 * k, oy + 2.5 * k - 0.3, "Формат A3", size=1.6)
    # метки
    sh.leader(gx + 20, gy + 2, gx + 32, gy - 10); sh.label(gx + 34, gy - 12, "1", circle=True)
    sh.leader(bx + 30, by + 8, bx + 10, by + 30); sh.label(bx + 8, by + 32, "2", circle=True)
    # размер левого поля
    sh.seg(ox, oy + H / 2, ox + 20 * k, oy + H / 2, "thin", color=ACCENT)
    sh.arrow_head(ox, oy + H / 2, 180, L=1.6, W=0.7, color=ACCENT)
    sh.arrow_head(ox + 20 * k, oy + H / 2, 0, L=1.6, W=0.7, color=ACCENT)
    sh.text(ox - 4, oy + H / 2, "?", size=4, color=ACCENT, bold=True)
    sh.text(75, 3.5, "Лист A3 (альбомная ориентация)", size=3, color=NOTE)
    sh.save(path)


def zones(path):
    """Разбивка поля на зоны: вариант А и Б."""
    sh = Sheet(170, 70)
    for i, (lab, ok) in enumerate((("А", True), ("Б", False))):
        ox, oy, W, H = 10 + i * 82, 12, 70, 48
        sh.rect(ox, oy, W, H, t=0.3)
        sh.rect(ox + 5, oy + 2, W - 7, H - 4, t=0.7)
        n = 4
        for j in range(n):
            x = ox + 5 + (W - 7) * (j + 0.5) / n
            num = (n - j) if ok else (j + 1)
            sh.text(x, oy + H - 1, str(num), size=2.4)
            if j:
                xx = ox + 5 + (W - 7) * j / n
                sh.seg(xx, oy + H - 2, xx, oy + H, t=0.3)
        m = 3
        letters = "ABC"
        for j in range(m):
            y = oy + 2 + (H - 4) * (j + 0.5) / m
            ch = letters[j] if ok else letters[m - 1 - j]
            sh.text(ox + 3, y, ch, size=2.4)
        sh.label(ox + W / 2, 5, lab)
    sh.text(85, 66, "Обозначение зон на поле чертежа", size=3, color=NOTE)
    sh.save(path)


FIGS = {
    "104_form1.png": form1_numbered,
    "104_a3.png": a3_sheet,
    "104_zones.png": zones,
}
