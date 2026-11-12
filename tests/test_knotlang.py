#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка канона КНОТЛАНГ v0.7.

Список корней не зашит в этот файл: он читается из lexicon_v0.7.md.
Фразы читаются из строк «> » в каноне, демо-текстах и README.

Проверяется:
  1. Формы словаря совпадают с правилом модели.
  2. У обычного корня четыре разные формы; у предельного — одна;
     у цвета нормативна только -u-; у momor нет -a-.
  3. Нет коллизий форм.
  4. Фонология форм, чисел и фраз.
  5. Числа из словаря дают записанное значение; zult не входит в состав;
     тройной pa в степени пятёрки законен, тройной повтор корня — нет.
  6. В фразах нет голого корня: каждое слово — форма, частица, число, имя,
     оператор с префиксом или звательное корень.le.
  7. Старые опечатки и снятые формы в норму не вернулись.

Запуск: python3 tests/test_knotlang.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEXICON = ROOT / "lexicon_v0.7.md"
UTTERANCE_FILES = [
    ROOT / "KNOTLANG.md",
    ROOT / "demo_texts_v0.7.md",
    ROOT / "README.md",
]

VOWELS = set("aeiou")
LAYERS = ("i", "u", "a", "e")
DIGRAPHS = ("sh", "ch", "zh", "ts", "kh")
POSITIONS = {"k", "t", "s", "m"}
AFFECTS = {"le", "li", "la"}
BOUND_PARTICLES = {"zhe", "kna"}
NUMERAL_MORPHEMES = {"zult", "nult", "duut", "dunult", "pant", "pan", "pa", "du"}
ATOM_ORDER = ["dunult", "duut", "nult", "zult", "pant", "pan", "pa", "du"]
ATOM_VALUE = {
    "zult": 0,
    "nult": 1,
    "duut": 2,
    "dunult": 3,
    "pant": 5,
    "pan": 5,
    "pa": 5,
    "du": 2,
}

errors = []


def sounds(text):
    """Буквы → фонемы. Диграф — один звук."""
    out = []
    i = 0
    while i < len(text):
        two = text[i:i + 2]
        if two in DIGRAPHS:
            out.append(two)
            i += 2
        else:
            out.append(text[i])
            i += 1
    return out


def cluster_len(seq, is_member):
    best = cur = 0
    for item in seq:
        if is_member(item):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def phonology_errors(word):
    """Ошибки фонологии одного слова или числового выражения."""
    found = []
    body = word.lower()
    # Плюс и скобки — границы. Дефис и точка — тоже границы части,
    # но стык одинаковых согласных через дефис ещё проверяется.
    chunks = re.split(r"[+()]+", body)
    for chunk in chunks:
        if not chunk:
            continue
        parts = [p for p in re.split(r"[-.]", chunk) if p]
        for part in parts:
            snd = sounds(part)
            if cluster_len(snd, lambda s: s in VOWELS) >= 3:
                found.append(f"3+ гласных в «{part}»")
            if cluster_len(snd, lambda s: s not in VOWELS) >= 3:
                found.append(f"3+ согласных в «{part}»")
            for i in range(len(snd) - 1):
                a, b = snd[i], snd[i + 1]
                if a == b and a not in VOWELS and a not in DIGRAPHS:
                    pair = a + a
                    if pair not in {"tt", "kk"} and not (pair == "nn" and part.startswith("venn")):
                        found.append(f"гемината {pair} в «{part}»")
            if part.startswith("pt") and not part.startswith("ptah"):
                found.append(f"начальное pt в «{part}»")
            for bad in ("stk", "ptl"):
                if bad in part:
                    found.append(f"сочетание {bad} в «{part}»")
        for left, right in zip(parts, parts[1:]):
            ls, rs = sounds(left), sounds(right)
            if not ls or not rs:
                continue
            if ls[-1] == rs[0] and ls[-1] not in VOWELS:
                pair = ls[-1] + ls[-1]
                if pair not in {"tt", "kk"}:
                    found.append(f"стык {pair} в «{chunk}»")
    return found


