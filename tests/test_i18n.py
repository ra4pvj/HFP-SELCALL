"""Every T('…') string in the program has an English translation with the same % format specifiers."""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from i18n_en import EN      # noqa: E402

SPEC = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?[sdfxXcr%]')
FILES = ['hfp_selcall_app.py', 'hfp_selcall_gui.py', 'selcall_engine.py']
EXTRA = ['Двухтональный', 'Трель', 'Короткие гудки', 'Мелодия «Калинка»', 'Выключено', 'системный выход',
         'Подтверждение', 'Сообщение', 'Вызов', 'HFPager: кадр «маяк»', 'HFPager: сообщение', 'HFPager: вызов (CALL)',
         'Selcall: вызов', 'Selcall: сообщение', 'CW (телеграф)']


def strings():
    for fn in FILES:
        tree = ast.parse(open(os.path.join(ROOT, fn), encoding='utf-8').read())
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'T' and n.args
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)):
                yield fn, n.lineno, n.args[0].value
    for s in EXTRA:
        yield 'extra', 0, s


def main():
    missing, bad = [], []
    for fn, ln, s in strings():
        if s not in EN:
            missing.append('%s:%d %r' % (fn, ln, s))
        elif SPEC.findall(s) != SPEC.findall(EN[s]):
            bad.append('%s:%d %r -> %r' % (fn, ln, s, EN[s]))
    for m in missing + bad:
        print('  ', m)
    assert not missing, '%d strings without English translation' % len(missing)
    assert not bad, '%d translations with different %% specifiers' % len(bad)
    print('OK  i18n: %d strings, all translated, format specifiers match' % len(EN))


if __name__ == '__main__':
    main()
