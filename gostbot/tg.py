"""Минимальный клиент Telegram Bot API (long polling) на requests."""
import json
import logging
import time

import requests

log = logging.getLogger("tg")


class TelegramError(Exception):
    def __init__(self, method, code, description):
        super().__init__(f"{method}: {code} {description}")
        self.code = code
        self.description = description or ""


class TelegramAPI:
    def __init__(self, token, base_url="https://api.telegram.org", session=None):
        self.url = f"{base_url}/bot{token}/"
        self.http = session or requests.Session()

    def call(self, method, files=None, http_timeout=30, **params):
        data = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                v = "true" if v else "false"
            data[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
        for attempt in range(3):
            try:
                if files:
                    r = self.http.post(self.url + method, data=data, files=files, timeout=http_timeout)
                else:
                    r = self.http.post(self.url + method, data=data, timeout=http_timeout)
                payload = r.json()
            except (requests.RequestException, ValueError) as e:
                if attempt == 2:
                    raise
                log.warning("%s: сеть: %s, повтор", method, e)
                time.sleep(2 + attempt * 3)
                continue
            if payload.get("ok"):
                return payload.get("result")
            code = payload.get("error_code")
            desc = payload.get("description", "")
            if code == 429:  # флуд-контроль
                wait = (payload.get("parameters") or {}).get("retry_after", 3)
                time.sleep(wait + 1)
                continue
            raise TelegramError(method, code, desc)
        raise TelegramError(method, 0, "too many retries")

    # --- обёртки ---
    def get_updates(self, offset, timeout=50):
        return self.call("getUpdates", http_timeout=timeout + 15, offset=offset, timeout=timeout,
                         allowed_updates=["message", "callback_query"])

    def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML"):
        return self.call("sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode,
                         reply_markup=reply_markup, disable_web_page_preview=True)

    def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode="HTML"):
        """photo — file_id (str) или путь к файлу (pathlib.Path)."""
        if isinstance(photo, str):
            return self.call("sendPhoto", chat_id=chat_id, photo=photo, caption=caption,
                             parse_mode=parse_mode, reply_markup=reply_markup)
        with open(photo, "rb") as f:
            return self.call("sendPhoto", files={"photo": (photo.name, f, "image/png")},
                             chat_id=chat_id, caption=caption, parse_mode=parse_mode,
                             reply_markup=reply_markup, http_timeout=60)

    def edit_caption(self, chat_id, message_id, caption, reply_markup=None, parse_mode="HTML"):
        return self.call("editMessageCaption", chat_id=chat_id, message_id=message_id,
                         caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)

    def edit_text(self, chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        return self.call("editMessageText", chat_id=chat_id, message_id=message_id, text=text,
                         parse_mode=parse_mode, reply_markup=reply_markup,
                         disable_web_page_preview=True)

    def edit_markup(self, chat_id, message_id, reply_markup=None):
        return self.call("editMessageReplyMarkup", chat_id=chat_id, message_id=message_id,
                         reply_markup=reply_markup)

    def answer_callback(self, callback_id, text=None, show_alert=False):
        try:
            return self.call("answerCallbackQuery", callback_query_id=callback_id, text=text,
                             show_alert=show_alert)
        except TelegramError as e:  # устаревший callback — не страшно
            log.debug("answerCallbackQuery: %s", e)

    def set_commands(self, commands):
        return self.call("setMyCommands", commands=commands)


def inline_kb(rows):
    """rows: [[(text, data), ...], ...]"""
    return {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in rows]}


def reply_kb(rows):
    return {"keyboard": [[{"text": t} for t in row] for row in rows], "resize_keyboard": True,
            "is_persistent": True}
