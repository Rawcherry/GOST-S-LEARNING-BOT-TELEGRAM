"""Загрузка и проверка банка вопросов (data/questions/*.yaml) и справочника ГОСТов (data/gosts.yaml)."""
import html
from dataclasses import dataclass, field
from pathlib import Path

import yaml

LETTERS = "АБВГДЕ"
CAPTION_LIMIT = 1024


@dataclass
class Gost:
    code: str          # "2.303"
    full: str          # "ГОСТ 2.303-68"
    title: str         # "Линии"
    emoji: str = "📐"
    note: str = ""     # статус/замечание
    cheat: str = ""    # шпаргалка (HTML)


@dataclass
class Question:
    id: str
    gost: str
    ref: str
    q: str
    options: list
    answer: int
    explain: str
    image: str = ""
    level: int = 1
    fixed: bool = False      # не перемешивать варианты (варианты — буквы на картинке)
    tags: list = field(default_factory=list)

    @property
    def correct_text(self):
        return self.options[self.answer]


class BankError(Exception):
    pass


class Bank:
    def __init__(self, data_dir: Path, images_dir: Path):
        self.data_dir = Path(data_dir)
        self.images_dir = Path(images_dir)
        self.gosts: dict[str, Gost] = {}
        self.questions: dict[str, Question] = {}
        self.load()

    def load(self):
        gosts, questions, errors = {}, {}, []
        meta = yaml.safe_load((self.data_dir / "gosts.yaml").read_text(encoding="utf-8"))
        for g in meta["gosts"]:
            gosts[g["code"]] = Gost(**g)
        for f in sorted((self.data_dir / "questions").glob("*.yaml")):
            items = yaml.safe_load(f.read_text(encoding="utf-8")) or []
            for raw in items:
                try:
                    q = Question(**raw)
                except TypeError as e:
                    errors.append(f"{f.name}: {raw.get('id')}: {e}")
                    continue
                errors += [f"{f.name}: {e}" for e in self.check(q, gosts)]
                if q.id in questions:
                    errors.append(f"{f.name}: повтор id {q.id}")
                questions[q.id] = q
        if errors:
            raise BankError("Ошибки в банке вопросов:\n" + "\n".join(errors))
        self.gosts, self.questions = gosts, questions

    def check(self, q, gosts):
        errs = []
        if q.gost not in gosts:
            errs.append(f"{q.id}: неизвестный ГОСТ {q.gost}")
        if not (2 <= len(q.options) <= 5):
            errs.append(f"{q.id}: вариантов должно быть 2–5")
        if not (0 <= q.answer < len(q.options)):
            errs.append(f"{q.id}: answer вне диапазона")
        if len(set(map(str, q.options))) != len(q.options):
            errs.append(f"{q.id}: одинаковые варианты")
        if q.image and not (self.images_dir / q.image).exists():
            errs.append(f"{q.id}: нет картинки {q.image}")
        # самый длинный вид подписи (после ответа) должен влезать в лимит Telegram
        g = gosts.get(q.gost)
        if g:
            longest = len(answered_caption(q, g, 99, 99, order=list(range(len(q.options))),
                                           chosen=(q.answer + 1) % len(q.options), plain=True))
            if longest > CAPTION_LIMIT:
                errs.append(f"{q.id}: подпись после ответа {longest} > {CAPTION_LIMIT} симв.")
        return errs

    def by_gost(self, code):
        return [q for q in self.questions.values() if q.gost == code]

    def image_path(self, q: Question):
        if q.image:
            return self.images_dir / q.image
        return self.images_dir / f"card_{q.gost.replace('.', '_')}.png"


# ---------------- форматирование подписей ----------------

def esc(s):
    return html.escape(str(s), quote=False)


def use_text_buttons(q):
    return all(len(str(o)) <= 32 for o in q.options)


def question_caption(q, g, num, total, order, title=None):
    head = f"{g.emoji} <b>{esc(g.full)}</b> · {esc(g.title)}"
    if title:
        head = f"<b>{esc(title)}</b> · {esc(g.full)}"
    lines = [head, f"<i>Вопрос {num} из {total}</i>", "", f"<b>{esc(q.q)}</b>"]
    if not use_text_buttons(q):
        lines.append("")
        for i, oi in enumerate(order):
            lines.append(f"{LETTERS[i]}) {esc(q.options[oi])}")
    return "\n".join(lines)


def answered_caption(q, g, num, total, order=None, chosen=None, plain=False, title=None):
    """chosen — индекс в исходном списке вариантов."""
    order = order or list(range(len(q.options)))
    head = f"{g.emoji} <b>{esc(g.full)}</b> · {esc(g.title)}"
    if title:
        head = f"<b>{esc(title)}</b> · {esc(g.full)}"
    ok = chosen == q.answer
    lines = [head, f"<i>Вопрос {num} из {total}</i>", "", f"<b>{esc(q.q)}</b>", ""]
    for i, oi in enumerate(order):
        mark = "✅" if oi == q.answer else ("❌" if oi == chosen else "▫️")
        lines.append(f"{mark} {LETTERS[i]}) {esc(q.options[oi])}")
    lines += ["", "👍 <b>Верно!</b>" if ok else "🙅 <b>Неверно.</b>",
              f"💡 {esc(q.explain)}", f"📘 <i>{esc(q.ref)}</i>"]
    text = "\n".join(lines)
    if plain:  # для оценки длины без HTML-тегов
        import re
        return html.unescape(re.sub(r"<[^>]+>", "", text))
    return text
