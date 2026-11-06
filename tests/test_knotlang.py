#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke-тест КНОТЛАНГ v0.6.4 — лексикон и фонология.

ВНИМАНИЕ: это smoke-тест, а не вычитыватель словаря. Список ROOTS задан
вручную и синхронизируется с каноном v0.6.4 и dictionary_v0.6.md вручную.
Кандидаты (knot_parts_v0.6.md, interjections_v0.6.md) в список НЕ входят —
они не норматив. Междометия (звуки-жесты) не флектируются и в проверках
омонимии как корни не участвуют. Цвета — подмодель только -u-, не четыре слоя.

Проверяет:
  1. У каждого нормативного корня ровно 4 РАЗНЫЕ формы слоёв (исключение:
     предельные fix-слова nul/vit/mil — все формы совпадают).
  2. Фонологию всех форм: нет 3+ гласных подряд, нет 3+ согласных подряд
     (по звукам: диграфы sh/ch/kh = один согласный), нет запрещённых кластеров,
     двойные согласные — только tt/kk (+ задокументированные исключения).
  3. Отсутствие омонимических коллизий между формами разных корней.
  4. Суффиксную модель: помеченные CVC-корни дают формы на -i/-u/-a/-e.
  5. Запреты: zult не входит в составные числа; тройное повторение основы
     запрещено; kni-vult-multa снят (16.10.2026).

