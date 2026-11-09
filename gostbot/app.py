"""Логика бота-преподавателя по ЕСКД."""
import datetime as dt
import logging
import random
import threading
import time
import uuid

from .bank import LETTERS, answered_caption, esc, question_caption, use_text_buttons
from .tg import TelegramError, inline_kb, reply_kb

log = logging.getLogger("app")

BTN_LEARN = "📚 Учить ГОСТ"
BTN_EXAM = "📝 Экзамен"
BTN_REVIEW = "🔁 Повторение"
BTN_PROGRESS = "📊 Прогресс"
BTN_SETTINGS = "⚙️ Настройки"
BTN_HELP = "ℹ️ Помощь"
MENU_BUTTONS = {BTN_LEARN, BTN_EXAM, BTN_REVIEW, BTN_PROGRESS, BTN_SETTINGS, BTN_HELP}
MAIN_KB = reply_kb([[BTN_LEARN, BTN_EXAM], [BTN_REVIEW, BTN_PROGRESS], [BTN_SETTINGS, BTN_HELP]])

LEARN_SIZE = 10
EXAM_SIZE = 20
REVIEW_SIZE = 15

HELP = (
    "<b>Как пользоваться</b>\n\n"
    f"{BTN_LEARN} — выберите стандарт, прочитайте шпаргалку и пройдите тренировку из "
    f"{LEARN_SIZE} вопросов. После каждого ответа — пояснение и ссылка на пункт ГОСТа.\n\n"
    f"{BTN_EXAM} — {EXAM_SIZE} вопросов по всем стандартам вперемешку, разбор в конце.\n\n"
    f"{BTN_REVIEW} — вопросы, где вы ошиблись, возвращаются через 1, 3, 7, 14 и 30 дней, "
    "пока не закрепятся.\n\n"
    f"{BTN_PROGRESS} — сколько вопросов освоено по каждому стандарту.\n\n"
    f"{BTN_SETTINGS} — «вопрос дня» по утрам и сброс прогресса.\n\n"
    "Нашли ошибку в вопросе? Нажмите «⚠️ Ошибка в вопросе» под пояснением — "
    "сообщение уйдёт составителю.\n\n"
    "Команды: /menu — меню, /stop — прервать тренировку."
)

REPORT_REASONS = ["Неверный правильный ответ", "Картинка не соответствует",
                  "Непонятная формулировка"]


def now_ts():
    return int(time.time())


def bar(frac, width=10):
    full = round(frac * width)
    return "▰" * full + "▱" * (width - full)


def plural(n, one, few, many):
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return one
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14:
        return few
    return many


