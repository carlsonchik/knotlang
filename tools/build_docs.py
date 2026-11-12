#!/usr/bin/env python3
"""Раскрывает строки «@@ фраза || перевод» в шаблонах tools/src/*.src.md в блоки
с подстрочником (лейпцигские правила, русские метки) и пишет файлы в корень репо.
Разбор берётся из tests/test_knotlang.py — тот же разборщик, что проверяет тексты."""
import importlib.util, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("t", ROOT/"tests"/"test_knotlang.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

def block(sentence, tr):
    t.errors.clear()
    segs, gls = t.gloss(sentence, "build")
    if t.errors: sys.exit(f"ОШИБКА в «{sentence}»: {t.errors}")
    w = [max(len(a), len(b)) for a, b in zip(segs, gls)]
    l1 = "  ".join(a.ljust(n) for a, n in zip(segs, w)).rstrip()
    l2 = "  ".join(b.ljust(n) for b, n in zip(gls, w)).rstrip()
    return [f"> {sentence}", "", "```", l1, l2, f"«{tr}»", "```"]

for src in sorted((ROOT/"tools"/"src").glob("*.src.md")):
    out = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if line.startswith("@@ "):
            s, tr = [x.strip() for x in line[3:].split("||")]
            out += block(s, tr)
        else:
            out.append(line)
    name = src.name.replace(".src.md", ".md")
    (ROOT/name).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("written", name)
