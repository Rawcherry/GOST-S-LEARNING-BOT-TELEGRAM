"""Запуск: python bot.py   (настройки — в файле .env рядом)."""
import logging
import os
import logging.handlers
import re
import socket
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from gostbot.app import App
from gostbot.bank import Bank
from gostbot.db import DB
from gostbot.tg import TelegramAPI, TelegramError

ROOT = Path(__file__).resolve().parent
LOCK_PORT = 47322  # «замок»: на одном компьютере работает только одна копия бота


@dataclass
class Config:
    token: str = ""
    admin_ids: set = field(default_factory=set)
    access_code: str = ""
    daily_hour: int = 9
    api_url: str = "https://api.telegram.org"


def load_config(path=None):
    path = path or Path(os.environ.get("GOSTBOT_ENV", ROOT / ".env"))
    cfg = Config()
    if not path.exists():
        sys.exit(f"Нет файла {path}. Скопируйте .env.example в .env и впишите токен.")
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = (x.strip() for x in line.split("=", 1))
        v = v.strip('"').strip("'")
        if k == "BOT_TOKEN":
            cfg.token = v
        elif k == "ADMIN_IDS":
            cfg.admin_ids = {int(x) for x in v.replace(";", ",").split(",") if x.strip().isdigit()}
        elif k == "ACCESS_CODE":
            cfg.access_code = v
        elif k == "DAILY_HOUR" and v.isdigit():
            cfg.daily_hour = int(v)
        elif k == "API_URL" and v:
            cfg.api_url = v.rstrip("/")
    if not cfg.token or ":" not in cfg.token:
        sys.exit("В .env не указан BOT_TOKEN (получите его у @BotFather).")
    return cfg


class HideToken(logging.Filter):
    """Убирает токен бота из журналов (сетевые ошибки содержат адрес с токеном)."""
    pattern = re.compile(r"bot\d+:[A-Za-z0-9_-]+")

    def filter(self, record):
        msg = record.getMessage()
        if self.pattern.search(msg):
            record.msg, record.args = self.pattern.sub("bot<TOKEN>", msg), ()
        return True


class HideTokenFormatter(logging.Formatter):
    def formatException(self, ei):
        return HideToken.pattern.sub("bot<TOKEN>", super().formatException(ei))


def setup_logging():
    fmt = HideTokenFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fh = logging.handlers.RotatingFileHandler(ROOT / "bot.log", maxBytes=2_000_000, backupCount=3,
                                              encoding="utf-8")
    fh.setFormatter(fmt)
    fh.addFilter(HideToken())
    root.addHandler(fh)
    # в консоль пишем только при ручном запуске (под сторожем всё уже есть в bot.log)
    if sys.stderr and not os.environ.get("GOSTBOT_WATCHDOG"):
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.addFilter(HideToken())
        root.addHandler(sh)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def single_instance():
    """Вторая копия на том же компьютере не стартует (иначе Telegram отвечает 409)."""
    lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock.bind(("127.0.0.1", LOCK_PORT))
    except OSError:
        msg = ("Бот уже запущен на этом компьютере (в фоне или в другом окне). "
               "Вторая копия не нужна — закройте это окно.")
        logging.getLogger("bot").warning(msg)
        print(msg)
        sys.exit(3)
    return lock


def wait_for_telegram(api, log):
    """Ждём сеть при старте, а не падаем (после включения ПК интернет появляется не сразу)."""
    delay = 5
    while True:
        try:
            return api.call("getMe")
        except TelegramError as e:
            if e.code == 401:
                sys.exit("Неверный BOT_TOKEN.")
            log.warning("getMe: %s", e)
        except Exception as e:
            log.warning("Нет связи с Telegram, жду %d с: %s", delay, e)
        time.sleep(delay)
        delay = min(120, delay * 2)


def daily_loop(app, stop):
    while not stop.is_set():
        try:
            app.daily_tick()
        except Exception:
            logging.exception("ошибка рассылки вопроса дня")
        stop.wait(60)


def main():
    setup_logging()
    cfg = load_config()
    _lock = single_instance()  # noqa: F841 — держим, пока процесс жив
    api = TelegramAPI(cfg.token, base_url=cfg.api_url)
    db = DB(Path(os.environ.get("GOSTBOT_DB", ROOT / "bot.sqlite3")))
    bank = Bank(ROOT / "data", ROOT / "images")
    app = App(api, db, bank, cfg)
    log = logging.getLogger("bot")
    me = wait_for_telegram(api, log)
    log.info("Бот @%s запущен: %d ГОСТов, %d вопросов", me.get("username"), len(bank.gosts),
             len(bank.questions))
    try:
        api.set_commands([
            {"command": "menu", "description": "Главное меню"},
            {"command": "learn", "description": "Учить ГОСТ"},
            {"command": "exam", "description": "Экзамен"},
            {"command": "review", "description": "Повторение ошибок"},
            {"command": "progress", "description": "Мой прогресс"},
            {"command": "stop", "description": "Прервать тренировку"},
            {"command": "help", "description": "Помощь"},
        ])
    except TelegramError as e:
        log.warning("setMyCommands: %s", e)

    stop = threading.Event()
    threading.Thread(target=daily_loop, args=(app, stop), daemon=True).start()

    offset = None
    errors = 0
    errors409 = 0
    while True:
        try:
            updates = api.get_updates(offset)
            errors = errors409 = 0
            for upd in updates:
                offset = upd["update_id"] + 1
                app.handle_update(upd)
        except KeyboardInterrupt:
            stop.set()
            log.info("Остановлено.")
            break
        except TelegramError as e:
            if e.code == 401:
                sys.exit("Неверный BOT_TOKEN.")
            if e.code == 409:
                errors409 += 1
                if errors409 in (1, 10) or errors409 % 120 == 0:  # не засоряем журнал
                    log.error("Telegram 409: %s. С этим токеном уже работает другая копия бота "
                              "(другое окно или другой компьютер). Жду.", e.description)
                time.sleep(30)
                continue
            errors += 1
            log.warning("Telegram: %s", e)
            time.sleep(min(60, 2 ** errors))
        except Exception as e:  # сеть пропала и т. п.
            errors += 1
            log.warning("Нет связи: %s", e)
            time.sleep(min(60, 2 ** errors))


if __name__ == "__main__":
    main()
