#!/usr/bin/env python3
"""يبني diffs-shubah.json من جدول الفروق الذي زوّدنا به المستخدم.

قاعدة صارمة: المصدر وحده يقرّر ما هو الفرق ونصَّ الروايتين.
الشيفرة لا تستنبط فرقاً من مقارنة النصوص، وإنما:
  1) تقرأ عمود «البيان» لتستخرج الكلمة والموضع (سورة/آية).
  2) تتحقّق أن الكلمة موجودة فعلاً في تلك الآية من مصحفنا (رسماً مجرّداً من النقط).
  3) إن لم توجد، تبحث في السورة نفسها؛ فإن وُجدت في آية واحدة لا غير
     صحّحت الرقم وسجّلت الرقم الأصلي في الحقل cited.
  4) ما بقي بلا موضع (قواعد عامّة: «حيث أتى»/«فواتح السور») يُعرَض قاعدةً بلا مواضع.
"""
import json, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'diffs-rows.json')
DATA = os.path.join(HERE, '..', 'quran-shubah.json')
OUT  = os.path.join(HERE, '..', 'diffs-shubah.json')

d   = json.load(open(DATA))
SUR = {int(k): v for k, v in d['suras'].items()}
AY, BY_SURA = {}, {}
for su, ay, pg, l1, l2, txt in d['v']:
    AY[(su, ay)] = (pg, txt)
    BY_SURA.setdefault(su, []).append((ay, pg, txt))

MARKS = re.compile('[ً-ٰٟۖ-ۭـٓ-ٕ]')
def light(s):
    """تجريد من الحركات مع بقاء النقط."""
    s = MARKS.sub('', s)
    for a, b in (('ٱ','ا'),('أ','ا'),('إ','ا'),('آ','ا'),('ء',''),
                 ('ؤ','و'),('ئ','ي'),('ة','ه'),('ى','ي')):
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', re.sub(r'[^ء-ي ]', '', s)).strip()

def rasm(s):
    """رسم مجرّد: بلا حركات وبلا نقط، لأن كثيراً من الفروق في النقط ذاته."""
    return re.sub('[تثنبي]', 'ٮ', light(s))

NAME2NUM = {light(v): n for n, v in SUR.items()}
NUMTOK   = re.compile(r'^[\d٠-٩][\d٠-٩:\-–,،/]*$')
FILLER   = {'الايات', 'الايه', 'ايه', 'ايات', 'من', 'و', 'رقم'}
PUNCT    = re.compile(r'^[،,\-–—:؛.]+$')
GEN_TAIL = ('حيث أتى', 'فواتح السور')
# فصل الكلمة القرآنية عن شرح القارئ: الشرح يبدأ بفعلٍ من هذه الطائفة،
# والكلمة القرآنية تحمل علامات المصحف (ٱ ۡ ٰ ٖ ٗ ٞ …) فلا تُحسب شرحاً أبداً.
UTH      = re.compile('[ٱۡٓٔ-ٕٖ-ٟۖ-ۭ]')
HARAK    = re.compile('[ً-ْٰـ]')
STARTERS = ('قرأ','فتح','ضم','كسر','اسكن','أسكن','اظهر','أظهر','ادغم','أدغم','خفف',
  'شدد','ابدل','أبدل','امال','أمال','ترك','قصر','حذف','اثبت','أثبت','وقف','رفع','نصب',
  'جر','جرّ','سكن','نوّن','زاد','الحق','ألحق','حرك','بضم','بفتح','بكسر','بتاء','بياء',
  'بنون','بالياء','بالتاء','بالنون','بالافراد','بالإفراد','بالجمع','بواو','بهمز',
  'بالخفض','بالرفع','بالنصب','بالجر','خفض','جزم','منع','اشبع','أشبع','سهل','لم','مد',
  'ادغمها','أدغمها','ابدلها','أبدلها','قرأها','امالها','أمالها','اظهرها','أظهرها',
  'بلا','نون','ياء')

def split_cmt(s):
    toks = s.split()
    for i, t in enumerate(toks):
        if i == 0 or UTH.search(t):
            continue
        c = HARAK.sub('', t)
        if any(c.startswith(k) for k in STARTERS):
            return ' '.join(toks[:i]).strip(' ،'), ' '.join(toks[i:])
    return s.strip(), ''

def ar2i(t):
    return int(''.join(chr(ord(c) - 0x660 + 0x30) if '٠' <= c <= '٩' else c for c in t))

def tokenize(a):
    a = a.replace('،', ' ، ')
    a = re.sub(r'(?<=[ء-ي])(?=[\d٠-٩])', ' ', a)      # «سبأ9» ← «سبأ 9»
    return a.split()

