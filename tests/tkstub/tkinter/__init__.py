"""Minimal tkinter stand-in for headless tests (CI has no display): widgets accept any call, variables,
Text and Notebook keep real state, root.after() callbacks are collected in AFTERS."""
AFTERS = []
CREATED = []


class _Any:
    def __call__(self, *a, **k):
        return _Any()

    def __getattr__(self, name):
        return _Any()

    def __iter__(self):
        return iter(())

    def __int__(self):
        return 0

    def __str__(self):
        return ''


class Misc:
    def __init__(self, master=None, *a, **k):
        self.master = master
        self._kids = []
        self._cfg = dict(k)
        self._state = set()
        if master is not None and hasattr(master, '_kids'):
            master._kids.append(self)
        CREATED.append(self)

    def __getattr__(self, name):
        return _Any()

    # configuration
    def configure(self, *a, **k):
        self._cfg.update(k)
    config = configure

    def cget(self, k):
        return self._cfg.get(k, '')

    def __setitem__(self, k, v):
        self._cfg[k] = v

    def __getitem__(self, k):
        return self._cfg.get(k, '')

    def state(self, s=None):
        if s:
            for x in s:
                (self._state.discard(x[1:]) if x.startswith('!') else self._state.add(x))
        return tuple(self._state)

    def winfo_children(self):
        return [k for k in self._kids if not getattr(k, '_dead', False)]

    def destroy(self):
        self._dead = True
        for k in list(self._kids):
            k.destroy()

    def after(self, ms, fn=None, *a):
        if fn:
            AFTERS.append((fn, a))
        return 'after#%d' % len(AFTERS)

    def winfo_class(self):
        return type(self).__name__

    def winfo_screenheight(self):
        return 900


class Tk(Misc):
    def __init__(self, *a, **k):
        super().__init__(None)

    def mainloop(self):
        pass


Toplevel = Frame = Label = Button = Entry = Scrollbar = Listbox = Misc


class Canvas(Misc):
    _n = 0

    def _new(self, *a, **k):
        Canvas._n += 1
        return Canvas._n
    create_line = create_rectangle = create_oval = create_polygon = create_text = create_image = create_window = _new


class Menu(Misc):
    pass


class Text(Misc):
    def __init__(self, master=None, *a, **k):
        super().__init__(master, *a, **k)
        self.buf = ''

    def insert(self, idx, text, *tags):
        self.buf += text

    def delete(self, a, b=None):
        self.buf = ''

    def get(self, a='1.0', b='end'):
        return self.buf


class PhotoImage(Misc):
    def __init__(self, *a, **k):
        if 'file' in k:
            raise RuntimeError('no image in tests')
        super().__init__(None)


class Variable:
    def __init__(self, master=None, value=None, name=None):
        self._v = value
        self._cb = []

    def get(self):
        return self._v

    def set(self, v):
        self._v = v
        for cb in self._cb:
            cb('', '', 'write')

    def trace_add(self, mode, cb):
        self._cb.append(cb)


class StringVar(Variable):
    def __init__(self, master=None, value='', name=None):
        super().__init__(master, '' if value is None else value)


class BooleanVar(Variable):
    def get(self):
        return bool(self._v)


class DoubleVar(Variable):
    def get(self):
        return float(self._v or 0)


IntVar = DoubleVar
