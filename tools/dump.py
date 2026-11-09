"""Краткий список вопросов для проверки: python tools/dump.py data/questions/2_307_b.yaml"""
import sys, yaml
for f in sys.argv[1:]:
    for q in yaml.safe_load(open(f, encoding="utf-8")):
        wrong = " | ".join(str(o) for i, o in enumerate(q["options"]) if i != q["answer"])
        print(f'{q["id"]} [{q.get("ref","")}] {q.get("image","")}\n  Q: {q["q"]}\n  ✔ {q["options"][q["answer"]]}\n  ✘ {wrong}')
