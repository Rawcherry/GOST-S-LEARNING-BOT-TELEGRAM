"""ГОСТ Р 2.105-2019 — текстовые документы (фрагменты оформления)."""
from draw import ACCENT, INK, NOTE, Sheet


def _variants(path, title, variants, h=None, size=3.4):
    rows = sum(len(v[1]) for v in variants) + len(variants)
    H = h or (16 + rows * 6.2)
    sh = Sheet(150, H)
    y = H - 9
    sh.text(75, y, title, size=3.1, color=NOTE)
    y -= 9
    for lab, lines in variants:
        sh.label(8, y, lab, size=4.2)
        for ln in lines:
            sh.text(16, y, ln, size=size, ha="left")
            y -= 6
        y -= 4
    sh.save(path)


def formula(path):
    sh = Sheet(150, 100)
    sh.text(75, 92, "Пояснение символов после формулы", size=3.1, color=NOTE)
    y = 80
    for lab, first in (("А", "где: m — масса образца, кг;"), ("Б", "где m — масса образца, кг;"),
                       ("В", "Где m — масса образца, кг;")):
        sh.label(8, y, lab, size=4.2)
        sh.text(75, y, "ρ = m / V,", size=3.6)
        sh.text(140, y, "(1)", size=3.4, ha="right")
        sh.text(18, y - 6.5, first, size=3.2, ha="left")
        sh.text(25.5, y - 12, "V — объём образца, м³.", size=3.2, ha="left")
        y -= 27
    sh.save(path)


def table_caption(path):
    sh = Sheet(150, 110)
    sh.text(75, 104, "Наименование таблицы", size=3.1, color=NOTE)
    y = 92
    for lab, cap, below in (("А", "Таблица 1 — Размеры манжет", False),
                            ("Б", "Таблица 1. Размеры манжет", False),
                            ("В", "Таблица 1 — Размеры манжет", True)):
        sh.label(8, y - 6, lab, size=4.2)
        ty = y - 14 if not below else y
        if not below:
            sh.text(18, y, cap, size=3.2, ha="left")
        # мини-таблица
        x0, w = 18, 110
        sh.rect(x0, ty - 10, w, 10, t=0.35)
        sh.seg(x0, ty - 5, x0 + w, ty - 5, t=0.35)
        for xx in (x0 + 35, x0 + 70):
            sh.seg(xx, ty - 10, xx, ty, t=0.35)
        if below:
            sh.text(18, ty - 15, cap, size=3.2, ha="left")
        y -= 31
    sh.save(path)


def figure_caption(path):
    _variants(path, "Подпись иллюстрации (располагается под рисунком)", [
        ("А", ["Рис. 1. Пыльник"]),
        ("Б", ["Рисунок 1 — Пыльник"]),
        ("В", ["Рисунок 1: пыльник."]),
    ])


def enumeration(path):
    _variants(path, "Перечисление в тексте", [
        ("А", ["Пресс-форма состоит из:", "- матрицы;", "- пуансона;", "- съёмника."]),
        ("Б", ["Пресс-форма состоит из:", "- Матрицы.", "- Пуансона.", "- Съёмника."]),
        ("В", ["Пресс-форма состоит из", "1. матрицы,", "2. пуансона,", "3. съёмника"]),
    ], size=3.2)


def appendix_letters(path):
    sh = Sheet(150, 40)
    letters = ["А", "Б", "В", "Г", "Д", "Е", "Ж", "З", "И", "К"]
    for i, ch in enumerate(letters):
        x = 12 + i * 14
        sh.rect(x - 5, 12, 10, 12, t=0.4)
        sh.text(x, 18, ch, size=5)
    sh.text(75, 33, "Буквы для обозначения приложений", size=3.1, color=NOTE)
    sh.save(path)


def margins(path):
    sh = Sheet(110, 110)
    ox, oy, W, H = 15, 8, 80, 95
    sh.rect(ox, oy, W, H, t=0.8)
    # строки текста
    for i in range(10):
        y = oy + H - 12 - i * 6
        sh.seg(ox + 4, y, ox + W - 4, y, "thin", t=0.6, color="#777777")
    # пояснения
    sh.seg(ox, oy + H - 30, ox + 4, oy + H - 30, "thin", t=0.3, color=ACCENT)
    sh.text(ox + 2, oy + H - 27, "а", size=3.5, color=ACCENT, bold=True)
    sh.seg(ox + 40, oy + H, ox + 40, oy + H - 12, "thin", t=0.3, color=ACCENT)
    sh.text(ox + 43, oy + H - 6, "б", size=3.5, color=ACCENT, bold=True)
    sh.text(55, 3, "Лист текстового документа в рамке", size=3, color=NOTE)
    sh.save(path)


FIGS = {
    "105_formula.png": formula,
    "105_table.png": table_caption,
    "105_figure.png": figure_caption,
    "105_list.png": enumeration,
    "105_appendix.png": appendix_letters,
    "105_margins.png": margins,
}
