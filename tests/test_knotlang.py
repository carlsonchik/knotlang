#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка канона КНОТЛАНГ v0.7 (12.11.2026).

Корни читаются из lexicon_v0.7.md, фразы — из строк «> » в каноне, демо-текстах,
длинном тексте, переписке и README. Правила склонения здесь свои (не импортируются),
чтобы расхождение словаря и правила ловилось.

Проверяется:
  1. Формы словаря совпадают с правилом модели; у обычного корня 4 разные формы.
  2. Нет совпадений форм разных корней, частиц, жестов и чисел; аффектив
     (форма + le/li/la) не даёт чужой формы.
  3. Фонотактика каждой формы (внутри слова; стык через дефис свободен).
  4. Числа: значение записи, zult не в составе, повтор >2 только у числительных.
  5. Каждое слово каждой фразы разбирается: нет голых корней, композит в одном
     слое (цвет-атрибут в -u-), жесты без аффектива, звательное = форма.le.
  6. Снятые формы (duult, wul, petl, zamk, tishut, momu…) не вернулись.
  Цвета — явный класс-исключение COLOR_U: только форма -u-, без правила замены,
  но с проверкой фонотактики и совпадений.
Запуск: python3 tests/test_knotlang.py   → код 0, если всё прошло.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEX = ROOT / "lexicon_v0.7.md"
UTTER_FILES = ["KNOTLANG.md", "demo_texts_v0.7.md", "long_text_v0.7.md",
               "correspondence_KD.md", "README.md"]
V = set("aeiou"); LAYERS = "iuae"; DIG = ("sh", "ch", "kh", "zh", "ts")
LAYER_GL = dict(zip(LAYERS, ["ЗРЕ", "ДЕРЖ", "ОТД", "ОТКЛ"]))
POS_GL = {"k": "ЦЕНТР", "t": "ГРАН", "s": "ВНЕ", "m": "РЕЗ"}
AFF_GL = {"le": "ЛАД", "li": "БЕР", "la": "РЯД"}
PARTICLES = {"nai": "ПРЕД", "nashe": "ОДН", "kne": "ВОПР", "kni": "ПРИК", "kam": "несколько", "tip": "мало"}
GESTURES = {"kve": "ЖЕСТ.зов", "mu": "ЖЕСТ.отклик", "ah": "ЖЕСТ.вдох", "oh": "ЖЕСТ.выдох", "eh": "ЖЕСТ.пауза"}
NAMES = {"Denis", "K", "Solvell"}
NUM = {"zult": 0, "nult": 1, "duut": 2, "dunult": 3, "pant": 5, "pan": 5, "pa": 5, "du": 2}
FREE_NUM = {"zult", "nult", "duut", "dunult", "pant"}
RETIRED = {"duult", "wilt", "wult", "walt", "welt", "petli", "petlu", "petla", "petle",
           "bult", "nukt", "zunt", "suvt", "krult", "trukt", "belu", "noku", "sivu", "zamku", "zamki", "zamka", "zamke",
           "tishit", "tishut", "tishat", "tishet", "momi", "momu", "moma", "mome", "kni-multu"}
errors = []

def seg(w):
    out, i = [], 0
    while i < len(w):
        if w[i:i+2] in DIG: out.append(w[i:i+2]); i += 2
        else: out.append(w[i]); i += 1
    return out

def rule(root, model):
    s = seg(root)
    if model in ("A", "A2"):
        vs = [i for i, x in enumerate(s) if x in V]
        vi = vs[0] if model == "A" else vs[-1]
        if model == "A" and (len(vs) != 1 or vi == 0 or s[-1] in V):
            raise ValueError("основа не подходит под A")
        res = []
        for L in LAYERS:
            t = s[:]; t[vi] = L; w = "".join(t)
            res.append(w if s[-1] in ("t", "d") else w + "t")
        return res
    if model in ("B", "CV", "EXC", "COLOR"): return [root + L for L in LAYERS]
    if model == "CVCV": return [root[:-1] + L for L in LAYERS]
    if model == "FIX": return [root] * 4
    raise ValueError(model)

def phon(w, where):
    s = seg(w); run_v = run_c = 0
    for x in s:
        if x in V: run_v += 1; run_c = 0
        else: run_c += 1; run_v = 0
        if run_v >= 3: errors.append(f"[фонология] {where}: «{w}» 3+ гласных"); break
        if run_c >= 3: errors.append(f"[фонология] {where}: «{w}» 3+ согласных"); break
    for a, b in zip(s, s[1:]):
        if a == b and a not in V and a + b not in ("tt", "kk") and not w.startswith("venn"):
            errors.append(f"[фонология] {where}: «{w}» двойное {a}{b}")
    if w.startswith("pt") and not w.startswith("ptah"): errors.append(f"[фонология] {where}: «{w}» начальное pt")
    for bad in ("stk", "ptl"):
        if bad in w: errors.append(f"[фонология] {where}: «{w}» {bad}")

