"""Генерация всех картинок для вопросов.

python tools/gen_images.py            — все картинки в папку images/
python tools/gen_images.py 303 311    — только картинки с этими префиксами
"""
import importlib
import pkgutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE.parent / "images"

import figs  # noqa: E402


def all_figs():
    reg = {}
    for m in pkgutil.iter_modules(figs.__path__):
        mod = importlib.import_module(f"figs.{m.name}")
        reg.update(getattr(mod, "FIGS", {}))
    return reg


def main(prefixes):
    OUT.mkdir(exist_ok=True)
    reg = all_figs()
    n = 0
    for name, fn in sorted(reg.items()):
        if prefixes and not any(name.startswith(p) for p in prefixes):
            continue
        fn(OUT / name)
        n += 1
    print(f"Готово: {n} картинок в {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
