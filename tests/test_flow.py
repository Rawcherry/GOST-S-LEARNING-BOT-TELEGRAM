"""Сквозной тест логики бота на поддельном Telegram API (без сети).

python tests/test_flow.py
"""
import datetime as dt
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot import Config  # noqa: E402
from gostbot.app import App, BTN_EXAM, BTN_LEARN, BTN_PROGRESS, BTN_REVIEW, BTN_SETTINGS  # noqa: E402
from gostbot.bank import CAPTION_LIMIT, Bank  # noqa: E402
from gostbot.db import DB  # noqa: E402
from gostbot.tg import TelegramError  # noqa: E402


class FakeAPI:
    def __init__(self):
        self.log = []
        self.msg_id = 100
        self.photo_uploads = 0
        self.fail_file_id_once = False

    def _new(self, chat, kind, text, kb):
        self.msg_id += 1
        self.log.append(dict(kind=kind, chat=chat, id=self.msg_id, text=text, kb=kb))
        return {"message_id": self.msg_id}

    def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML"):
        assert len(text) <= 4096, "сообщение длиннее 4096"
        self._check_html(text)
        return self._new(chat_id, "msg", text, reply_markup)

    def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode="HTML"):
        assert caption is None or len(re.sub(r"<[^>]+>", "", caption)) <= CAPTION_LIMIT
        self._check_html(caption or "")
        if isinstance(photo, str):
            if self.fail_file_id_once:
                self.fail_file_id_once = False
                raise TelegramError("sendPhoto", 400, "wrong file identifier")
        else:
            assert photo.exists(), photo
            self.photo_uploads += 1
        r = self._new(chat_id, "photo", caption, reply_markup)
        r["photo"] = [{"file_id": "small"}, {"file_id": f"FID-{self.msg_id}"}]
        return r

    def edit_caption(self, chat_id, message_id, caption, reply_markup=None, parse_mode="HTML"):
        assert len(re.sub(r"<[^>]+>", "", caption)) <= CAPTION_LIMIT, "подпись > 1024"
        self._check_html(caption)
        self.log.append(dict(kind="edit_caption", chat=chat_id, id=message_id, text=caption,
                             kb=reply_markup))

    def edit_text(self, chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        self._check_html(text)
        self.log.append(dict(kind="edit_text", chat=chat_id, id=message_id, text=text, kb=reply_markup))

    def edit_markup(self, chat_id, message_id, reply_markup=None):
        self.log.append(dict(kind="edit_markup", chat=chat_id, id=message_id, kb=reply_markup))

    def answer_callback(self, cid, text=None, show_alert=False):
        self.log.append(dict(kind="cb_answer", text=text))

    def set_commands(self, c):
        pass

    @staticmethod
    def _check_html(s):
        # только разрешённые теги и они сбалансированы
        tags = re.findall(r"</?([a-z]+)[^>]*>", s)
        for t in tags:
            assert t in ("b", "i", "u", "s", "code", "pre", "a"), f"тег {t}"
        for t in set(tags):
            assert len(re.findall(f"<{t}>", s)) == len(re.findall(f"</{t}>", s)), f"незакрыт {t}"
        stripped = re.sub(r"</?(b|i|u|s|code|pre|a)>", "", s)
        assert "<" not in stripped.replace("&lt;", ""), f"неэкранированный < в: {s[:80]}"

    def last(self, kind=None):
        for e in reversed(self.log):
            if kind is None or e["kind"] == kind:
                return e


U = {"id": 555, "first_name": "Иван", "username": "ivan"}
ADMIN = {"id": 1, "first_name": "Админ"}


def msg(text, frm=U):
    return {"update_id": 1, "message": {"message_id": 1, "chat": {"id": frm["id"], "type": "private"},
                                        "from": frm, "text": text}}


def cb(data, message_id, frm=U):
    return {"update_id": 2, "callback_query": {"id": "c", "from": frm, "data": data,
                                               "message": {"message_id": message_id,
                                                           "chat": {"id": frm["id"]}}}}


def buttons(kb):
    return [b for row in kb["inline_keyboard"] for b in row] if kb else []


def answer_current(app, api, uid, correct=True):
    """Нажать вариант в последнем вопросе (верный или неверный)."""
    s = app.db.load_session(uid)
    qid = s["qids"][s["idx"]]
    q = app.bank.questions[qid]
    order = s["orders"][qid]
    target = q.answer if correct else next(i for i in range(len(q.options)) if i != q.answer)
    k = order.index(target)
    photo = api.last("photo")
    data = f"a:{s['sid']}:{k}"
    assert data in [b["callback_data"] for b in buttons(photo["kb"])], "нет такой кнопки"
    app.handle_update(cb(data, photo["id"]))
    return qid


def main():
    tmp = Path(tempfile.mkdtemp())
    api = FakeAPI()
    cfg = Config(token="x:y", admin_ids={1}, access_code="", daily_hour=9)
    db = DB(tmp / "t.sqlite3")
    bank = Bank(ROOT / "data", ROOT / "images")
    app = App(api, db, bank, cfg)
    uid = U["id"]

    # --- старт и меню
    app.handle_update(msg("/start"))
    assert "преподаватель" in api.last("msg")["text"]
    app.handle_update(msg(BTN_LEARN))
    kb = api.last("msg")["kb"]
    assert len(buttons(kb)) == len(bank.gosts)
    list_msg = api.last("msg")["id"]

    # --- карточка и тренировка по 2.303
    app.handle_update(cb("g:2.303", list_msg))
    card = api.last("edit_text")
    assert "Линии" in card["text"] and "s/3" in card["text"]
    app.handle_update(cb("s:learn:2.303", list_msg))
    s = db.load_session(uid)
    assert s["mode"] == "learn" and len(s["qids"]) == 10
    wrong_ids = []
    for i in range(10):
        ok = i % 3 != 0
        qid = answer_current(app, api, uid, correct=ok)
        if not ok:
            wrong_ids.append(qid)
        ed = api.last("edit_caption")
        assert ("Верно" in ed["text"]) == ok
        assert "📘" in ed["text"]
        nxt = buttons(ed["kb"])[0]["callback_data"]
        # повторное нажатие на тот же вопрос игнорируется
        app.handle_update(cb(f"a:{s['sid']}:0", ed["id"]))
        assert api.last("cb_answer")["text"] == "Этот вопрос уже закрыт"
        app.handle_update(cb(nxt, ed["id"]))
    res = api.last("msg")["text"]
    assert "Тренировка: итоги" in res and "6 из 10" in res, res
    assert db.load_session(uid) is None
    assert db.review_count(uid) == 4
    assert api.photo_uploads <= 10

    # --- повторение: сейчас ничего не «созрело», через сутки — 4 вопроса
    app.handle_update(msg(BTN_REVIEW))
    assert "повторять нечего" in api.last("msg")["text"]
    for q in wrong_ids:
        db._exec("UPDATE review SET due=? WHERE user_id=? AND qid=?", (int(time.time()) - 1, uid, q))
    app.handle_update(msg(BTN_REVIEW))
    s = db.load_session(uid)
    assert s["mode"] == "review" and sorted(s["qids"]) == sorted(wrong_ids)
    for _ in range(len(wrong_ids)):
        answer_current(app, api, uid, correct=True)
        app.handle_update(cb(buttons(api.last("edit_caption")["kb"])[0]["callback_data"],
                             api.last("edit_caption")["id"]))
    assert "Повторение: итоги" in api.last("msg")["text"]
    boxes = [r["box"] for r in db._all("SELECT box FROM review WHERE user_id=?", (uid,))]
    assert boxes == [2, 2, 2, 2], boxes

    # --- экзамен: 20 вопросов, разные ГОСТы, без пояснений по ходу
    app.handle_update(msg(BTN_EXAM))
    app.handle_update(cb("s:exam", api.last("msg")["id"]))
    s = db.load_session(uid)
    assert len(s["qids"]) == 20 and len(set(s["qids"])) == 20
    gosts_in_exam = {bank.questions[q].gost for q in s["qids"]}
    assert len(gosts_in_exam) == len(bank.gosts), gosts_in_exam
    for i in range(20):
        answer_current(app, api, uid, correct=(i >= 5))
        assert "Ваш ответ" in api.last("edit_caption")["text"]
        assert "💡" not in api.last("edit_caption")["text"]
    res = api.last("msg")
    assert "15 из 20" in res["text"] and "хорошо" in res["text"], res["text"]
    fix_btn = [b for b in buttons(res["kb"]) if b["callback_data"] == "fix:last"]
    assert fix_btn
    app.handle_update(cb("fix:last", res["id"]))
    assert db.load_session(uid)["mode"] == "fix" and len(db.load_session(uid)["qids"]) == 5

    # --- /stop прерывает
    answer_current(app, api, uid, correct=True)
    app.handle_update(msg("/stop"))
    assert "Разбор ошибок: итоги</b> (прервано)" in api.last("msg")["text"]

    # --- прогресс и настройки
    app.handle_update(msg(BTN_PROGRESS))
    p = api.last("msg")["text"]
    assert "Освоено" in p and "Экзаменов: 1" in p, p
    app.handle_update(msg(BTN_SETTINGS))
    sm = api.last("msg")
    app.handle_update(cb("set:daily", sm["id"]))
    assert db.get_user(uid)["daily"] == 1

    # --- вопрос дня: в 9 часов приходит, второй раз за день — нет
    db._exec("DELETE FROM review WHERE user_id=?", (uid,))
    n_before = len(api.log)
    app.daily_tick(dt.datetime(2026, 10, 27, 8, 30))
    assert len(api.log) == n_before
    app.daily_tick(dt.datetime(2026, 10, 27, 9, 1))
    assert api.last("photo")["text"].startswith("<b>Вопрос дня")
    n_after = len(api.log)
    app.daily_tick(dt.datetime(2026, 10, 27, 9, 30))
    assert len(api.log) == n_after
    # нет сети в 9:00 — вопрос не теряется, уходит при следующей попытке
    app.finish_session(uid, uid)
    real_send = api.send_photo
    def offline(*a, **k):
        raise ConnectionError("нет сети")
    api.send_photo = offline
    app.daily_tick(dt.datetime(2026, 10, 28, 9, 0))
    assert db.get_user(uid)["last_daily"] != "2026-10-28"
    api.send_photo = real_send
    app.daily_tick(dt.datetime(2026, 10, 28, 9, 1))
    assert db.get_user(uid)["last_daily"] == "2026-10-28"
    # ПК включили в 11:00 — вопрос дня догоняет; в 22:00 уже не шлём
    app.finish_session(uid, uid)
    app.daily_tick(dt.datetime(2026, 10, 29, 11, 0))
    assert db.get_user(uid)["last_daily"] == "2026-10-29"
    app.daily_tick(dt.datetime(2026, 10, 30, 22, 0))
    assert db.get_user(uid)["last_daily"] == "2026-10-29"
    app.finish_session(uid, uid)

    # --- жалоба на вопрос: быстрая причина и свой текст, уведомление админу, /reports, /fixed
    app.handle_update(msg(BTN_LEARN))
    app.handle_update(cb("s:learn:2.311", api.last("msg")["id"]))
    q1 = answer_current(app, api, uid)
    rep_btn = [b for b in buttons(api.last("edit_caption")["kb"]) if b["callback_data"].startswith("rep:")]
    assert rep_btn and rep_btn[0]["callback_data"] == f"rep:{q1}"
    app.handle_update(cb(f"rep:{q1}", api.last("edit_caption")["id"]))
    menu = api.last("msg")
    app.handle_update(cb(f"rp:{q1}:0", menu["id"]))
    admin_note = [e for e in api.log if e["kind"] == "msg" and e["chat"] == 1][-1]
    assert f"Жалоба на вопрос {q1}" in admin_note["text"] and "Неверный правильный ответ" in admin_note["text"]
    app.handle_update(cb(f"rep:{q1}", api.last("edit_caption")["id"]))
    app.handle_update(cb(f"rp:{q1}:t", api.last("msg")["id"]))
    app.handle_update(msg("На картинке нет метки 5"))
    assert "Спасибо" in [e for e in api.log if e["kind"] == "msg" and e["chat"] == uid][-1]["text"]
    app.handle_update(msg("/reports", ADMIN))
    assert "Открытые жалобы: 2" in api.last("msg")["text"] and "метки 5" in api.last("msg")["text"]
    app.handle_update(msg(f"/fixed {q1}", ADMIN))
    assert "Закрыто жалоб: 2" in api.last("msg")["text"]
    app.handle_update(msg("/reports", ADMIN))
    assert "нет" in api.last("msg")["text"]
    # ожидание текста жалобы снимается нажатием меню
    app.handle_update(cb(f"rep:{q1}", api.last("edit_caption")["id"]))
    app.handle_update(cb(f"rp:{q1}:t", api.last("msg")["id"]))
    app.handle_update(msg(BTN_PROGRESS))
    assert "Ваш прогресс" in api.last("msg")["text"]
    app.finish_session(uid, uid)

    # --- кэш file_id: повторный показ той же картинки не загружает файл
    uploads = api.photo_uploads
    app.handle_update(msg(BTN_EXAM))
    app.handle_update(cb("s:exam", api.last("msg")["id"]))
    for _ in range(20):
        answer_current(app, api, uid)
    assert api.photo_uploads - uploads < 20
    # устаревший file_id — перезагрузка
    api.fail_file_id_once = True
    app.handle_update(msg(BTN_EXAM))
    app.handle_update(cb("s:exam", api.last("msg")["id"]))
    assert db.load_session(uid)["msg"] is not None

    # --- код доступа
    cfg.access_code = "РТИ2026"
    stranger = {"id": 777, "first_name": "Гость"}
    app.handle_update(msg("/start", stranger))
    assert "код доступа" in api.last("msg")["text"]
    app.handle_update(msg(BTN_LEARN, stranger))
    assert "код доступа" in api.last("msg")["text"]
    app.handle_update(msg("РТИ2026", stranger))
    assert db.get_user(777)["approved"] == 1
    app.handle_update(msg(BTN_LEARN))   # старый пользователь без кода теперь тоже должен ввести код
    assert "код доступа" in api.last("msg")["text"]
    cfg.access_code = ""

    # --- админ
    app.handle_update(msg("/stats", ADMIN))
    assert "Пользователи" in api.last("msg")["text"]
    app.handle_update(msg("/reload", ADMIN))
    assert "перезагружена" in api.last("msg")["text"]
    app.handle_update(msg("/stats"))  # не админ
    assert "Пользователи" not in api.last("msg")["text"]

    # --- сброс прогресса
    app.handle_update(msg(BTN_SETTINGS))
    sm = api.last("msg")
    app.handle_update(cb("rs:ask", sm["id"]))
    app.handle_update(cb("rs:yes", sm["id"]))
    assert db.totals(uid) == (0, 0)

    # --- каждый вопрос банка: подпись до и после ответа влезает, кнопки ≤ 64 байт
    from gostbot.bank import answered_caption, question_caption
    for q in bank.questions.values():
        g = bank.gosts[q.gost]
        order = list(range(len(q.options)))
        for ch in order:
            c = answered_caption(q, g, 10, 20, order, ch, title="Разбор ошибок")
            assert len(re.sub(r"<[^>]+>", "", c)) <= CAPTION_LIMIT, q.id
        question_caption(q, g, 1, 20, order)
        sess = {"sid": "abcdef", "orders": {q.id: order}}
        for b in buttons(app.question_markup(sess, q)):
            assert len(b["callback_data"].encode()) <= 64

    print("OK: все проверки пройдены,", len(api.log), "вызовов API")


if __name__ == "__main__":
    main()

