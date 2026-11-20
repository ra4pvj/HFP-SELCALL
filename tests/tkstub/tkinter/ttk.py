from tkinter import Misc


class Style:
    def __init__(self, *a):
        self._t = 'default'

    def theme_use(self, t=None):
        if t:
            self._t = t
        return self._t

    def configure(self, *a, **k):
        pass

    def map(self, *a, **k):
        pass


class Notebook(Misc):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.tabs_ = []
        self.cur = 0

    def add(self, w, **k):
        self.tabs_.append(w)

    def select(self, x=None):
        if x is None:
            return self.cur
        self.cur = x if isinstance(x, int) else self.tabs_.index(x)

    def index(self, x):
        return self.cur


Frame = LabelFrame = Label = Entry = Button = Combobox = Checkbutton = Scale = Progressbar = Scrollbar = \
    Treeview = Spinbox = Radiobutton = Separator = Misc
