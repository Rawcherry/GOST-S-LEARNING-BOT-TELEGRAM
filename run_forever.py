"""Сторож: запускает bot.py и перезапускает его, если он упал или пропала сеть.

Запускается автоматически при входе в Windows (см. install_autostart.py).
Второй экземпляр не стартует — сторож держит «замок» на локальном порту.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCK_PORT = 47321


def main():
    lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock.bind(("127.0.0.1", LOCK_PORT))
    except OSError:
        return  # уже запущен
    python = Path(sys.executable)
    # под pythonw окна консоли нет; сам бот запускаем тем же интерпретатором
    wlog = ROOT / "watchdog.log"
    if wlog.exists() and wlog.stat().st_size > 1_000_000:  # старый журнал больше не нужен целиком
        wlog.replace(ROOT / "watchdog.old.log")
    log = open(wlog, "a", encoding="utf-8")
    env = dict(os.environ, GOSTBOT_WATCHDOG="1", PYTHONIOENCODING="utf-8")
    fails = 0
    while True:
        started = time.time()
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} запуск бота\n")
        log.flush()
        flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
        code = subprocess.call([str(python), str(ROOT / "bot.py")], cwd=ROOT,
                               stdout=subprocess.DEVNULL, stderr=log, creationflags=flags, env=env)
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} бот завершился с кодом {code}\n")
        log.flush()
        if code == 3:  # бот сообщил, что уже запущен другой копией — ждём дольше
            time.sleep(300)
            continue
        fails = fails + 1 if time.time() - started < 120 else 0
        time.sleep(min(300, 10 * (fails + 1)))  # 10 с, 20 с … не чаще раза в 5 мин при частых падениях


if __name__ == "__main__":
    main()