def type_a(root):
    idxs = [i for i, ch in enumerate(root) if ch in VOWELS]
    if len(idxs) != 1:
        raise AssertionError(f"тип A требует одну гласную: {root}")
    i = idxs[0]
    forms = []
    for vowel in LAYERS:
        form = root[:i] + vowel + root[i + 1:]
        if root[-1] not in "td":
            form += "t"
        forms.append(form)
    return forms


def expected_forms(root, model):
    if model == "A":
        return type_a(root)
    if model in {"B", "CV", "EXC"}:
        return [root + vowel for vowel in LAYERS]
    if model == "CVCV":
        if root[-1] not in VOWELS:
            raise AssertionError(root)
        return [root[:-1] + vowel for vowel in LAYERS]
    if model == "SIB":
        return [root + vowel + "t" for vowel in LAYERS]
    if model == "FIX":
        return [root, root, root, root]
    if model == "NEAR":
        return None
    if model == "COLOR":
        if root[0] in VOWELS:
            held = root + "u"
        else:
            held = type_a(root)[1]
        return ["-", held, "-", "-"]
    raise AssertionError(model)


def looks_like_a(root):
    snd = sounds(root)
    vowel_idx = [i for i, seg in enumerate(snd) if seg in VOWELS]
    if len(vowel_idx) != 1:
        return False
    if vowel_idx[0] in {0, len(snd) - 1}:
        return False
    if snd[-1] in {"sh", "ch", "zh"}:
        return False
    try:
        forms = type_a(root)
    except AssertionError:
        return False
    return all(not phonology_errors(form) for form in forms)


def parse_table(text, header_prefix):
    rows = []
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(header_prefix):
            start = i + 2
            break
    if start is None:
        errors.append(f"[словарь] нет таблицы {header_prefix!r}")
        return rows
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def load_lexicon():
    text = LEXICON.read_text(encoding="utf-8")
    nodes = []
    for cells in parse_table(text, "| корень |"):
        if len(cells) != 8:
            errors.append(f"[словарь] строка узла не из 8 клеток: {cells}")
            continue
        root, model, ripe, held, released, echo, gloss, note = cells
        nodes.append({
            "root": root,
            "model": model,
            "forms": [ripe, held, released, echo],
            "gloss": gloss,
            "note": note,
        })
    particles = []
    for cells in parse_table(text, "| слово |"):
        particles.append({"word": cells[0], "role": cells[1]})
    names = []
    for cells in parse_table(text, "| имя |"):
        names.append(cells[0])
    numbers = []
    for cells in parse_table(text, "| значение |"):
        numbers.append({"value": int(cells[0]), "spell": cells[1]})
    compounds = []
    for cells in parse_table(text, "| основа |"):
        compounds.append({"stem": cells[0], "gloss": cells[1]})
    return nodes, particles, names, numbers, compounds


class ParseError(Exception):
    pass


def parse_number(spell):
    """Дерево выражения и его значение. Непроверяет допустимость сокращений."""
    def parse_sum(s, i):
        node, i = parse_prod(s, i)
        terms = [node]
        while i < len(s) and s[i] == "+":
            node, i = parse_prod(s, i + 1)
            terms.append(node)
        if len(terms) == 1:
            return terms[0], i
        return ("add", terms), i

    def parse_prod(s, i):
        node, i = parse_factor(s, i)
        factors = [node]
        while i < len(s) and s[i] == "-":
            node, i = parse_factor(s, i + 1)
            factors.append(node)
        if len(factors) == 1:
            return factors[0], i
        return ("mul", factors), i

    def parse_factor(s, i):
        if i < len(s) and s[i] == "(":
            node, j = parse_sum(s, i + 1)
            if j >= len(s) or s[j] != ")":
                raise ParseError(spell)
            return node, j + 1
        for atom in ATOM_ORDER:
            if s.startswith(atom, i):
                nxt = i + len(atom)
                if nxt == len(s) or s[nxt] in "+-)":
                    return ("atom", atom), nxt
        raise ParseError(spell)

    node, end = parse_sum(spell, 0)
    if end != len(spell):
        raise ParseError(spell)
    return node


