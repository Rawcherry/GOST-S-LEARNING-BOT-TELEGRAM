"""Автозапуск бота при входе в Windows (без прав администратора).

python install_autostart.py          — включить автозапуск и сразу запустить бота в фоне
python install_autostart.py remove   — выключить автозапуск
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "GOST-bot.vbs"


def startup_dir():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        sys.exit("Этот скрипт работает только в Windows.")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def pythonw():
    exe = Path(sys.executable)
    w = exe.with_name("pythonw.exe")
    return w if w.exists() else exe


def install():
    target = startup_dir() / NAME
    cmd = f'"{pythonw()}" "{ROOT / "run_forever.py"}"'
    vbs = ('Set sh = CreateObject("WScript.Shell")\r\n'
           f'sh.CurrentDirectory = "{ROOT}"\r\n'
           f'sh.Run "{cmd.replace(chr(34), chr(34) * 2)}", 0, False\r\n')
    # UTF-16 с BOM — чтобы Windows Script Host понял кириллицу в путях
    target.write_bytes(b"\xff\xfe" + vbs.encode("utf-16-le"))
    print(f"Автозапуск включён: {target}")
    subprocess.Popen(["wscript.exe", str(target)])
    print("Бот запущен в фоне. Журнал: bot.log и watchdog.log в папке бота.")


def remove():
    target = startup_dir() / NAME
    if target.exists():
        target.unlink()
        print("Автозапуск выключен. Работающий бот можно остановить в Диспетчере задач (pythonw.exe).")
    else:
        print("Автозапуск и так не настроен.")


if __name__ == "__main__":
    remove() if (len(sys.argv) > 1 and sys.argv[1] == "remove") else install()
