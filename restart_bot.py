"""Перезапуск бота в фоне (после обновления файлов).

Останавливает фоновый бот этой папки (сторожа run_forever.py и запущенный им bot.py)
и запускает заново без окна. Другие программы Python не трогает: процессы ищутся
по «замкам» бота — локальным портам 47321 (сторож) и 47322 (бот).
Окно run_bot.bat, если оно открыто, закройте сами.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PS = r"""
$ports = 47321, 47322
$ids = @()
foreach ($p in $ports) {
  $c = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
  if ($c) { $ids += $c.OwningProcess }
}
$ids = $ids | Sort-Object -Unique
foreach ($id in $ids) {
  Get-CimInstance Win32_Process -Filter "ParentProcessId=$id" | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
}
Write-Output ("stopped: " + ($ids -join ","))
"""


def main():
    if sys.platform != "win32":
        sys.exit("Скрипт для Windows.")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", PS],
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    time.sleep(2)
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    subprocess.Popen([str(pyw if pyw.exists() else exe), str(ROOT / "run_forever.py")], cwd=ROOT,
                     creationflags=0x08000000 | 0x00000008)  # без окна, отдельно от консоли
    print("Бот перезапущен в фоне. Проверьте: напишите ему /start.")


if __name__ == "__main__":
    main()
