SHOWN = []


def _show(*a, **k):
    SHOWN.append(a)
    return True


showwarning = showinfo = showerror = askokcancel = askyesno = _show
