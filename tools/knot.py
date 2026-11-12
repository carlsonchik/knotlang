"""Общие правила кнотланга v0.7: фонемы, модели склонения, фонотактика.
Используется генератором словаря и поиском кандидатов; тест держит свою копию правил
(чтобы ловить расхождение словаря и правила)."""
VOWELS = set("aeiou")
LAYERS = "iuae"  # зреет, держится, отдаётся, откликается
DIG = ("sh", "ch", "kh", "zh", "ts")

def seg(w):
    out, i = [], 0
    while i < len(w):
        if w[i:i+2] in DIG: out.append(w[i:i+2]); i += 2
        else: out.append(w[i]); i += 1
    return out

def shape(w):
    return "".join("V" if s in VOWELS else "C" for s in seg(w))

def forms(root, model):
    s = seg(root)
    if model == "A":
        vi = [i for i, x in enumerate(s) if x in VOWELS]
        assert len(vi) == 1 and vi[0] > 0 and s[-1] not in VOWELS, (root, model)
        res = []
        for L in LAYERS:
            t = s[:]; t[vi[0]] = L
            w = "".join(t)
            if s[-1] not in ("t", "d"): w += "t"
            res.append(w)
        return res
    if model == "A2":   # гласная меняется в последнем слоге (momor → momurt)
        vi = [i for i, x in enumerate(s) if x in VOWELS][-1]
        res = []
        for L in LAYERS:
            t = s[:]; t[vi] = L
            w = "".join(t)
            if s[-1] not in ("t", "d"): w += "t"
            res.append(w)
        return res
    if model in ("B", "CV", "EXC", "COLOR"):
        return [root + L for L in LAYERS]
    if model == "CVCV":
        return [root[:-1] + L for L in LAYERS]
    if model == "FIX":
        return [root] * 4
    if model == "COLOR_U":
        from base_lex import COLOR_U
        return ["-", COLOR_U[root], "-", "-"]
    raise ValueError(model)

def max_run(w, vowel):
    best = cur = 0
    for x in seg(w):
        cur = cur + 1 if ((x in VOWELS) == vowel) else 0
        best = max(best, cur)
    return best

def phon_errors(w, allow_pt=False):
    e = []
    if max_run(w, True) >= 3: e.append("3+ гласных")
    if max_run(w, False) >= 3: e.append("3+ согласных")
    s = seg(w)
    for a, b in zip(s, s[1:]):
        if a == b and a not in VOWELS and a + b not in ("tt", "kk", "nn"):
            e.append(f"двойное {a}{b}")
    if w.startswith("pt") and not allow_pt: e.append("начальное pt")
    for bad in ("stk", "ptl"):
        if bad in w: e.append(bad)
    return e

def lev1(a, b):
    a, b = seg(a), seg(b)
    if a == b or abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    return any(b[:i] + b[i+1:] == a for i in range(len(b)))