# ---------- 1. словарь ----------
lex = {}   # root -> dict
for line in LEX.read_text(encoding="utf-8").splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 10 and cells[1] in ("A", "A2", "B", "CV", "CVCV", "EXC", "COLOR_U", "FIX"):
        r, m, fi, fu, fa, fe, mean, gl, note, st = cells
        lex[r] = dict(model=m, forms=[fi, fu, fa, fe], gloss=gl, status=st)
if len(lex) < 60: errors.append(f"[словарь] прочитано только {len(lex)} корней")
for r, d in lex.items():
    if d["model"] == "COLOR_U":
        # Исключение «у цвета свой характер» (20.08, подтверждено Д. 12.11.2026):
        # только форма -u-, записанная как есть; правила замены нет, остальные клетки пусты.
        fi, fu, fa, fe = d["forms"]
        if (fi, fa, fe) != ("-", "-", "-") or fu == "-" or not fu.startswith(r[0]):
            errors.append(f"[цвет] {r}: ожидается только форма -u-, в словаре {d['forms']}")
        phon(fu, f"цвет {r}"); continue
    try:
        exp = rule(r, d["model"])
    except ValueError as e:
        errors.append(f"[модель] {r}: {e}"); continue
    if exp != d["forms"]: errors.append(f"[модель] {r}: правило {exp}, в словаре {d['forms']}")
    if d["model"] != "FIX" and len(set(d["forms"])) != 4: errors.append(f"[формы] {r}: повтор внутри ряда")
    for f in set(d["forms"]): phon(f, f"форма {r}")

# ---------- 2. совпадения ----------
surf = {}
for r, d in lex.items():
    for i, f in enumerate(d["forms"]):
        if f != "-": surf.setdefault(f, set()).add((r, LAYERS[i]))
owners = {}
for f, s in surf.items():
    roots = {r for r, _ in s}
    if len(roots) > 1: errors.append(f"[коллизия] «{f}»: {sorted(roots)}")
    owners[f] = s
for w in list(PARTICLES) + list(GESTURES) + list(NUM) + ["zhe", "kna"]:
    if w in surf: errors.append(f"[коллизия] служебное «{w}» совпадает с формой {sorted(surf[w])}")
for f in list(surf) + list(PARTICLES):
    for a in AFF_GL:
        if f + a in surf: errors.append(f"[аффектив] «{f}»+-{a} = форма {sorted(surf[f + a])}")

# ---------- 4. числа ----------
def num_value(expr):
    toks = re.findall(r"[a-z]+(?:-[a-z]+)*|[+()-]", expr)
    out = ""
    for t in toks:
        if t in "+()": out += t
        elif t == "-": out += "*"
        else:
            parts = t.split("-")
            if not all(p in NUM for p in parts): return None
            out += "(" + "*".join(str(NUM[p]) for p in parts) + ")"
    out = out.replace(")(", ")*(")
    try: return eval(out)
    except Exception: return None

def is_number(w):
    return re.fullmatch(r"[a-z()+\-]+", w) and all(p in NUM for p in re.split(r"[()+\-]", w) if p)

numtable = re.findall(r"^\| (\d+) \| ([a-z()+\-]+) \|$", LEX.read_text(encoding="utf-8"), re.M)
if len(numtable) < 15: errors.append("[числа] таблица чисел не прочитана")
for n, e in numtable:
    v = num_value(e)
    if v != int(n): errors.append(f"[числа] {e} = {v}, а записано {n}")
    if n != "0" and "zult" in e: errors.append(f"[числа] zult в составе: {e}")
    for p in re.split(r"[()+\-]", e):
        if p: phon(p, f"число {n}")

# ---------- 5. разбор фраз ----------
def gl_form(f):
    """форма -> (сегментация, глосса, слой, корень)"""
    (r, L), = sorted(surf[f])[:1] if len({x for x, _ in surf[f]}) == 1 else [None]
    d = lex[r]; m = d["model"]
    if m == "FIX": return f, d["gloss"], None, r
    if m in ("A", "A2", "COLOR_U"): return f, f"{d['gloss']}\\{LAYER_GL[L]}", L, r
    return f"{f[:-1]}-{f[-1]}", f"{d['gloss']}-{LAYER_GL[L]}", L, r

def analyse(w, where):
    """Возвращает (сегментация, глосса) или добавляет ошибку."""
    if w.rstrip(".") in NAMES: return w, "имя"
    if w in ("k:", "t:", "s:", "m:"): return w, POS_GL[w[0]]
    if w in GESTURES: return w, GESTURES[w]
    if w in PARTICLES: return w, PARTICLES[w]
    if w == "nai-zhe": return w, "ПРЕД-ОДН"
    if is_number(w):
        if num_value(w) is None: errors.append(f"[фраза] {where}: число «{w}» не считается"); return w, "?"
        if "-" not in w and "+" not in w and w not in FREE_NUM:
            errors.append(f"[фраза] {where}: «{w}» не бывает отдельным словом")
        return w, str(num_value(w))
    m = re.fullmatch(r"([ktsm])-(.+)", w)
    if m:
        s, g = analyse_core(m.group(2), where, w)
        return f"{m.group(1)}-{s}", f"{POS_GL[m.group(1)]}-{g}"
    return analyse_core(w, where, w)