def try_split(toks, ntoks, i):
    """هل ينحلّ ما بعد الموضع i إلى قائمة مواضع صحيحة؟"""
    refs, j, last, n = [], i, None, len(toks)
    while j < n:
        if PUNCT.match(toks[j]) or ntoks[j] in FILLER:
            j += 1; continue
        hit = None
        for L in (3, 2, 1):
            if j + L <= n and ' '.join(ntoks[j:j + L]) in NAME2NUM:
                hit = (NAME2NUM[' '.join(ntoks[j:j + L])], L); break
        if hit:
            last = hit[0]; j += hit[1]; continue
        raw = toks[j].strip('،')
        if last is not None and NUMTOK.match(raw):
            for p in [x for x in re.split(r'[,،/]', raw) if x]:
                seg = [x for x in re.split(r'[:\-–]', p) if x]
                if len(seg) == 2:
                    a1, a2 = ar2i(seg[0]), ar2i(seg[1])
                    refs += ([(last, a1), (last, a2)] if a2 - a1 <= 1
                             else [(last, k) for k in range(a1, a2 + 1)])
                else:
                    refs += [(last, ar2i(x)) for x in seg]
            j += 1; continue
        return None
    if last is None:
        return None
    return refs, last

def parse_head(a):
    toks, n = tokenize(a), len(tokenize(a))
    ntoks = [light(t) for t in toks]
    best = None
    for i in range(n):
        r = try_split(toks, ntoks, i)
        if r is None:
            continue
        refs, last = r
        key = (len(refs), i)
        if best is None or key > best[0]:
            best = (key, i, refs, last)
    if best is None:
        return None
    _, i, refs, last = best
    return ' '.join(toks[:i]).strip(' ،'), refs, last

def head_of(s):
    return split_cmt(s)[0]

def find_in_sura(su, words):
    """الآيات التي يظهر فيها الرسم؛ words قائمة صيغ."""
    hits = []
    for ay, pg, txt in BY_SURA.get(su, []):
        r = rasm(txt)
        if any(w and w in r for w in words):
            hits.append(ay)
    return hits

def main():
    rows = json.load(open(SRC))
    out, notes = [], []
    for x in rows[1:]:
        a = (x.get('A') or '').strip()
        b = (x.get('B') or '').strip()
        c = (x.get('C') or '').strip()
        if not (a and b and c):
            notes.append(('سطر ناقص', x.get('r'), a)); continue

        hw, hc = split_cmt(b)
        sw, sc = split_cmt(c)
        e = {'r': x['r'], 'hafs': b, 'shubah': c,
             'hw': hw, 'hc': hc, 'sw': sw, 'sc': sc,
             'refs': [], 'scope': ''}

        # ــ قواعد عامّة
        if a.endswith(GEN_TAIL) or a in ('كٓهيعٓصٓ', 'طه'):
            head = a
            for t in GEN_TAIL:
                if head.endswith(t):
                    head = head[:-len(t)].strip()
            e['word']  = head or a
            e['scope'] = 'فواتح السور' if a.endswith(GEN_TAIL[1]) else 'حيث أتى'
            out.append(e); continue

        p = parse_head(a)
        if p is None:
            notes.append(('تعذّر التحليل', x['r'], a)); continue
        word, refs, last = p
        e['word'] = word or head_of(b) or a

        # صيغ البحث: كلمة حفص وكلمة شعبة
        forms = {rasm(w) for w in (e['word'], head_of(b), head_of(c)) if w}
        forms = {w for w in forms if len(w) >= 3}

        if refs:
            for su, ay in refs:
                if (su, ay) in AY:
                    r = {'s': su, 'a': ay, 'p': AY[(su, ay)][0]}
                    if forms and not any(f in rasm(AY[(su, ay)][1]) for f in forms):
                        near = [n for n in find_in_sura(su, forms) if abs(n - ay) <= 8]
                        if len(near) == 1:
                            r = {'s': su, 'a': near[0], 'p': AY[(su, near[0])][0],
                                 'cited': ay}
                            notes.append(('تصحيح رقم آية', x['r'],
                                          f'{SUR[su]} {ay} ← {near[0]}'))
                    e['refs'].append(r)
                else:
                    hits = find_in_sura(su, forms)
                    if len(hits) == 1:
                        e['refs'].append({'s': su, 'a': hits[0],
                                          'p': AY[(su, hits[0])][0], 'cited': ay})
                        notes.append(('رقم خارج السورة', x['r'],
                                      f'{SUR[su]} {ay} ← {hits[0]}'))
                    else:
                        notes.append(('موضع غير موجود', x['r'], f'{SUR[su]} {ay}'))
        else:
            # لم يُذكر رقم الآية، إنما السورة وحدها
            hits = find_in_sura(last, {rasm(head_of(c))} - {''})
            if len(hits) == 1:
                e['refs'].append({'s': last, 'a': hits[0],
                                  'p': AY[(last, hits[0])][0], 'found': 1})
            else:
                e['scope'] = 'سورة ' + SUR[last]
                e['sura']  = last
                notes.append(('سورة بلا رقم', x['r'],
                              f'{SUR[last]} → {len(hits)} احتمال'))
        out.append(e)

    out.sort(key=lambda e: (e['refs'][0]['s'], e['refs'][0]['a']) if e['refs']
                            else (0, e['r']))
    json.dump({'v': 1,
               'src': 'جدول الفروق بين روايتي شعبة وحفص (nquran.com) — بتزويد المستخدم',
               'items': out},
              open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))

    nref = sum(len(e['refs']) for e in out)
    print(f'المدخلات: {len(out)}   المواضع: {nref}   '
          f'القواعد العامّة: {sum(1 for e in out if not e["refs"])}')
    for n in notes:
        print('   •', *n)

main()