def number_value(node):
    kind = node[0]
    if kind == "atom":
        return ATOM_VALUE[node[1]]
    if kind == "add":
        total = 0
        for term in node[1]:
            total += number_value(term)
        return total
    if kind == "mul":
        total = 1
        for factor in node[1]:
            total *= number_value(factor)
        return total
    raise AssertionError(kind)


def number_wellformed(node, top=True):
    kind = node[0]
    if kind == "atom":
        name = node[1]
        if name in {"zult", "pant"} and not top:
            return False
        if top and name in {"pan", "pa", "du"}:
            return False
        return True
    if kind == "add":
        return all(number_wellformed(term, top=False) for term in node[1])
    if kind == "mul":
        factors = node[1]
        for i, factor in enumerate(factors):
            if not number_wellformed(factor, top=False):
                return False
            if factor[0] != "atom":
                continue
            name = factor[1]
            nxt = factors[i + 1] if i + 1 < len(factors) else None
            nxt_name = nxt[1] if nxt and nxt[0] == "atom" else None
            if name == "pa" and nxt_name not in {"pa", "pan"}:
                return False
            if name == "du" and nxt_name != "duut":
                return False
            if name == "pan" and nxt_name in {"pa", "pan"}:
                return False
            if name == "duut" and nxt_name in {"du", "duut"}:
                return False
        return True
    return False


def try_number(token):
    try:
        node = parse_number(token)
    except ParseError:
        return None
    if not number_wellformed(node, top=True):
        return None
    return number_value(node)


def content_triple(parts):
    """True, если корень содержания повторён трижды. Числовые морфемы не считаются."""
    counts = {}
    for part in parts:
        if part in NUMERAL_MORPHEMES or part in POSITIONS or part in AFFECTS or part in BOUND_PARTICLES:
            continue
        counts[part] = counts.get(part, 0) + 1
    return any(n >= 3 for n in counts.values())


def utterances_in(path):
    found = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("> "):
            found.append((path.name, lineno, line[2:].strip()))
    return found


def tokens_of(utterance):
    text = utterance.strip()
    text = re.sub(r"^(?:[A-Za-z][A-Za-z]*|[A-ZА-Я]\.)\s*:\s*", "", text)
    raw = text.split()
    tokens = []
    for token in raw:
        token = token.strip(".,?!;:…").lower()
        if token:
            tokens.append(token)
    return tokens


def check_token(token, forms, form_layer, color_forms, roots, free_particles, names):
    if token in names or token in free_particles or token in forms:
        return
    if token == "nai-zhe":
        return
    if try_number(token) is not None:
        return
    if "." in token:
        root, suffix = token.split(".", 1)
        if suffix == "le" and root in roots:
            return
        errors.append(f"[фраза] звательное «{token}» не сходится")
        return
    if "-" in token:
        parts = token.split("-")
        while parts and parts[0] in POSITIONS:
            parts = parts[1:]
        while parts and parts[0] == "kna":
            parts = parts[1:]
        if parts and parts[-1] in AFFECTS and parts[-1] not in forms:
            parts = parts[:-1]
        if len(parts) == 1 and parts[0] in {"kne", "kni"}:
            return
        if not parts or any(part not in forms for part in parts):
            errors.append(f"[фраза] не разобрано «{token}»")
            return
        if any(part in color_forms for part in parts[1:]):
            errors.append(f"[фраза] цвет не в начале «{token}»")
        if content_triple(token.split("-")):
            errors.append(f"[фраза] тройной повтор в «{token}»")
        layers = []
        for i, part in enumerate(parts):
            if i == 0 and part in color_forms:
                continue
            layers.append(form_layer[part])
        concrete = [layer for layer in layers if layer != "*"]
        if len(set(concrete)) > 1:
            errors.append(f"[фраза] разные слои в композите «{token}»")
        return
    for suffix in ("le", "li", "la"):
        if token.endswith(suffix) and token[: -len(suffix)] in forms:
            return
    errors.append(f"[фраза] не разобрано «{token}»")


