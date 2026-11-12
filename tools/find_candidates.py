import sys; sys.path.insert(0, '.')
from knot import *
from base_lex import *
def surfaces(extra=()):
    S = {}
    for r,m,*_ in list(BASE)+list(extra):
        for f in set(forms(r,m)): S.setdefault(f,set()).add(r)
    for w in PARTICLES+GESTURES+NUMWORDS: S.setdefault(w,set()).add(w)
    return S
S = surfaces()
AFF=("le","li","la")
def check(root, model):
    fs = forms(root, model)
    rep = {"forms":fs,"exact":[],"near":[],"phon":[],"aff":[]}
    for f in fs:
        if f in S: rep["exact"].append((f,S[f]))
        rep["phon"] += phon_errors(f)
        for w in S:
            if lev1(f,w) and len(w)>=3: rep["near"].append(f"{f}~{w}({','.join(S[w])})")
        for a in AFF:
            # форма = чужая форма + аффектив?
            if f.endswith(a) and f[:-2] in S: rep["aff"].append(f"{f}={f[:-2]}+{a}")
        for a in AFF:
            if f+a in S: rep["aff"].append(f"{f}+{a}={f+a}")
    return rep
if __name__=="__main__":
    for r,m in [(x.split(':')[0],x.split(':')[1]) for x in sys.argv[1:]]:
        rep=check(r,m); print(r,m,rep["forms"],"EXACT",rep["exact"],"PHON",rep["phon"],"AFF",rep["aff"]); print("   near:",rep["near"])