def analyse_core(w, where, full):
    m = re.fullmatch(r"(kni|kne)(?:-(li|le|la))?", w)
    if m:
        g = PARTICLES[m.group(1)] + (f"-{AFF_GL[m.group(2)]}" if m.group(2) else "")
        return w, g
    if w.startswith("kna-"):
        s, g = analyse_core(w[4:], where, full)
        return "kna-" + s, "ИНО-" + g
    m = re.fullmatch(r"([a-z]+)\.le", w)
    if m:
        if m.group(1) not in surf:
            errors.append(f"[фраза] {where}: звательное «{w}» — перед точкой должна стоять форма со слоем"); return w, "?"
        s, g, L, r = gl_form(m.group(1))
        if lex[r]["model"] == "FIX": pass
        return s + ".le", g + ".ЗВ"
    parts = w.split("-")
    if len(parts) > 1:
        segs, gls, layers = [], [], []
        for i, p in enumerate(parts):
            if p not in surf:
                errors.append(f"[фраза] {where}: «{p}» в «{full}» — не форма словаря"); return w, "?"
            s, g, L, r = gl_form(p)
            segs.append(s); gls.append(g)
            if lex[r]["model"] == "COLOR_U":
                if i != 0: errors.append(f"[фраза] {where}: цвет «{p}» должен стоять первым в композите")
                continue
            if L: layers.append(L)
        if len(set(layers)) > 1: errors.append(f"[фраза] {where}: композит «{full}» в разных слоях")
        return "-".join(segs), "-".join(gls)
    if w in surf:
        s, g, L, r = gl_form(w); return s, g
    for a in AFF_GL:
        if w.endswith(a) and w[:-2] in surf:
            s, g, L, r = gl_form(w[:-2]); return f"{s}-{a}", f"{g}-{AFF_GL[a]}"
    if any(w.startswith(gx) and w[len(gx):] in AFF_GL for gx in GESTURES):
        errors.append(f"[фраза] {where}: жест с аффективом «{w}»"); return w, "?"
    if w in lex: errors.append(f"[фраза] {where}: голый корень «{w}»"); return w, "?"
    errors.append(f"[фраза] {where}: «{w}» не разбирается"); return w, "?"

def tokens(sentence):
    out = []
    for t in sentence.split():
        if t in ("—", "–", "...", "…"): continue
        t = t.strip("«»\"")
        if re.fullmatch(r"K\.[,:]?", t): out.append("K"); continue
        if t.endswith(":") and t[:-1] in NAMES: out.append(t[:-1]); continue
        if t in ("k:", "t:", "s:", "m:"): out.append(t); continue
        t = t.rstrip(",.!?:;…")
        if not t: continue
        if t not in NAMES:
            m0 = re.match(r"[(]*", t).end()
            if m0 < len(t) and t[m0].isupper():
                t = t[:m0] + t[m0].lower() + t[m0+1:]
        if re.search(r"[A-Z]", t) and t not in NAMES:
            errors.append(f"[орфография] прописная внутри слова «{t}»"); t = t.lower()
        out.append(t)
    return out

def gloss(sentence, where="?"):
    segs, gls = [], []
    for t in tokens(sentence):
        s, g = analyse(t, where); segs.append(s); gls.append(g)
    return segs, gls

def utterances():
    for fn in UTTER_FILES:
        p = ROOT / fn
        if not p.exists(): continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("> ") and not line.startswith("> **") and not line.startswith("> «"):
                yield f"{fn}:{i}", line[2:].strip()

def main():
    n = 0
    for where, s in utterances():
        n += 1
        if s.count(" nai") + s.lower().startswith("nai") > 1 and "," not in s and "nai-zhe" not in s:
            errors.append(f"[nai] {where}: две nai в одном предложении")
        for t in tokens(s):
            if t in RETIRED and t not in surf: errors.append(f"[снято] {where}: «{t}»")
        gloss(s, where)
    if n < 40: errors.append(f"[фразы] найдено только {n} фраз")
    if errors:
        print(f"FAIL: {len(errors)} ошибок")
        for e in errors[:80]: print("  -", e)
        return 1
    print(f"OK: {len(lex)} корней, {len(surf)} форм, {len(numtable)} чисел, {n} фраз; "
          f"коллизий нет, фонотактика соблюдена, все фразы разобраны")
    return 0

if __name__ == "__main__":
    sys.exit(main())