class App:
    def __init__(self, api, db, bank, config):
        self.api, self.db, self.bank, self.cfg = api, db, bank, config
        self.lock = threading.RLock()

    # ================= точка входа =================
    def handle_update(self, upd):
        with self.lock:
            try:
                if "message" in upd:
                    self.on_message(upd["message"])
                elif "callback_query" in upd:
                    self.on_callback(upd["callback_query"])
            except Exception:
                log.exception("ошибка обработки апдейта %s", upd.get("update_id"))

    # ================= доступ =================
    def _register(self, frm):
        name = " ".join(x for x in (frm.get("first_name"), frm.get("last_name")) if x) or "—"
        self.db.touch_user(frm["id"], name, frm.get("username"))
        return self.db.get_user(frm["id"])

    def is_admin(self, uid):
        return uid in self.cfg.admin_ids

    def has_access(self, user):
        if not self.cfg.access_code or self.is_admin(user["user_id"]):
            return True
        return bool(user["approved"])

    # ================= сообщения =================
    def on_message(self, msg):
        chat = msg["chat"]["id"]
        frm = msg.get("from") or {}
        if msg["chat"].get("type") != "private" or not frm:
            return
        uid = frm["id"]
        user = self._register(frm)
        text = (msg.get("text") or "").strip()

        if not self.has_access(user):
            if text and text == self.cfg.access_code:
                self.db.set_approved(uid)
                self.api.send_message(chat, "Код принят ✅")
                self.welcome(chat, frm)
            else:
                self.api.send_message(chat, "🔒 Бот для конструкторов. Введите код доступа.")
            return

        cmd = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""
        pending = self.db.get_kv(uid, "report_q")
        if pending:
            self.db.set_kv(uid, "report_q", None)
            if text and not cmd and text not in MENU_BUTTONS:
                return self.save_report(chat, uid, pending, text[:1000])
            if cmd == "/cancel":
                return self.api.send_message(chat, "Хорошо, отменено.", reply_markup=MAIN_KB)
        if cmd == "/start" or cmd == "/menu":
            return self.welcome(chat, frm) if cmd == "/start" else self.api.send_message(
                chat, "Главное меню 👇", reply_markup=MAIN_KB)
        if cmd == "/help" or text == BTN_HELP:
            return self.api.send_message(chat, HELP, reply_markup=MAIN_KB)
        if cmd == "/stop":
            return self.finish_session(chat, uid, aborted=True)
        if text == BTN_LEARN or cmd == "/learn":
            return self.show_gost_list(chat)
        if text == BTN_EXAM or cmd == "/exam":
            return self.exam_intro(chat)
        if text == BTN_REVIEW or cmd == "/review":
            return self.start_review(chat, uid)
        if text == BTN_PROGRESS or cmd == "/progress":
            return self.show_progress(chat, uid)
        if text == BTN_SETTINGS or cmd == "/settings":
            return self.show_settings(chat, uid)
        if cmd == "/stats" and self.is_admin(uid):
            return self.admin_stats(chat)
        if cmd == "/reload" and self.is_admin(uid):
            return self.admin_reload(chat)
        if cmd == "/reports" and self.is_admin(uid):
            return self.admin_reports(chat)
        if cmd == "/fixed" and self.is_admin(uid):
            return self.admin_fixed(chat, text.split()[1:])
        self.api.send_message(chat, "Выберите действие в меню 👇", reply_markup=MAIN_KB)

    def welcome(self, chat, frm):
        n_q, n_g = len(self.bank.questions), len(self.bank.gosts)
        self.api.send_message(
            chat,
            f"Здравствуйте, {esc(frm.get('first_name') or 'коллега')}! 👋\n\n"
            "Я — преподаватель по ЕСКД. Помогаю держать в голове требования ГОСТов к чертежам: "
            f"{n_g} {plural(n_g, 'стандарт', 'стандарта', 'стандартов')}, "
            f"{n_q} {plural(n_q, 'вопрос', 'вопроса', 'вопросов')} с картинками "
            "и ссылками на пункты.\n\nНачните с «📚 Учить ГОСТ» или проверьте себя на экзамене.",
            reply_markup=MAIN_KB)

    # ================= список ГОСТов и шпаргалки =================
    def _mastery(self, uid):
        last = self.db.last_results(uid)
        res = {}
        for code in self.bank.gosts:
            qs = self.bank.by_gost(code)
            done = sum(1 for q in qs if last.get(q.id))
            res[code] = (done, len(qs))
        return res

    def gost_list_markup(self, uid):
        mastery = self._mastery(uid)
        rows = []
        for code, g in self.bank.gosts.items():
            done, total = mastery[code]
            pct = f"{round(100 * done / total)}%" if total else "—"
            rows.append([(f"{g.emoji} {g.full.replace('ГОСТ ', '')} {g.title} · {pct}", f"g:{code}")])
        return inline_kb(rows)

    def show_gost_list(self, chat, edit_msg=None):
        text = "<b>Выберите стандарт</b>\nВ скобках — доля освоенных вопросов."
        kb = self.gost_list_markup(chat)  # в личном чате chat_id == user_id
        if edit_msg:
            try:
                return self.api.edit_text(chat, edit_msg, text, reply_markup=kb)
            except TelegramError:
                pass
        self.api.send_message(chat, text, reply_markup=kb)

    def show_gost_card(self, chat, msg_id, code):
        g = self.bank.gosts.get(code)
        if not g:
            return
        n = len(self.bank.by_gost(code))
        text = f"{g.emoji} <b>{esc(g.full)} — {esc(g.title)}</b>\n"
        if g.note:
            text += f"<i>{esc(g.note)}</i>\n"
        text += f"\n{g.cheat.strip()}\n\nВопросов в базе: {n}"
        kb = inline_kb([[(f"▶ Тренировка ({min(LEARN_SIZE, n)} вопр.)", f"s:learn:{code}")],
                        [("⬅ К списку", "g:list")]])
        try:
            self.api.edit_text(chat, msg_id, text, reply_markup=kb)
        except TelegramError:
            self.api.send_message(chat, text, reply_markup=kb)

    # ================= запуск сессий =================
    def _new_session(self, uid, mode, qids, gost=None, title=None):
        orders = {}
        for qid in qids:
            q = self.bank.questions[qid]
            perm = list(range(len(q.options)))
            if not q.fixed:
                random.shuffle(perm)
            orders[qid] = perm
        s = {"sid": uuid.uuid4().hex[:6], "mode": mode, "gost": gost, "title": title,
             "qids": qids, "orders": orders, "idx": 0, "answers": {}, "correct": 0,
             "msg": None, "answered": False, "started": now_ts()}
        self.db.save_session(uid, s)
        return s

    def pick_learn(self, uid, code, n=LEARN_SIZE):
        qs = self.bank.by_gost(code)
        last = self.db.last_results(uid)
        due = set(self.db.due_reviews(uid))
        random.shuffle(qs)
        def prio(q):
            if q.id in due:
                return (0, q.level)
            if q.id not in last:
                return (1, q.level)
            if not last[q.id]:
                return (2, q.level)
            return (3, random.random())
        qs.sort(key=prio)
        return [q.id for q in qs[:n]]

    def pick_exam(self, n=EXAM_SIZE):
        pools = {c: random.sample(self.bank.by_gost(c), len(self.bank.by_gost(c)))
                 for c in self.bank.gosts}
        picked = []
        codes = list(pools)
        random.shuffle(codes)
        while len(picked) < n and any(pools.values()):
            for c in codes:
                if pools[c] and len(picked) < n:
                    picked.append(pools[c].pop().id)
        random.shuffle(picked)
        return picked

    def start_learn(self, chat, uid, code):
        qids = self.pick_learn(uid, code)
        if not qids:
            return self.api.send_message(chat, "По этому стандарту пока нет вопросов.")
        s = self._new_session(uid, "learn", qids, gost=code)
        self.send_question(chat, uid, s)

    def exam_intro(self, chat):
        n = min(EXAM_SIZE, len(self.bank.questions))
        self.api.send_message(
            chat,
            f"📝 <b>Экзамен</b>\n\n{n} вопросов по всем стандартам. Правильные ответы и пояснения — "
            "в конце. Ошибки попадут в «Повторение».\n\nОценка: 90% и выше — отлично, "
            "75% — хорошо, 60% — удовлетворительно.",
            reply_markup=inline_kb([[("▶ Начать экзамен", "s:exam")]]))

    def start_exam(self, chat, uid):
        s = self._new_session(uid, "exam", self.pick_exam(), title="Экзамен")
        self.send_question(chat, uid, s)

    def start_review(self, chat, uid):
        due = [q for q in self.db.due_reviews(uid) if q in self.bank.questions]
        if not due:
            total = self.db.review_count(uid)
            text = "🔁 Сейчас повторять нечего — отлично!"
            if total:
                text += (f"\nНа контроле {total} {plural(total, 'вопрос', 'вопроса', 'вопросов')}, "
                         "они вернутся в свой срок.")
            else:
                text += "\nСюда попадают вопросы, в которых вы ошиблись."
            return self.api.send_message(chat, text, reply_markup=MAIN_KB)
        s = self._new_session(uid, "review", due[:REVIEW_SIZE], title="Повторение")
        self.send_question(chat, uid, s)

    def start_fix(self, chat, uid, qids):
        s = self._new_session(uid, "fix", qids, title="Разбор ошибок")
        self.send_question(chat, uid, s)

    # ================= вопрос / ответ =================
    def send_photo_cached(self, chat, path, caption, kb):
        key = path.name
        mtime = path.stat().st_mtime
        fid = self.db.get_media(key, mtime)
        if fid:
            try:
                return self.api.send_photo(chat, fid, caption=caption, reply_markup=kb)
            except TelegramError as e:
                log.info("file_id устарел для %s: %s", key, e)
                self.db.drop_media(key)
        res = self.api.send_photo(chat, path, caption=caption, reply_markup=kb)
        try:
            self.db.set_media(key, mtime, res["photo"][-1]["file_id"])
        except (KeyError, IndexError, TypeError):
            pass
        return res

    def question_markup(self, s, q):
        order = s["orders"][q.id]
        sid = s["sid"]
        if use_text_buttons(q):
            rows = [[(str(q.options[oi]), f"a:{sid}:{i}")] for i, oi in enumerate(order)]
        else:
            rows = [[(LETTERS[i], f"a:{sid}:{i}") for i in range(len(order))]]
        rows.append([("⏹ Завершить", f"x:{sid}")])
        return inline_kb(rows)

    def send_question(self, chat, uid, s):
        qid = s["qids"][s["idx"]]
        q = self.bank.questions[qid]
        g = self.bank.gosts[q.gost]
        cap = question_caption(q, g, s["idx"] + 1, len(s["qids"]), s["orders"][qid], s.get("title"))
        res = self.send_photo_cached(chat, self.bank.image_path(q), cap, self.question_markup(s, q))
        s["msg"] = res["message_id"]
        s["answered"] = False
        self.db.save_session(uid, s)

    def on_answer(self, cb, chat, uid, sid, k):
        s = self.db.load_session(uid)
        if not s or s["sid"] != sid or s["answered"]:
            return self.api.answer_callback(cb["id"], "Этот вопрос уже закрыт")
        qid = s["qids"][s["idx"]]
        q = self.bank.questions.get(qid)
        if q is None:
            return self.api.answer_callback(cb["id"], "Вопрос удалён из базы")
        order = s["orders"][qid]
        if not 0 <= k < len(order):
            return self.api.answer_callback(cb["id"])
        chosen = order[k]
        ok = chosen == q.answer
        s["answers"][qid] = chosen
        s["correct"] += int(ok)
        s["answered"] = True
        self.db.record_answer(uid, qid, ok, s["mode"])
        self.db.save_session(uid, s)
        last = s["idx"] + 1 >= len(s["qids"])
        msg_id = cb["message"]["message_id"]
        g = self.bank.gosts[q.gost]

        if s["mode"] == "exam":
            self.api.answer_callback(cb["id"], "Ответ принят")
            short = question_caption(q, g, s["idx"] + 1, len(s["qids"]), order, s.get("title"))
            self._safe_edit_caption(chat, msg_id, short + f"\n\n☑️ Ваш ответ: {LETTERS[k]}) "
                                    f"{esc(q.options[chosen])}", None)
            return self.next_question(chat, uid)

        self.api.answer_callback(cb["id"], "✅ Верно!" if ok else "❌ Неверно")
        cap = answered_caption(q, g, s["idx"] + 1, len(s["qids"]), order, chosen,
                               title=s.get("title"))
        btn = ("🏁 Итоги", f"n:{sid}") if last else ("Далее ▶", f"n:{sid}")
        rows = [[btn]] if last else [[btn], [("⏹ Завершить", f"x:{sid}")]]
        rows.append([("⚠️ Ошибка в вопросе", f"rep:{qid}")])
        kb = inline_kb(rows)
        self._safe_edit_caption(chat, msg_id, cap, kb)

    def _safe_edit_caption(self, chat, msg_id, cap, kb):
        try:
            self.api.edit_caption(chat, msg_id, cap, reply_markup=kb)
        except TelegramError as e:
            if "not modified" in e.description:
                return
            log.warning("не удалось изменить подпись: %s", e)
            self.api.send_message(chat, cap, reply_markup=kb)

    def next_question(self, chat, uid, sid=None, cb=None):
        s = self.db.load_session(uid)
        if not s or (sid and s["sid"] != sid):
            if cb:
                self.api.answer_callback(cb["id"], "Тренировка уже завершена")
            return
        if cb:
            self.api.answer_callback(cb["id"])
        if not s["answered"]:
            return
        if cb and s.get("msg"):  # убираем кнопки «Далее» у старого сообщения
            try:
                self.api.edit_markup(chat, s["msg"], None)
            except TelegramError:
                pass
        s["idx"] += 1
        if s["idx"] >= len(s["qids"]):
            return self.finish_session(chat, uid, s=s)
        self.db.save_session(uid, s)
        self.send_question(chat, uid, s)

    def finish_session(self, chat, uid, s=None, aborted=False, cb=None):
        s = s or self.db.load_session(uid)
        if cb:
            self.api.answer_callback(cb["id"])
        if not s:
            if aborted:
                self.api.send_message(chat, "Активной тренировки нет.", reply_markup=MAIN_KB)
            return
        self.db.drop_session(uid)
        if s.get("msg"):
            try:
                self.api.edit_markup(chat, s["msg"], None)
            except TelegramError:
                pass
        answered = len(s["answers"])
        correct = s["correct"]
        if answered == 0:
            return self.api.send_message(chat, "Тренировка прервана.", reply_markup=MAIN_KB)
        pct = correct / answered
        lines = []
        if s["mode"] == "exam":
            if not aborted:
                self.db.record_exam(uid, answered, correct)
            grade = ("отлично 🏆" if pct >= .9 else "хорошо 👍" if pct >= .75 else
                     "удовлетворительно 🙂" if pct >= .6 else "нужно подтянуть 📚")
            lines.append(f"📝 <b>Экзамен {'прерван' if aborted else 'завершён'}</b>")
            lines.append(f"Результат: <b>{correct} из {answered}</b> ({round(pct * 100)}%) — {grade}")
        else:
            title = {"learn": "Тренировка", "review": "Повторение", "fix": "Разбор ошибок",
                     "daily": "Вопрос дня"}.get(s["mode"], "Тренировка")
            lines.append(f"🏁 <b>{title}: итоги</b>" + (" (прервано)" if aborted else ""))
            lines.append(f"Верно: <b>{correct} из {answered}</b> ({round(pct * 100)}%)  {bar(pct)}")
        wrong = [qid for qid, ch in s["answers"].items()
                 if qid in self.bank.questions and ch != self.bank.questions[qid].answer]
        if wrong:
            lines.append("")
            lines.append("<b>Ошибки:</b>")
            for qid in wrong[:12]:
                q = self.bank.questions[qid]
                lines.append(f"• {esc(q.q)}\n   ✅ {esc(q.correct_text)}  <i>({esc(q.ref)})</i>")
            if len(wrong) > 12:
                lines.append(f"…и ещё {len(wrong) - 12}")
            lines.append("\nЭти вопросы вернутся в «🔁 Повторение» завтра.")
        rows = []
        if wrong and s["mode"] == "exam":
            self.db.set_kv(uid, "exam_wrong", wrong[:20])
            rows.append([("🔍 Разобрать ошибки с пояснениями", "fix:last")])
        if s["mode"] == "learn" and s.get("gost"):
            rows.append([("🔄 Ещё тренировка", f"s:learn:{s['gost']}"), ("📚 К списку", "g:list")])
        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:3990] + "…"
        self.api.send_message(chat, text, reply_markup=inline_kb(rows) if rows else MAIN_KB)

    # ================= прогресс, настройки =================
    def show_progress(self, chat, uid):
        mastery = self._mastery(uid)
        n, c = self.db.totals(uid)
        lines = ["📊 <b>Ваш прогресс</b>", ""]
        all_done = sum(d for d, _ in mastery.values())
        all_total = sum(t for _, t in mastery.values()) or 1
        lines.append(f"Освоено: <b>{all_done} из {all_total}</b>  {bar(all_done / all_total)}")
        lines.append("")
        for code, g in self.bank.gosts.items():
            d, t = mastery[code]
            lines.append(f"{g.emoji} {esc(g.full)} — {d}/{t}  {bar(d / t if t else 0, 8)}")
        lines.append("")
        lines.append(f"Всего ответов: {n}, верных: {c}" + (f" ({round(100 * c / n)}%)" if n else ""))
        ex = self.db.exam_stats(uid)
        if ex and ex["n"]:
            lines.append(f"Экзаменов: {ex['n']}, лучший результат: {round(ex['best'] * 100)}%")
        rc = self.db.review_count(uid)
        due = len(self.db.due_reviews(uid))
        lines.append(f"На повторении: {rc} (сегодня к повторению: {due})")
        self.api.send_message(chat, "\n".join(lines), reply_markup=MAIN_KB)

    def settings_markup(self, user):
        daily = "✅ Вопрос дня: включён" if user["daily"] else "⬜ Вопрос дня: выключен"
        return inline_kb([[(daily, "set:daily")], [("🗑 Сбросить мой прогресс", "rs:ask")]])

    def show_settings(self, chat, uid, edit_msg=None):
        user = self.db.get_user(uid)
        text = (f"⚙️ <b>Настройки</b>\n\nВопрос дня приходит в {self.cfg.daily_hour}:00. "
                "Если есть вопросы на повторение — бот напомнит о них.")
        kb = self.settings_markup(user)
        if edit_msg:
            try:
                return self.api.edit_text(chat, edit_msg, text, reply_markup=kb)
            except TelegramError:
                pass
        self.api.send_message(chat, text, reply_markup=kb)

    # ================= админ =================
    def admin_stats(self, chat):
        users = self.db.all_users()
        total_q = len(self.bank.questions)
        lines = [f"👥 <b>Пользователи: {len(users)}</b>", ""]
        for u in users:
            n, c = self.db.totals(u["user_id"])
            mastered = sum(d for d, _ in self._mastery(u["user_id"]).values())
            ex = self.db.exam_stats(u["user_id"])
            best = f", экз. {round(ex['best'] * 100)}%" if ex and ex["n"] else ""
            nick = f" @{u['username']}" if u["username"] else ""
            acc = f"{round(100 * c / n)}%" if n else "—"
            lines.append(f"• {esc(u['name'])}{esc(nick)}: освоено {mastered}/{total_q}, "
                         f"ответов {n}, точность {acc}{best}")
        text = "\n".join(lines)
        for i in range(0, len(text), 4000):
            self.api.send_message(chat, text[i:i + 4000])

    def save_report(self, chat, uid, qid, text):
        self.db.add_report(uid, qid, text)
        self.api.send_message(chat, "Спасибо! Сообщение передано составителю вопросов 🙏",
                              reply_markup=MAIN_KB)
        u = self.db.get_user(uid)
        who = esc(u["name"]) + (f" (@{esc(u['username'])})" if u["username"] else "")
        q = self.bank.questions.get(qid)
        body = (f"⚠️ <b>Жалоба на вопрос {esc(qid)}</b> от {who}\n«{esc(text)}»")
        if q:
            body += (f"\n\n<i>{esc(q.q)}</i>\nОтвет в базе: {esc(q.correct_text)}\n"
                     f"{esc(q.ref)}")
        for admin in self.cfg.admin_ids:
            if admin == uid:
                continue
            try:
                self.api.send_message(admin, body[:4000])
            except Exception as e:  # админ не запускал бота и т. п. — жалоба всё равно сохранена
                log.warning("жалоба админу %s: %s", admin, e)

    def admin_reports(self, chat):
        rows = self.db.open_reports()
        if not rows:
            return self.api.send_message(chat, "Открытых жалоб нет ✅")
        lines = [f"⚠️ <b>Открытые жалобы: {len(rows)}</b>", ""]
        for r in rows:
            who = esc(r["name"] or str(r["user_id"]))
            lines.append(f"• <code>{esc(r['qid'])}</code> — {esc(r['text'])} <i>({who})</i>")
        lines.append("\nПосле правки файла вопросов: /reload, затем /fixed &lt;id&gt;")
        self.api.send_message(chat, "\n".join(lines)[:4000])

    def admin_fixed(self, chat, args):
        if not args:
            return self.api.send_message(chat, "Укажите номер вопроса: /fixed 305-101")
        n = sum(self.db.resolve_reports(a) for a in args)
        self.api.send_message(chat, f"Закрыто жалоб: {n}")

    def admin_reload(self, chat):
        try:
            self.bank.load()
            self.api.send_message(chat, f"✅ База перезагружена: {len(self.bank.questions)} вопросов.")
        except Exception as e:
            self.api.send_message(chat, f"⚠️ Ошибка, оставлена старая база:\n{esc(str(e))[:3500]}")

    # ================= callback-кнопки =================
    def on_callback(self, cb):
        frm = cb["from"]
        uid = frm["id"]
        msg = cb.get("message")
        if not msg:
            return self.api.answer_callback(cb["id"])
        chat = msg["chat"]["id"]
        user = self._register(frm)
        if not self.has_access(user):
            return self.api.answer_callback(cb["id"], "Нет доступа", show_alert=True)
        data = cb.get("data") or ""
        parts = data.split(":")
        kind = parts[0]

        if kind == "a" and len(parts) == 3:
            try:
                k = int(parts[2])
            except ValueError:
                return self.api.answer_callback(cb["id"])
            return self.on_answer(cb, chat, uid, parts[1], k)
        if kind == "n":
            return self.next_question(chat, uid, sid=parts[1], cb=cb)
        if kind == "x":
            s = self.db.load_session(uid)
            if s and s["sid"] == parts[1]:
                return self.finish_session(chat, uid, s=s, aborted=True, cb=cb)
            return self.api.answer_callback(cb["id"], "Уже завершено")
        if kind == "rep" and len(parts) == 2 and parts[1] in self.bank.questions:
            self.api.answer_callback(cb["id"])
            rows = [[(r, f"rp:{parts[1]}:{i}")] for i, r in enumerate(REPORT_REASONS)]
            rows.append([("✍️ Написать своими словами", f"rp:{parts[1]}:t")])
            return self.api.send_message(
                chat, f"Что не так с вопросом <code>{esc(parts[1])}</code>?",
                reply_markup=inline_kb(rows))
        if kind == "rp" and len(parts) == 3:
            self.api.answer_callback(cb["id"])
            qid = parts[1]
            if parts[2] == "t":
                self.db.set_kv(uid, "report_q", qid)
                return self.api.edit_text(chat, msg["message_id"],
                                          "Опишите ошибку одним сообщением (или /cancel).")
            try:
                reason = REPORT_REASONS[int(parts[2])]
            except (ValueError, IndexError):
                return
            self.api.edit_markup(chat, msg["message_id"], None)
            return self.save_report(chat, uid, qid, reason)
        self.api.answer_callback(cb["id"])
        if data == "g:list":
            return self.show_gost_list(chat, edit_msg=msg["message_id"])
        if kind == "g":
            return self.show_gost_card(chat, msg["message_id"], parts[1])
        if data.startswith("s:learn:"):
            return self.start_learn(chat, uid, parts[2])
        if data == "s:exam":
            try:
                self.api.edit_markup(chat, msg["message_id"], None)
            except TelegramError:
                pass
            return self.start_exam(chat, uid)
        if data == "s:review":
            return self.start_review(chat, uid)
        if kind == "fix":
            qids = [q for q in self.db.get_kv(uid, "exam_wrong", []) if q in self.bank.questions]
            if qids:
                return self.start_fix(chat, uid, qids)
        if data == "set:daily":
            self.db.set_daily(uid, 0 if user["daily"] else 1)
            return self.show_settings(chat, uid, edit_msg=msg["message_id"])
        if data == "rs:ask":
            return self.api.edit_text(chat, msg["message_id"],
                                      "Точно сбросить весь прогресс, историю и экзамены?",
                                      reply_markup=inline_kb([[("Да, сбросить", "rs:yes"),
                                                               ("Отмена", "rs:no")]]))
        if data == "rs:yes":
            self.db.reset_progress(uid)
            return self.api.edit_text(chat, msg["message_id"], "Прогресс сброшен.")
        if data == "rs:no":
            return self.show_settings(chat, uid, edit_msg=msg["message_id"])

    # ================= вопрос дня =================
    DAILY_UNTIL = 21  # если ПК был выключен в DAILY_HOUR — догоняем, но не позже 21:00

    def daily_tick(self, now=None):
        now = now or dt.datetime.now()
        if not (self.cfg.daily_hour <= now.hour < max(self.DAILY_UNTIL, self.cfg.daily_hour + 1)):
            return
        today = now.strftime("%Y-%m-%d")
        with self.lock:
            for u in self.db.daily_users(today):
                uid = u["user_id"]
                if not self.has_access(u):
                    self.db.mark_daily_sent(uid, today)
                    continue
                try:
                    self._send_daily(uid)
                except TelegramError as e:  # ответ Telegram: повторять бессмысленно
                    log.warning("вопрос дня для %s: %s", uid, e)
                    if e.code == 403:  # пользователь заблокировал бота
                        self.db.set_daily(uid, 0)
                except Exception as e:  # нет сети — попробуем в следующую минуту
                    log.warning("вопрос дня для %s отложен (нет связи): %s", uid, e)
                    return
                self.db.mark_daily_sent(uid, today)

    def _send_daily(self, uid):
        due = len(self.db.due_reviews(uid))
        active = self.db.load_session(uid)
        if due:
            self.api.send_message(
                uid, f"☀️ Доброе утро! На повторение: {due} "
                     f"{plural(due, 'вопрос', 'вопроса', 'вопросов')}.",
                reply_markup=inline_kb([[("🔁 Повторить", "s:review")]]))
            return
        if active:
            self.api.send_message(uid, "☀️ Доброе утро! У вас есть незавершённая тренировка — "
                                       "продолжим? Нажмите «Далее» в последнем вопросе.")
            return
        last = self.db.last_results(uid)
        pool = [q for q in self.bank.questions if q not in last] or list(self.bank.questions)
        s = self._new_session(uid, "daily", [random.choice(pool)], title="Вопрос дня ☀️")
        self.send_question(uid, uid, s)