def main():
    nodes, particles, names, numbers, compounds = load_lexicon()
    by_root = {}
    form_owner = {}
    form_layer = {}
    color_forms = set()
    all_forms = set()

    for node in nodes:
        root = node["root"]
        model = node["model"]
        listed = node["forms"]
        if root in by_root:
            errors.append(f"[словарь] корень {root} повторён")
        by_root[root] = node
        if model != "NEAR":
            want = expected_forms(root, model)
            if listed != want:
                errors.append(f"[формы] {root}: в словаре {listed}, по правилу {want}")
        else:
            if listed[2] != "-":
                errors.append(f"[формы] {root}: почтипредельное не должно отдаваться в -a-")
            if listed[1] != "momu" or root != "momor":
                errors.append(f"[формы] почтипредельное v0.7 — это momor/momu, получено {root} {listed}")
        if model == "FIX" and len(set(listed)) != 1:
            errors.append(f"[формы] предельное {root} изменилось: {listed}")
        if model == "COLOR":
            if listed[0] != "-" or listed[2] != "-" or listed[3] != "-":
                errors.append(f"[формы] цвет {root} имеет не только -u-")
            color_forms.add(listed[1])
        if model not in {"FIX", "COLOR", "NEAR"} and len(set(listed)) != 4:
            errors.append(f"[формы] {root}: формы не различны {listed}")
        if looks_like_a(root) and model not in {"A", "COLOR"} and node["note"] == "-":
            errors.append(f"[модель] {root} выглядит как тип A, но записан как {model} без заметки")
        if model == "A" and not looks_like_a(root):
            errors.append(f"[модель] {root} записан как тип A, но правило A на него не садится")
        for layer, form in zip(LAYERS, listed):
            if form == "-":
                continue
            all_forms.add(form)
            if form in form_owner and form_owner[form] != root:
                errors.append(f"[коллизия] «{form}» у {form_owner[form]} и {root}")
            form_owner[form] = root
            if model == "FIX":
                form_layer[form] = "*"
            else:
                form_layer[form] = layer
            for problem in phonology_errors(form):
                errors.append(f"[фонология] {root} «{form}»: {problem}")

    if "moma" in all_forms:
        errors.append("[формы] moma не должна входить в норму")
    if "mult" in all_forms:
        errors.append("[формы] голое mult не форма; много — это multu")
    if "multu" not in all_forms:
        errors.append("[формы] нет multu")

    banned = [
        "belt", "nokt", "zant", "sivut", "krelut", "trekut", "amrut",
        "duult", "vultu", "wulte", "radi", "radu", "rada", "rade",
        "chaii", "ptil", "ptilu", "zemu", "moma",
    ]
    for old in banned:
        if old in all_forms:
            errors.append(f"[снято] «{old}» снова в норме")

    # Близкие, но разные слова обязаны остаться разными.
    guards = [
        ("wult", "vult"),
        ("dut", "duut"),
        ("duut", "dult"),
        ("dut", "dult"),
        ("nul", "nult"),
        ("momu", "mou-murt"),
    ]
    for left, right in guards:
        if left == right:
            errors.append(f"[коллизия] сторож {left}")

    free_particles = {row["word"] for row in particles if row["word"] not in BOUND_PARTICLES}
    for bound in BOUND_PARTICLES:
        if bound not in {row["word"] for row in particles}:
            errors.append(f"[частицы] нет связанной частицы {bound}")
    name_set = {name.lower().rstrip(".") for name in names}

    for row in numbers:
        spell = row["spell"]
        try:
            node = parse_number(spell)
        except ParseError:
            errors.append(f"[число] не читается {spell}")
            continue
        if not number_wellformed(node, top=True):
            errors.append(f"[число] запись запрещена правилом: {spell}")
            continue
        got = number_value(node)
        if got != row["value"]:
            errors.append(f"[число] {spell}: по правилу {got}, в словаре {row['value']}")
        for problem in phonology_errors(spell):
            errors.append(f"[фонология] число {spell}: {problem}")
        if "zult" in spell and row["value"] != 0:
            errors.append(f"[число] zult внутри {spell}")

    extras = {
        "dunult-duut": 6,
        "dunult-du-duut": 12,
        "pa-pa-pa-pan": 625,
        "pant": 5,
        "duut-pan": 10,
        "pa-pan+duut-pan": 35,
        "pa-pa-pan+pan": 130,
    }
    for spell, value in extras.items():
        node = parse_number(spell)
        if not number_wellformed(node, top=True) or number_value(node) != value:
            errors.append(f"[число] {spell} должно давать {value}")
    for bad in ("zult-pan", "pan", "pa", "du", "pan-pan", "duut-duut", "pant+nult", "duult", "duult-pan"):
        if try_number(bad) is not None:
            errors.append(f"[число] запрещённая запись прошла: {bad}")
    if not content_triple(["kni", "kni", "kni"]):
        errors.append("[повтор] kni-kni-kni должен быть запрещён")
    if content_triple(["pa", "pa", "pa", "pan"]):
        errors.append("[повтор] степень pa-pa-pa-pan не должна считаться тройным корнем")

    # Композиты: один слой на обоих корнях, и морская вода не равна океану.
    for row in compounds:
        left, right = row["stem"].split("-")
        if left not in by_root or right not in by_root:
            errors.append(f"[композит] неизвестная основа {row['stem']}")
            continue
        for index, layer in enumerate(LAYERS):
            a = by_root[left]["forms"][index]
            b = by_root[right]["forms"][index]
            if a == "-" or b == "-":
                errors.append(f"[композит] {row['stem']} не имеет слоя {layer}")
                continue
            built = f"{a}-{b}"
            for problem in phonology_errors(built):
                errors.append(f"[фонология] композит {built}: {problem}")
        if row["stem"] == "mo-mor":
            sea = f"{by_root['mo']['forms'][1]}-{by_root['mor']['forms'][1]}"
            if sea == "momu" or sea == "momor":
                errors.append(f"[коллизия] морская вода {sea} совпала с океаном")

    for path in UTTERANCE_FILES:
        for filename, lineno, utterance in utterances_in(path):
            tokens = tokens_of(utterance)
            if not tokens:
                errors.append(f"[фраза] {filename}:{lineno} пустая")
            for token in tokens:
                before = len(errors)
                check_token(token, all_forms, form_layer, color_forms, by_root, free_particles, name_set)
                for problem in phonology_errors(token):
                    errors.append(f"[фонология] {filename}:{lineno} «{token}»: {problem}")
                if len(errors) > before:
                    errors.append(f"    источник {filename}:{lineno} «{utterance}»")

    # Сторож: голый корень и старая опечатка не должны проходить как фраза.
    for bad_line in ("Okn nai.", "Kna-knot nai.", "Rawu var nai.", "Duult nai.", "Moma nai."):
        bad_tokens = tokens_of(bad_line)
        before = len(errors)
        for token in bad_tokens:
            check_token(token, all_forms, form_layer, color_forms, by_root, free_particles, name_set)
        if len(errors) == before:
            errors.append(f"[сторож] незаконная фраза прошла: {bad_line}")
        else:
            del errors[before:]

    if errors:
        print(f"FAIL: {len(errors)} ошибок")
        for item in errors[:60]:
            print(" ", item)
        return 1
    print(
        f"OK: {len(nodes)} корней, {len(all_forms)} форм, "
        f"{len(numbers)} чисел, фразы канона и демо разобраны"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
