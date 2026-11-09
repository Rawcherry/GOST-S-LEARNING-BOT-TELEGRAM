"""Удалить вопросы по id из YAML-файла, сохранив форматирование остальных: python tools/drop_ids.py file id1 id2 ..."""
import sys
p, drop = sys.argv[1], {f'"{x}"' for x in sys.argv[2:]}
txt = open(p, encoding="utf-8").read()
head, *items = txt.split("\n- id: ")
keep = [b for b in items if b.split("\n", 1)[0].strip() not in drop]
open(p, "w", encoding="utf-8").write(head + "".join("\n- id: " + b for b in keep))
print(p, len(items), "->", len(keep))