Запуск:  python3 tests/test_knotlang.py
Выход:   0 — все проверки прошли; 1 — найдены ошибки.
"""

VOWELS = "aeiou"
# Канон Ч.IV.3: sh/ch/kh — один звук. ts/zh — из исторической фонологии v0.4;
# в живом лексиконе не встречаются, схлопывание их не мешает проверке.
DIGRAPHS = ("sh", "ch", "kh", "ts", "zh")

# Двойные согласные внутри формы: разрешены tt/kk + исключения (задокументированы)
DOUBLE_OK = {"tt", "kk", "nn"}  # nn — только venn (кандидат консилиума)
DOUBLE_EXCEPTIONS = {"vennu", "venni", "venna", "venne"}  # venn: nn внутри основы

# Корни: модель + формы [зреет, держится, отдаётся, откликается]
# Модели: "A-t" (тип A на -t, флексия), "B" (тип B, суффиксы),
#         "suff" (суффиксная подмодель для CVC), "vowel" (основа на гласную),
#         "fix" (неизменяемое/предельное), "hist" (историческая форма)
ROOTS = {
    # --- Ядро канона (Часть II) ---
    "knot": ("A-t", ["knit", "knut", "knat", "knet"]),
    "rod":  ("A", ["rid", "rud", "rad", "red"]),  # на -d: без лишнего -t
    "okn":  ("suff", ["okni", "oknu", "okna", "okne"]),
    "grad": ("B", ["gradi", "gradu", "grada", "grade"]),
    "mil":  ("fix", ["mil", "mil", "mil", "mil"]),  # предельное, 14.10.2026
    "wul":  ("A-t", ["wilt", "wult", "walt", "welt"]),
    "ast":  ("suff", ["asti", "astu", "asta", "aste"]),
    "sen":  ("A-t", ["sint", "sunt", "sant", "sent"]),
    "vedr": ("B", ["vedri", "vedru", "vedra", "vedre"]),
    "mo":   ("vowel", ["moi", "mou", "moa", "moe"]),
    "ten":  ("A-t", ["tint", "tunt", "tant", "tent"]),
    "veh":  ("B", ["vehi", "vehu", "veha", "vehe"]),
    "lum":  ("A-t", ["limt", "lumt", "lamt", "lemt"]),
    "nul":  ("fix", ["nul", "nul", "nul", "nul"]),
    "vit":  ("fix", ["vit", "vit", "vit", "vit"]),  # предельное слово (легенда vit)
    "tish": ("B", ["tishit", "tishut", "tishat", "tishet"]),  # шипящие: наращение -t
    "vel":  ("A-t", ["vilt", "vult", "valt", "velt"]),
    "var":  ("A-t", ["virt", "vurt", "vart", "vert"]),
    "kafe": ("B", ["kafei", "kafeu", "kafea", "kafee"]),  # морф. искл.: удвоение
    "momor": ("B", ["momi", "momu", "moma", "mome"]),  # почтипредельное: ряд словаря §12.2
    # --- Миро (§12) ---
    "mor":  ("A-t", ["mirt", "murt", "mart", "mert"]),
    "sol":  ("A-t", ["silt", "sult", "salt", "selt"]),
    "tul":  ("A-t", ["tilt", "tult", "talt", "telt"]),
    "der":  ("A-t", ["dirt", "durt", "dart", "dert"]),
    "tor":  ("A-t", ["tirt", "turt", "tart", "tert"]),
    "dil":  ("A-t", ["dilt", "dult", "dalt", "delt"]),
    "kap":  ("A-t", ["kipt", "kupt", "kapt", "kept"]),
    "krep": ("B", ["krepi", "krepu", "krepa", "krepe"]),
    # --- Бытовое ядро (§15); rad снят — радость = khush (коллизия с rod→rad) ---
    "sut":  ("A-t", ["sit", "sut", "sat", "set"]),
    "pit":  ("A-t", ["pit", "put", "pat", "pet"]),
    "hod":  ("suff", ["hodi", "hodu", "hoda", "hode"]),
    "rech": ("B", ["rechi", "rechu", "recha", "reche"]),
    "zret": ("B", ["zreti", "zretu", "zreta", "zrete"]),
    "chut": ("B", ["chuti", "chutu", "chuta", "chute"]),
    "mat":  ("A-t", ["mit", "mut", "mat", "met"]),
    "tat":  ("A-t", ["tit", "tut", "tat", "tet"]),
    "det":  ("A-t", ["dit", "dut", "dat", "det"]),
    "khush": ("suff", ["khushi", "khushu", "khusha", "khushe"]),
    "tug":  ("suff", ["tugi", "tugu", "tuga", "tuge"]),
    "trep": ("B", ["trepi", "trepu", "trepa", "trepe"]),
    "bol":  ("suff", ["boli", "bolu", "bola", "bole"]),
    "den":  ("suff", ["deni", "denu", "dena", "dene"]),
    # --- Связки (§13) ---
    "rawi": ("vowel", ["rawi", "rawu", "rawa", "rawe"]),
    "hel":  ("A-t", ["hilt", "hult", "halt", "helt"]),
    "kvel": ("B", ["kveli", "kvelu", "kvela", "kvele"]),
    "plet": ("B", ["pleti", "pletu", "pleta", "plete"]),
    "drem": ("B", ["dremi", "dremu", "drema", "dreme"]),
    # --- Миро/роды ---
    "kor":  ("suff", ["kori", "koru", "kora", "kore"]),
    "gor":  ("suff", ["gori", "goru", "gora", "gore"]),
    "neb":  ("suff", ["nebi", "nebu", "neba", "nebe"]),
    "venn": ("suff", ["venni", "vennu", "venna", "venne"]),
    "pret": ("suff", ["preti", "pretu", "preta", "prete"]),
    "cha":  ("vowel", ["chai", "chau", "chaa", "chae"]),
    "ptah": ("B", ["ptahi", "ptahu", "ptaha", "ptahe"]),  # фонет. искл. (pt)
}

# Исторические формы (не должны участвовать в коллизиях как норма, но фонологию проходят)
HISTORICAL = ["vultu", "wulte", "sent", "vedru", "vedra", "kniu"]

# Цвета: подмодель только -u- (словарь §12.3). Полного ряда канон не даёт.
COLORS = {
    "lur": "lurt",
    "zan": "zant",
    "amr": "amrut",
    "krel": "krelut",
    "siv": "sivut",
    "dun": "dunt",
    "vip": "vupt",
    "brun": "brunt",
    "nok": "nokt",
    "bel": "belt",
    "trek": "trekut",
}

# Квантификаторы без засвидетельствованного четырёхформного ряда (словарь §6.1).
QUANTIFIERS = ["ves", "veves", "mult", "kam", "tip"]

# Междометия (звуки-жесты, вне морфологии): не флектируются, в омонимии не участвуют
INTERJECTIONS = ["kve", "mu", "ah", "oh", "eh"]  # кандидаты служебного слоя (interjections_v0.6.md)

# Числовые формы (базовые + конструкции)
NUMBERS = {
    "0": "zult", "1": "nult", "2": "duut", "3": "dunult", "4": "du-duut",
    "5": "pant", "5m": "pan", "10": "duult-pan", "25": "pa-pan",
    "26": "pa-pan+nult", "100": "du-duut-pa-pan", "125": "pa-pa-pan",
    "135": "(pa-pan+duult)-pan", "3125": "pa-pa-pa-pa-pan",
}

errors = []


def sounds(word):
    """Слово как последовательность звуков: диграфы схлопываются в один."""
    w = word.lower().replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    out = []
    i = 0
    while i < len(w):
        two = w[i:i+2]
        if two in DIGRAPHS:
            out.append(two)
            i += 2
        else:
            out.append(w[i])
            i += 1
    return out


def vowel_clusters(snd):
    """Максимальная длина подряд идущих гласных звуков."""
    best = cur = 0
    for s in snd:
        if s in VOWELS:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def consonant_clusters(snd):
    """Максимальная длина подряд идущих согласных звуков."""
    best = cur = 0
    for s in snd:
        if s not in VOWELS:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def check_phonology(word, where):
    # Маркеры -, +, () — границы/паузы: кластеры считаем по сегментам,
    # внутри сегмента согласные соединяются, через маркер — нет (просодия: пауза как слой).
    segments = []
    for part in word.replace("(", " ").replace(")", " ").replace("+", " ").split():
        for sub in part.split("-"):
            segments.append(sub)
    for seg in segments:
        snd = sounds(seg)
        if vowel_clusters(snd) >= 3:
            errors.append(f"[фонология] {where} «{word}» (сегмент «{seg}»): 3+ гласных подряд")
        if consonant_clusters(snd) >= 3:
            errors.append(f"[фонология] {where} «{word}» (сегмент «{seg}»): 3+ согласных подряд (по звукам)")
        # двойные согласные внутри сегмента
        for i in range(len(snd) - 1):
            a, b = snd[i], snd[i+1]
            if a == b and a not in VOWELS and a not in DIGRAPHS and (a + a) not in DOUBLE_OK and word not in DOUBLE_EXCEPTIONS:
                errors.append(f"[фонология] {where} «{word}»: двойной согласный «{a}{a}» (разрешены tt/kk)")
                break
    whole = word.lower().replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    # запрещённые начальные кластеры: pt- (кроме ptah)
    if whole.startswith("pt") and not whole.startswith("ptah"):
        errors.append(f"[фонология] {where} «{word}»: начальный кластер pt (запрещён, кроме ptah)")
    for bad in ("stk", "ptl"):
        if bad in whole:
            errors.append(f"[фонология] {where} «{word}»: запрещённое сочетание {bad}")


# 1. Четыре разные формы у каждого корня + фонология
for root, (model, forms) in ROOTS.items():
    if len(forms) != 4:
        errors.append(f"[формы] корень {root}: ожидается 4 формы, получено {len(forms)}")
    # повторяющиеся нормативные формы внутри корня (кроме предельных fix)
    if model != "fix" and len(set(forms)) != 4:
        errors.append(f"[формы] корень {root}: повторяющиеся формы {forms}")
    for f in forms:
        check_phonology(f, f"форма {root}")
    if model == "fix" and len(set(forms)) != 1:
        errors.append(f"[формы] предельное слово {root} должно не изменяться")

# 2. Фонология чисел и исторических форм
for label, num in NUMBERS.items():
    check_phonology(num, f"число {label}")
for h in HISTORICAL:
    check_phonology(h, "историческая")

# 3. Коллизии форм
seen = {}
for root, (model, forms) in ROOTS.items():
    for f in forms:
        if f in seen and seen[f] != root:
            errors.append(f"[коллизия] форма «{f}» у корней {seen[f]} и {root}")
        seen[f] = root
# числа не должны совпадать с формами корней (кроме закреплённых: pant/pan — число 5)
number_forms = set(NUMBERS.values())
number_words = set()
for n in number_forms:
    for part in n.replace("(", "").replace(")", "").split("+"):
        for p in part.split("-"):
            number_words.add(p)
collide = set(seen) & number_words
allowed_collide = {"pan", "pant", "duut", "nult", "zult", "dunult", "nul"}
bad = collide - allowed_collide
for w in sorted(bad):
    errors.append(f"[коллизия] форма корня «{w}» совпадает с числовым словом")
for root, form in COLORS.items():
    check_phonology(form, f"цвет {root}")
    if form in seen:
        errors.append(f"[коллизия] цвет «{form}» ({root}) совпадает с формой корня {seen[form]}")
for q in QUANTIFIERS:
    check_phonology(q, f"квантификатор {q}")
    if q in seen:
        errors.append(f"[коллизия] квантификатор «{q}» совпадает с формой корня {seen[q]}")

# 4. Суффиксная модель: формы оканчиваются на -i/-u/-a/-e (кроме историч. kafee)
for root, (model, forms) in ROOTS.items():
    if model == "suff":
        for f in forms:
            if not f.endswith(("i", "u", "a", "e")):
                errors.append(f"[суфф. модель] {root}: «{f}» не оканчивается на гласную слоя")
    if model == "vowel":
        endings = [f[-1] for f in forms]
        if endings != ["i", "u", "a", "e"]:
            errors.append(f"[подмодель на гласную] {root}: окончания {endings} ≠ i,u,a,e")

# 5. Запреты
# zult не входит в составные числа
for label, num in NUMBERS.items():
    if label not in ("0",) and "zult" in num:
        errors.append(f"[запрет] zult в составном числе {label} = {num}")
# тройное повторение основы запрещено (композиты); числовое сокращение pa-pan допустимо
COMPOSITES_OK = ["kni-multu", "tish-duut", "rod-kni", "tish-duut-rod", "kni-vult",
                 "du-duut", "du-duut-pa-pan", "kni multu",
                 "vit pa-pan", "pa-pa-pan"]
for c in COMPOSITES_OK:
    parts = c.replace("+", "-").replace("(", "").replace(")", "").split("-")
    for p in parts:
        # тройное повторение одной основы подряд — запрещено
        if parts.count(p) >= 3:
            errors.append(f"[запрет] тройное повторение основы «{p}» в {c}")
# Стражи: запрещённые конструкции не должны встречаться среди нормативных форм
# kni-vult-multa снят 16.10.2026 (Д./Л.): смешение слоёв внутри словосложения
FORBIDDEN_COMPOSITES = ["kni-kni-kni", "kni-kni-multu", "zult-pa-pa-pan", "kni-vult-multa"]
all_normal_forms = set()
for root, (model, forms) in ROOTS.items():
    all_normal_forms.update(forms)
all_normal_forms.update(NUMBERS.values())
for c in FORBIDDEN_COMPOSITES:
    if c in all_normal_forms or c in COMPOSITES_OK:
        errors.append(f"[запрет] запрещённая конструкция «{c}» присутствует в норме")
for g in INTERJECTIONS:
    if g in ROOTS:
        errors.append(f"[норма] междометие «{g}» не входит в нормативный список корней")

if errors:
    print(f"FAIL: {len(errors)} ошибок")
    for e in errors[:40]:
        print("  -", e)
    raise SystemExit(1)
else:
    print(f"OK: {len(ROOTS)} корней, все формы фонологичны, коллизий нет, запреты соблюдены")
    raise SystemExit(0)
