"""
HFP+SELCALL window (tkinter).  The main page is the chat only; everything else lives on tabs:

    Chat | New message / call | HFPager | HF Selcall | Transceiver & audio | Program

Above the tabs (always visible): RX/TX lamps, input level meter (peak dBFS, green / yellow / red),
spectrum, two seven-segment clocks (UTC and a chosen time zone).  Language (RU/EN) and theme
(light/dark) are switched from the menu or the Program tab: the window is rebuilt, the radio keeps
working (the Core with the audio streams is not touched).
"""
import copy
import datetime
import os
import queue
import sys
import threading
import time

import numpy as np

import hfp_selcall_app as A
import hfpager_ptt as P
import hfpager_rig as G
import hfpager_rx as R
import i18n
import selcall_engine as SE
from i18n import T

PORT_OFF = 'Выключено'          # port combobox value meaning "no COM port" (stored as '')
SYS_OUT = 'системный выход'

# second clock: (key, label, offset hours); 'LOCAL' = the computer's time zone
TIME_ZONES = [('LOCAL', None, None)] + [
    ('UTC%+d' % h if h else 'UTC+0', None, h) for h in range(-12, 15)] + [
    ('KALT', 'KALT +2', 2), ('MSK', 'MSK +3', 3), ('SAMT', 'SAMT +4', 4), ('YEKT', 'YEKT +5', 5),
    ('OMST', 'OMST +6', 6), ('KRAT', 'KRAT +7', 7), ('IRKT', 'IRKT +8', 8), ('YAKT', 'YAKT +9', 9),
    ('VLAT', 'VLAT +10', 10), ('MAGT', 'MAGT +11', 11), ('PETT', 'PETT +12', 12)]

LAMP = {'rx_on': '#33ff33', 'rx_off': '#0b3a0b', 'rx_dec': '#ffcc00', 'tx_on': '#ff2a2a', 'tx_off': '#4a0b0b'}
DARK = dict(bg='#1e1f22', fg='#e3e3e3', field='#2b2d31', sel='#3d5a80', dim='#9aa0a6', border='#3a3c42',
            button='#33363c', active='#41454c', tab='#2b2d31', tab_sel='#1e1f22')
METER_W, METER_H = 200, 16
WF_BINS = 270                    # spectrum rows from the receiver: 300..3000 Hz in 10 Hz bins
OVER_DB = 20 * np.log10(A.CLIP_LEVEL)      # -0.18 dBFS


def tz_label(key):
    for k, lbl, h in TIME_ZONES:
        if k == key:
            if k == 'LOCAL':
                return T('Местное (компьютер)')
            return lbl or k
    return key


def tz_time(key):
    """(label for the clock, datetime)"""
    now = datetime.datetime.utcnow()
    for k, lbl, h in TIME_ZONES:
        if k == key:
            if k == 'LOCAL':
                loc = datetime.datetime.now()
                off = round((loc - now).total_seconds() / 900) * 0.25
                return ('LOC %+g' % off), loc
            return (lbl or k), now + datetime.timedelta(hours=h)
    return 'UTC', now


# ============================================================================ seven-segment clock
_SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc',
        '7': 'abc', '8': 'abcdefg', '9': 'abcdfg', '-': 'g', ' ': ''}


class SegClock:
    """HH:MM:SS drawn as green seven-segment digits on a black canvas"""

    def __init__(self, tk, parent, title, digit_h=26, on='#39ff39', off='#0d260d', bg='#000000'):
        self.on, self.off = on, off
        self.dh = digit_h
        self.dw = int(digit_h * 0.55)
        self.t = max(3, digit_h // 8)
        w = 8 * (self.dw + 6) - 2 * (self.dw - 6) + 8
        self.c = tk.Canvas(parent, width=w, height=digit_h + 22, background=bg, highlightthickness=1,
                           highlightbackground='#333333')
        self.title = self.c.create_text(6, 8, anchor='w', fill='#1fae1f', font=('Helvetica', 9, 'bold'),
                                        text=title)
        self.items = []
        x = 6
        for i in range(8):
            if i in (2, 5):
                self.items.append(self._colon(x))
                x += 12
            else:
                self.items.append(self._digit(x))
                x += self.dw + 6
        self.c.configure(width=x + 2)

    def _poly(self, pts):
        return self.c.create_polygon(pts, fill=self.off, outline='')

    def _digit(self, x0):
        y0 = 18
        w, h, t = self.dw, self.dh, self.t
        m = y0 + h / 2
        seg = {}
        seg['a'] = self._poly([x0 + t, y0, x0 + w - t, y0, x0 + w - 2 * t, y0 + t, x0 + 2 * t, y0 + t])
        seg['d'] = self._poly([x0 + 2 * t, y0 + h - t, x0 + w - 2 * t, y0 + h - t, x0 + w - t, y0 + h, x0 + t, y0 + h])
        seg['g'] = self._poly([x0 + t, m, x0 + 2 * t, m - t / 2, x0 + w - 2 * t, m - t / 2, x0 + w - t, m,
                               x0 + w - 2 * t, m + t / 2, x0 + 2 * t, m + t / 2])
        seg['f'] = self._poly([x0, y0 + t, x0 + t, y0 + 2 * t, x0 + t, m - t, x0, m - t / 2])
        seg['e'] = self._poly([x0, m + t / 2, x0 + t, m + t, x0 + t, y0 + h - 2 * t, x0, y0 + h - t])
        seg['b'] = self._poly([x0 + w, y0 + t, x0 + w - t, y0 + 2 * t, x0 + w - t, m - t, x0 + w, m - t / 2])
        seg['c'] = self._poly([x0 + w, m + t / 2, x0 + w - t, m + t, x0 + w - t, y0 + h - 2 * t, x0 + w, y0 + h - t])
        return seg

    def _colon(self, x0):
        y0, h, r = 18, self.dh, max(2, self.t // 2 + 1)
        a = self.c.create_oval(x0 + 3, y0 + h * 0.3 - r, x0 + 3 + 2 * r, y0 + h * 0.3 + r, fill=self.on, outline='')
        b = self.c.create_oval(x0 + 3, y0 + h * 0.7 - r, x0 + 3 + 2 * r, y0 + h * 0.7 + r, fill=self.on, outline='')
        return (a, b)

    def show(self, text, title=None):
        """text = 'HH:MM:SS'"""
        if title is not None:
            self.c.itemconfigure(self.title, text=title)
        for ch, it in zip(text, self.items):
            if isinstance(it, tuple):
                continue
            lit = _SEG.get(ch, '')
            for name, poly in it.items():
                self.c.itemconfigure(poly, fill=self.on if name in lit else self.off)


# ============================================================================ clipboard everywhere
# Ctrl+C / V / X / A must also work with a Russian keyboard layout (Tk sees Cyrillic keysyms then), and
# every input field and the chat get a right-click menu.
_CYR = {'Cyrillic_es': 'c', 'Cyrillic_em': 'v', 'Cyrillic_che': 'x', 'Cyrillic_ef': 'a',
        'Cyrillic_ES': 'c', 'Cyrillic_EM': 'v', 'Cyrillic_CHE': 'x', 'Cyrillic_EF': 'a'}
# Windows virtual key codes of C, V, X, A (layout independent)
_VK = {67: 'c', 86: 'v', 88: 'x', 65: 'a'}


def _is_readonly(w):
    try:
        return str(w.cget('state')) in ('disabled', 'readonly')
    except Exception:
        return False


def _do(w, what):
    try:
        if what == 'a':
            if w.winfo_class() == 'Text':
                w.tag_add('sel', '1.0', 'end-1c')
            else:
                w.select_range(0, 'end')
                w.icursor('end')
            return 'break'
        if what in ('x', 'v') and _is_readonly(w):
            if what == 'v':
                return 'break'
            what = 'c'
        w.event_generate({'c': '<<Copy>>', 'v': '<<Paste>>', 'x': '<<Cut>>'}[what])
    except Exception:
        pass
    return 'break'


def install_clipboard(root, tk):
    def on_key(ev):
        what = _CYR.get(ev.keysym)
        if what is None and sys.platform.startswith('win'):
            what = _VK.get(ev.keycode) if ev.keysym.lower() not in ('c', 'v', 'x', 'a') else None
        if what is None:
            return None
        return _do(ev.widget, what)

    def menu(ev):
        w = ev.widget
        m = tk.Menu(w, tearoff=0)
        ro = _is_readonly(w) or w.winfo_class() == 'Text' and str(w.cget('state')) == 'disabled'
        if not ro:
            m.add_command(label=T('Вырезать'), command=lambda: _do(w, 'x'))
        m.add_command(label=T('Копировать'), command=lambda: _do(w, 'c'))
        if not ro:
            m.add_command(label=T('Вставить'), command=lambda: _do(w, 'v'))
        m.add_separator()
        m.add_command(label=T('Выделить всё'), command=lambda: _do(w, 'a'))
        try:
            w.focus_set()
        except Exception:
            pass
        m.tk_popup(ev.x_root, ev.y_root)
        return 'break'

    mod = 'Command' if sys.platform == 'darwin' else 'Control'
    for cls in ('Entry', 'TEntry', 'Text', 'TCombobox', 'Spinbox', 'TSpinbox'):
        root.bind_class(cls, '<%s-KeyPress>' % mod, on_key, add='+')
        root.bind_class(cls, '<Button-3>', menu, add='+')
        if sys.platform == 'darwin':
            root.bind_class(cls, '<Button-2>', menu, add='+')
            root.bind_class(cls, '<Control-Button-1>', menu, add='+')
    # a disabled Text (the chat) ignores <<Copy>> on some Tk versions: copy the selection by hand
    def text_copy(ev):
        try:
            sel = ev.widget.get('sel.first', 'sel.last')
            ev.widget.clipboard_clear()
            ev.widget.clipboard_append(sel)
        except Exception:
            pass
        return 'break'
    root.bind_class('Text', '<<Copy>>', text_copy)


# ============================================================================ message field with a limit
class LimitedText:
    """One- or two-line text field; characters beyond the limit are shown red.
    count(text) -> list of cumulative "cost" per character (bytes / transliterated length)."""

    def __init__(self, tk, parent, limit, cost, on_change=None, on_enter=None, width=60, font=None, colors=None):
        self.limit = limit
        self.cost = cost
        self.on_change = on_change
        self.w = tk.Text(parent, height=2, width=width, wrap='word', undo=True, font=font)
        if colors:
            self.w.configure(background=colors['field'], foreground=colors['fg'],
                             insertbackground=colors['fg'], selectbackground=colors['sel'])
        self.w.tag_configure('over', foreground='#ffffff', background='#d0021b')
        self.w.bind('<KeyRelease>', lambda e: self.update())
        self.w.bind('<<Paste>>', lambda e: self.w.after(1, self.update), add='+')
        if on_enter:
            def enter(ev):
                on_enter()
                return 'break'
            self.w.bind('<Return>', enter)
            self.w.bind('<KP_Enter>', enter)
        self.w.bind('<Tab>', lambda e: (e.widget.tk_focusNext().focus_set(), 'break')[1])

    def get(self):
        return self.w.get('1.0', 'end-1c').replace('\n', ' ')

    def set(self, text):
        self.w.delete('1.0', 'end')
        self.w.insert('1.0', text)
        self.update()

    def over_from(self):
        """index of the first character beyond the limit, or None"""
        for i, c in enumerate(self.cost(self.get())):
            if c > self.limit:
                return i
        return None

    def update(self):
        self.w.tag_remove('over', '1.0', 'end')
        i = self.over_from()
        if i is not None:
            self.w.tag_add('over', '1.0 + %d chars' % i, 'end-1c')
        if self.on_change:
            self.on_change()


def cost_hfp(text):
    out, n = [], 0
    for ch in text:
        n += len(ch.encode('cp1251', 'replace'))
        out.append(n)
    return out


def cost_selcall(use_translit):
    def f(text):
        out, n = [], 0
        for ch in text:
            n += len(SE.translit(ch)) if use_translit() else 1
            out.append(n)
        return out
    return f


# ============================================================================ the application window
class App:
    def __init__(self, root, tk, ttk, messagebox, filedialog, tkfont):
        self.root, self.tk, self.ttk = root, tk, ttk
        self.mb, self.fd, self.tkfont = messagebox, filedialog, tkfont
        self.q = queue.Queue()
        self.core = A.Core(self.q)
        i18n.set_lang(self.core.s.get('lang', 'ru'))
        self.rig_ui = {}
        self.ob_ui = {}
        self.rx_state = {'state': 'idle', 'flash_until': 0.0}
        self.clip_until = 0.0
        self.peak_hold = (-90.0, 0.0)          # dBFS, time
        self.banner_call = None
        self.wf = None
        self.wf_state = {'lo': None, 'img': None}
        self.base_style = None
        self.chat_lines = []                   # (text, tag): kept across rebuilds (language / theme)
        install_clipboard(root, tk)
        root.bind_all('<F1>', lambda e: self.open_help())
        self.scroll_canvases = []
        self.install_wheel()
        try:
            self.icon = tk.PhotoImage(file=os.path.join(_here(), 'icon.png'))
            root.iconphoto(True, self.icon)
        except Exception:
            self.icon = None
        self.build()

    # ------------------------------------------------------------------ build / rebuild
    @property
    def dark(self):
        return self.core.s.get('theme') == 'dark'

    def colors(self):
        if self.dark:
            return DARK
        return dict(bg=None, fg='#000000', field='#ffffff', sel='#a6c8ff', dim='#777777', border='#c0c0c0')

    def apply_theme(self):
        ttk, root = self.ttk, self.root
        st = ttk.Style(root)
        if self.base_style is None:
            self.base_style = st.theme_use()
        root.option_clear()
        if not self.dark:
            st.theme_use(self.base_style)
            try:
                root.configure(background=self.root_bg_default)
            except Exception:
                pass
            return
        c = DARK
        st.theme_use('clam')
        st.configure('.', background=c['bg'], foreground=c['fg'], fieldbackground=c['field'],
                     bordercolor=c['border'], lightcolor=c['bg'], darkcolor=c['bg'], troughcolor=c['field'],
                     selectbackground=c['sel'], selectforeground='#ffffff', insertcolor=c['fg'])
        st.configure('TButton', background=c['button'])
        st.map('TButton', background=[('active', c['active']), ('disabled', c['bg'])],
               foreground=[('disabled', '#666666')])
        st.map('TCheckbutton', background=[('active', c['bg'])], indicatorcolor=[('selected', '#4c8bf5')])
        st.map('TRadiobutton', background=[('active', c['bg'])], indicatorcolor=[('selected', '#4c8bf5')])
        st.configure('TEntry', fieldbackground=c['field'], foreground=c['fg'])
        st.map('TCombobox', fieldbackground=[('readonly', c['field'])], foreground=[('readonly', c['fg'])],
               selectbackground=[('readonly', c['field'])], selectforeground=[('readonly', c['fg'])])
        st.configure('TNotebook', background=c['bg'], bordercolor=c['border'])
        st.configure('TNotebook.Tab', background=c['tab'], foreground=c['dim'], padding=(10, 4))
        st.map('TNotebook.Tab', background=[('selected', c['tab_sel'])], foreground=[('selected', c['fg'])])
        st.configure('Treeview', background=c['field'], fieldbackground=c['field'], foreground=c['fg'])
        st.configure('Treeview.Heading', background=c['button'], foreground=c['fg'])
        st.configure('TLabelframe.Label', foreground=c['fg'])
        root.configure(background=c['bg'])
        root.option_add('*TCombobox*Listbox.background', c['field'])
        root.option_add('*TCombobox*Listbox.foreground', c['fg'])
        root.option_add('*TCombobox*Listbox.selectBackground', c['sel'])
        root.option_add('*Menu.background', c['button'])
        root.option_add('*Menu.foreground', c['fg'])
        root.option_add('*Menu.activeBackground', c['sel'])
        root.option_add('*Text.background', c['field'])
        root.option_add('*Text.foreground', c['fg'])
        root.option_add('*Toplevel.background', c['bg'])

    def rebuild(self):
        """language / theme changed: recreate all widgets (the Core and the audio keep running)"""
        self.pull()
        self.core.save()
        for d in (self.rig_ui, self.ob_ui):
            w = d.get('win')
            if w is not None:
                try:
                    w.destroy()
                except Exception:
                    pass
            d.clear()
        for w in list(self.root.winfo_children()):
            try:
                w.destroy()
            except Exception:
                pass
        self.root.configure(menu='')
        i18n.set_lang(self.core.s.get('lang', 'ru'))
        self.build()

    def build(self):
        tk, ttk, core, root = self.tk, self.ttk, self.core, self.root
        if not hasattr(self, 'root_bg_default'):
            try:
                self.root_bg_default = root.cget('background')
            except Exception:
                self.root_bg_default = None
        self.apply_theme()
        root.title('%s — HFPager (PS-18) %s HF Selcall (CCIR 493-4, CODAN)   v%s' % (
            A.APP_NAME, T('и'), A.APP_VERSION))
        self.make_vars()
        self.build_menu()
        self.build_monitor()
        # status bar first (packed at the bottom), then the banner place and the notebook
        sbar = ttk.Frame(root)
        sbar.pack(side='bottom', fill='x', padx=8, pady=(0, 4))
        ttk.Label(sbar, textvariable=self.var['status'], width=28).pack(side='left')
        ttk.Label(sbar, textvariable=self.var['info']).pack(side='left', padx=8)
        ttk.Label(sbar, textvariable=self.var['scan_info'], foreground='#d08000').pack(side='left', padx=8)
        ttk.Label(sbar, text='%s  v%s' % (A.COPYRIGHT, A.APP_VERSION), foreground=self.colors()['dim']).pack(
            side='right')
        self.banner_box = ttk.Frame(root)
        self.banner_box.pack(side='top', fill='x')
        self.tab_outer = []
        self.scroll_canvases = []
        self.nb = ttk.Notebook(root)
        self.nb.pack(side='top', fill='both', expand=True, padx=8, pady=(2, 4))
        self.build_chat_tab()
        self.build_hfp_tab()
        self.build_selcall_tab()
        self.build_rig_tab()
        self.build_beacon_tab()
        self.build_program_tab()
        try:
            self.nb.select(self.tab_outer[int(core.s.get('tab', 0))])
        except Exception:
            pass
        self.refresh_devices()
        self.refresh_ports()
        self.update_counter()
        self.sel_update_counter()
        self.update_sel_buttons()
        self.update_scan_ui()
        for text, tag in self.chat_lines[-2000:]:
            self._insert(text, tag)
        if self.banner_call is not None:
            c_, t_, p_ = self.banner_call
            self.show_banner(c_, t_, ring=False, proto=p_)

    def make_vars(self):
        tk, s = self.tk, self.core.s

        def sv(k, fmt=None):
            v = s.get(k, '')
            return tk.StringVar(value=(fmt % v) if fmt else str(v))

        def bv(k):
            return tk.BooleanVar(value=bool(s.get(k)))

        styles = dict(SE.RING_STYLES)
        self.var = dict(
            my_id=sv('my_id'), to_id=sv('to_id'), in_dev=sv('in_dev'), out_dev=sv('out_dev'), speed=sv('speed'),
            f0=sv('f0'), tx_level=tk.DoubleVar(value=s['tx_level']), ptt_delay=sv('ptt_delay'), afc=bv('afc'),
            ack=bv('ack'), auto_ack=bv('auto_ack'), only_mine=bv('only_mine'), sens_db=sv('sens_db'),
            ptt_method=sv('ptt_method'), ptt_port=tk.StringVar(value=s['ptt_port'] or T(PORT_OFF)),
            ptt_baud=sv('ptt_baud'), ptt_invert=bv('ptt_invert'), icom_model=sv('icom_model'),
            icom_addr=sv('icom_addr'), kenwood_variant=sv('kenwood_variant'),
            status=tk.StringVar(value=T('Ожидание')), info=tk.StringVar(value=''), counter=tk.StringVar(),
            level_txt=tk.StringVar(value='— dBFS'), clip=tk.StringVar(value=''),
            in_channel=tk.StringVar(value=self.in_channels()[int(s.get('in_channel') or 0)]),
            # selcall
            sel_enable=bv('sel_enable'), hfp_enable=bv('hfp_enable'), scan_btn=tk.BooleanVar(value=False),
            scan_calc=tk.StringVar(value=''), chan_sel=tk.IntVar(value=-1), sel_my_id=sv('sel_my_id'), sel_to_id=sv('sel_to_id'),
            sel_dot_seconds=sv('sel_dot_seconds'), sel_translit=bv('sel_translit'), sel_afc=bv('sel_afc'),
            sel_center=sv('sel_center', '%.0f'), sel_ring=bv('sel_ring'),
            sel_ring_style=tk.StringVar(value=T(styles.get(s['sel_ring_style'], SE.RING_STYLES[0][1]))),
            sel_ring_dev=tk.StringVar(value=s['sel_ring_dev'] or T(SYS_OUT)),
            sel_ring_seconds=sv('sel_ring_seconds', '%g'), sel_counter=tk.StringVar(),
            sel_ring_air=bv('sel_ring_air'),
            sel_answer_style=tk.StringVar(value=T(styles.get(s['sel_answer_style'], SE.RING_STYLES[-1][1]))),
            sel_ext_enabled=bv('sel_ext_enabled'), sel_ext_port=tk.StringVar(value=s['sel_ext_port'] or T(PORT_OFF)),
            sel_ext_line=sv('sel_ext_line'), sel_ext_invert=bv('sel_ext_invert'),
            sel_ext_seconds=sv('sel_ext_seconds', '%g'), sel_listen_after_call=bv('sel_listen_after_call'),
            sel_listen_seconds=sv('sel_listen_seconds', '%g'), sel_listen_after_tx=bv('sel_listen_after_tx'),
            sel_listen_after_tx_seconds=sv('sel_listen_after_tx_seconds', '%g'), sel_centers=tk.StringVar(),
            sel_banner=tk.StringVar(),
            # HFPager call / ring / answer, BCN REQ
            call_text=sv('call_text'), hfp_ring=bv('hfp_ring'),
            hfp_ring_style=tk.StringVar(value=T(styles.get(s['hfp_ring_style'], SE.RING_STYLES[0][1]))),
            hfp_ring_seconds=sv('hfp_ring_seconds', '%g'), hfp_msg_sound=bv('hfp_msg_sound'),
            hfp_msg_style=tk.StringVar(value=T(styles.get(s['hfp_msg_style'], SE.RING_STYLES[2][1]))),
            hfp_ring_air=bv('hfp_ring_air'),
            hfp_answer_style=tk.StringVar(value=T(styles.get(s['hfp_answer_style'], SE.RING_STYLES[-1][1]))),
            hfp_listen_after_call=bv('hfp_listen_after_call'), hfp_listen_seconds=sv('hfp_listen_seconds', '%g'),
            hfp_ext_enabled=bv('hfp_ext_enabled'),
            bcn_req_enable=bv('bcn_req_enable'), bcn_req_text=sv('bcn_req_text'),
            bcn_req_style=tk.StringVar(value=T(styles.get(s['bcn_req_style'], SE.RING_STYLES[-1][1]))),
            # beacon
            bcn_enable=bv('bcn_enable'), bcn_mode=tk.StringVar(value=s.get('bcn_mode', 'interval')),
            bcn_interval=sv('bcn_interval', '%g'), bcn_times=sv('bcn_times'),
            bcn_kind=tk.StringVar(value=self.kind_label(s.get('bcn_kind', 'hfp_beacon'))),
            bcn_to=sv('bcn_to'), bcn_text=sv('bcn_text'), bcn_cw_wpm=sv('bcn_cw_wpm', '%g'),
            bcn_cw_tone=sv('bcn_cw_tone', '%g'), bcn_next=tk.StringVar(value=''),
            # preamble / scanning
            hfp_pre_seconds=sv('hfp_pre_seconds', '%g'), pre_info=tk.StringVar(value=''),
            scan_resume=sv('scan_resume', '%g'), scan_info=tk.StringVar(value=''),
            # CAT
            rig_proto=sv('rig_proto'), rig_port=tk.StringVar(value=s['rig_port'] or T(PORT_OFF)),
            rig_baud=sv('rig_baud'), rig_freq=tk.StringVar(value='7.100'), rig_mode=tk.StringVar(value='USB'),
            rig_cur=tk.StringVar(value='—'),
            # program
            lang=tk.StringVar(value='English' if s.get('lang') == 'en' else 'Русский'),
            theme=tk.StringVar(value=T('Тёмная') if s.get('theme') == 'dark' else T('Светлая')),
            clock_tz=tk.StringVar(value=tz_label(s.get('clock_tz', 'MSK'))),
            log_dir=tk.StringVar(value=self.core.data_dir()),
        )

    KINDS = [('hfp_beacon', 'HFPager: кадр «маяк»'), ('hfp_msg', 'HFPager: сообщение'),
             ('hfp_call', 'HFPager: вызов (CALL)'), ('sel_call', 'Selcall: вызов'), ('sel_msg', 'Selcall: сообщение'),
             ('cw', 'CW (телеграф)')]

    @classmethod
    def kind_label(cls, key):
        return T(dict(cls.KINDS).get(key, key))

    @classmethod
    def kind_key(cls, label):
        for k, t in cls.KINDS:
            if T(t) == label:
                return k
        return None

    @staticmethod
    def in_channels():
        return [T('авто (где есть сигнал)'), T('1 (левый)'), T('2 (правый)')]

    # ------------------------------------------------------------------ menu
    def build_menu(self):
        tk = self.tk
        m = tk.Menu(self.root)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label=T('Открыть журнал (TXT)'), command=self.open_log)
        f.add_command(label=T('Папка журнала и отложенных…'), command=self.choose_log_dir)
        f.add_command(label=T('Отложенные сообщения…'), command=self.open_outbox_window)
        f.add_separator()
        f.add_command(label=T('Выход'), command=self.on_close)
        m.add_cascade(label=T('Файл'), menu=f)
        v = tk.Menu(m, tearoff=0)
        self.m_theme = tk.StringVar(value=self.core.s.get('theme', 'light'))
        self.m_lang = tk.StringVar(value=self.core.s.get('lang', 'ru'))
        v.add_radiobutton(label=T('Светлая тема'), variable=self.m_theme, value='light',
                          command=lambda: self.set_theme('light'))
        v.add_radiobutton(label=T('Тёмная тема'), variable=self.m_theme, value='dark',
                          command=lambda: self.set_theme('dark'))
        v.add_separator()
        v.add_radiobutton(label='Русский', variable=self.m_lang, value='ru', command=lambda: self.set_lang('ru'))
        v.add_radiobutton(label='English', variable=self.m_lang, value='en', command=lambda: self.set_lang('en'))
        m.add_cascade(label=T('Вид'), menu=v)
        h = tk.Menu(m, tearoff=0)
        h.add_command(label=T('Инструкция (F1)'), command=self.open_help)
        h.add_command(label=T('О программе'), command=self.about)
        m.add_cascade(label=T('Справка'), menu=h)
        self.root.configure(menu=m)

    def set_theme(self, theme):
        if self.core.s.get('theme') != theme:
            self.pull()
            self.core.s['theme'] = theme
            self.rebuild()

    def set_lang(self, lang):
        if self.core.s.get('lang') != lang:
            self.pull()
            self.core.s['lang'] = lang
            self.rebuild()

    # ------------------------------------------------------------------ monitor strip (always visible)
    def build_monitor(self):
        tk, ttk = self.tk, self.ttk
        # one group centred in the window, equal gaps between its parts:
        # lamps · level meter · spectrum · clocks · decoder buttons
        bar = ttk.Frame(self.root)
        bar.pack(side='top', fill='x', pady=(8, 2))
        mon = ttk.Frame(bar)
        mon.pack(side='top')                  # packed without fill: centred, free space split left / right
        GAP = 10
        lamp_fr = ttk.Frame(mon)
        lamp_fr.pack(side='left', padx=GAP)

        def make_lamp(col, label, off):
            c = tk.Canvas(lamp_fr, width=34, height=34, highlightthickness=0,
                          background=self.colors()['bg'] or self.root_bg_default)
            c.grid(row=0, column=col, padx=4)
            oval = c.create_oval(4, 4, 30, 30, fill=off, outline='#222222', width=2)
            ttk.Label(lamp_fr, text=label, font=('Helvetica', 11, 'bold')).grid(row=1, column=col)
            return c, oval
        self.rx_lamp = make_lamp(0, 'RX', LAMP['rx_off'])
        self.tx_lamp = make_lamp(1, 'TX', LAMP['tx_off'])

        meter = ttk.Frame(mon)
        meter.pack(side='left', padx=GAP)
        ttk.Label(meter, text=T('Уровень входа (пик), dBFS')).pack(anchor='w')
        self.meter = tk.Canvas(meter, width=METER_W, height=METER_H + 12, highlightthickness=0,
                               background=self.colors()['bg'] or self.root_bg_default)
        self.meter.pack(anchor='w', pady=2)
        x_ = lambda db: (db + 60) / 60.0 * METER_W
        # scale: green up to -12 dBFS, yellow -12…-3, red above -3; overload = 0.98 FS (-0.2 dBFS)
        for a, b, col in ((-60, -12, '#123d12'), (-12, -3, '#3d3a10'), (-3, 0, '#4a1010')):
            self.meter.create_rectangle(x_(a), 0, x_(b), METER_H, fill=col, outline='')
        self.meter_bar = self.meter.create_rectangle(0, 2, 0, METER_H - 2, fill='#2ecc40', outline='')
        self.meter_peak = self.meter.create_line(0, 0, 0, METER_H, fill='#ffffff', width=2)
        for db in (-60, -48, -36, -24, -12, -3, 0):
            self.meter.create_line(x_(db), METER_H, x_(db), METER_H + 3, fill=self.colors()['dim'])
            self.meter.create_text(min(max(x_(db), 8), METER_W - 6), METER_H + 8, text=str(db),
                                   font=('Helvetica', 7), fill=self.colors()['dim'])
        row = ttk.Frame(meter)
        row.pack(anchor='w')
        ttk.Label(row, textvariable=self.var['level_txt'], width=11).pack(side='left')
        ttk.Label(row, textvariable=self.var['clip'], foreground='#e02020').pack(side='left')

        # spectrum (waterfall) 300..3000 Hz, newest line on top: 270 bins of 10 Hz drawn WF_W pixels wide
        WF_W, WF_H, ZOOM = 360, 50, 2
        self.WF = (WF_W, WF_H, ZOOM)
        if self.wf is None or self.wf.shape != (WF_H, WF_W):
            self.wf = np.full((WF_H, WF_W), -120.0, dtype=np.float32)
        _pos = [0.0, 0.25, 0.55, 0.8, 1.0]
        _lx = np.linspace(0, 1, 256)
        self.lut = np.stack([np.interp(_lx, _pos, c) for c in
                             ([0, 0, 40, 255, 255], [0, 50, 230, 255, 255], [0, 0, 40, 60, 200])],
                            axis=1).astype(np.uint8)
        wf_box = ttk.Frame(mon)
        wf_box.pack(side='left', padx=GAP)
        self.wf_canvas = tk.Canvas(wf_box, width=WF_W, height=WF_H * ZOOM, background='black',
                                   highlightthickness=1, highlightbackground='#333333')
        self.wf_canvas.pack()
        self.wf_item = self.wf_canvas.create_image(0, 0, anchor='nw')
        axis = tk.Canvas(wf_box, width=WF_W, height=14, highlightthickness=0,
                         background=self.colors()['bg'] or self.root_bg_default)
        axis.pack()
        for f_hz in (500, 1000, 1500, 2000, 2500, 3000):
            xx = (f_hz - 300) / 2700.0 * WF_W
            axis.create_line(xx, 0, xx, 4, fill=self.colors()['dim'])
            axis.create_text(min(xx, WF_W - 14), 10, text=str(f_hz), font=('Helvetica', 8),
                             fill=self.colors()['dim'])
        clk = ttk.Frame(mon)
        clk.pack(side='left', padx=GAP)
        dec = ttk.Frame(mon)
        dec.pack(side='left', padx=GAP)
        self.tb_hfp = ttk.Checkbutton(dec, text='HFPager', style='Toolbutton', variable=self.var['hfp_enable'],
                                      command=self.toggle_hfp, width=13)
        self.tb_hfp.pack(fill='x', pady=(0, 6))
        self.tb_sel = ttk.Checkbutton(dec, text='Selcall', style='Toolbutton', variable=self.var['sel_enable'],
                                      command=self.toggle_sel, width=13)
        self.tb_sel.pack(fill='x')
        self.update_decoder_buttons()

        self.clock_utc = SegClock(tk, clk, 'UTC')
        self.clock_utc.c.pack(pady=(0, 4))
        self.clock_loc = SegClock(tk, clk, tz_time(self.core.s.get('clock_tz', 'MSK'))[0])
        self.clock_loc.c.pack()
        self.tick_clock()

    def tick_clock(self):
        try:
            u = datetime.datetime.utcnow()
            self.clock_utc.show(u.strftime('%H:%M:%S'))
            lbl, t = tz_time(self.core.s.get('clock_tz', 'MSK'))
            self.clock_loc.show(t.strftime('%H:%M:%S'), lbl)
        except Exception:
            pass

    def draw_waterfall(self):
        WF_W, WF_H, ZOOM = self.WF
        tk = self.tk
        norm = np.clip((self.wf - self.wf_state['lo']) / 45.0, 0.0, 1.0)
        rgb = self.lut[(norm * 255).astype(np.uint8)]
        try:
            ppm = b'P6 %d %d 255\n' % (WF_W, WF_H) + rgb.tobytes()
            img = tk.PhotoImage(data=ppm, format='PPM').zoom(1, ZOOM)
        except Exception:            # old Tk (Python 3.8 / Windows 7): pixel-by-pixel put
            img = tk.PhotoImage(width=WF_W, height=WF_H)
            img.put(' '.join('{' + ' '.join('#%02x%02x%02x' % (r_, g_, b_) for r_, g_, b_ in row) + '}'
                             for row in rgb.tolist()))
            img = img.zoom(1, ZOOM)
        self.wf_state['img'] = img
        self.wf_canvas.itemconfig(self.wf_item, image=img)

    def on_spectrum(self, row):
        WF_W = self.WF[0]
        row = np.asarray(row, dtype=np.float32)[:WF_BINS]
        if len(row) < WF_BINS:
            row = np.pad(row, (0, WF_BINS - len(row)), constant_values=-120.0)
        row = np.interp(np.linspace(0, WF_BINS - 1, WF_W), np.arange(WF_BINS), row).astype(np.float32)
        med = float(np.median(row))
        lo = self.wf_state['lo']
        # the colour scale follows the noise floor slowly; while the input is overloaded the clipping products
        # raise the whole spectrum, so the scale is frozen then (otherwise the picture "jumps")
        if lo is None:
            self.wf_state['lo'] = med
        elif time.time() - self.core.clip_time > 2.0:
            self.wf_state['lo'] = 0.99 * lo + 0.01 * med
        self.wf[1:] = self.wf[:-1]
        self.wf[0] = row
        self.draw_waterfall()

    def update_meter(self):
        db = A.read_peak(self.core) if self.core.stream is not None else -90.0
        now_ = time.time()
        hold, t_hold = self.peak_hold
        if db >= hold or now_ - t_hold > 2.0:
            self.peak_hold = (db, now_)
        x_ = lambda d: max(0.0, min(1.0, (d + 60) / 60.0)) * METER_W
        col = '#2ecc40' if db < -12 else ('#f1c40f' if db < -3 else '#e74c3c')
        self.meter.coords(self.meter_bar, 0, 2, x_(db), METER_H - 2)
        self.meter.itemconfigure(self.meter_bar, fill=col)
        hx = x_(self.peak_hold[0])
        self.meter.coords(self.meter_peak, hx, 0, hx, METER_H)
        self.var['level_txt'].set(('%.1f dBFS' % db) if db > -60 else '— dBFS')
        if now_ - self.core.clip_time < 1.5:
            self.var['clip'].set(T('ПЕРЕГРУЗКА ВХОДА — уменьшите уровень!'))
        else:
            self.var['clip'].set('')

    def update_lamps(self):
        t = time.time()
        st = self.rx_state['state']
        if st == 'receiving' or t < self.rx_state['flash_until']:
            colr = LAMP['rx_on']
        elif st == 'decoding':
            colr = LAMP['rx_dec']
        else:
            colr = LAMP['rx_off']
        self.rx_lamp[0].itemconfig(self.rx_lamp[1], fill=colr)
        self.tx_lamp[0].itemconfig(self.tx_lamp[1], fill=LAMP['tx_on'] if self.core.tx_busy else LAMP['tx_off'])

    # ------------------------------------------------------------------ scrollable tabs
    def add_tab(self, title, padding=8):
        """a notebook tab whose content scrolls (both ways) when the window is smaller than the content, and
        stretches to the window when it is larger; returns the frame to build the tab in"""
        tk, ttk = self.tk, self.ttk
        outer = ttk.Frame(self.nb)
        self.nb.add(outer, text=title)
        self.tab_outer.append(outer)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        cv = tk.Canvas(outer, highlightthickness=0, borderwidth=0,
                       background=self.colors()['bg'] or self.root_bg_default)
        vs = ttk.Scrollbar(outer, orient='vertical', command=cv.yview)
        hs = ttk.Scrollbar(outer, orient='horizontal', command=cv.xview)
        cv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        cv.grid(row=0, column=0, sticky='nsew')
        inner = ttk.Frame(cv, padding=padding)
        win = cv.create_window(0, 0, anchor='nw', window=inner)
        state = {'v': None, 'h': None}

        def fit(*_):
            try:
                w, h = cv.winfo_width(), cv.winfo_height()
                rw, rh = inner.winfo_reqwidth(), inner.winfo_reqheight()
            except Exception:
                return
            if w <= 1 or h <= 1:
                return
            cv.itemconfigure(win, width=max(w, rw), height=max(h, rh))
            cv.configure(scrollregion=(0, 0, max(w, rw), max(h, rh)))
            need_v, need_h = rh > h, rw > w
            if need_v != state['v']:
                state['v'] = need_v
                (vs.grid(row=0, column=1, sticky='ns') if need_v else vs.grid_remove())
            if need_h != state['h']:
                state['h'] = need_h
                (hs.grid(row=1, column=0, sticky='ew') if need_h else hs.grid_remove())
            if not need_v:
                cv.yview_moveto(0)
            if not need_h:
                cv.xview_moveto(0)
        cv.bind('<Configure>', fit)
        inner.bind('<Configure>', fit)
        self.scroll_canvases.append(cv)
        return inner

    def install_wheel(self):
        """mouse wheel scrolls the tab under the pointer (Text, lists and tables keep their own scrolling)"""
        def canvas_of(w):
            while w is not None:
                if w in self.scroll_canvases:
                    return w
                try:
                    w = w.master
                except Exception:
                    return None
            return None

        def wheel(ev):
            w = ev.widget
            try:
                if w.winfo_class() in ('Text', 'Listbox', 'Treeview', 'TCombobox'):
                    return None
            except Exception:
                return None
            cv = canvas_of(w)
            if cv is None:
                return None
            if getattr(ev, 'num', None) == 4:
                step = -1
            elif getattr(ev, 'num', None) == 5:
                step = 1
            else:
                d = ev.delta
                step = -int(d / 120) if abs(d) >= 120 else (-1 if d > 0 else 1)
            if ev.state & 0x1:                    # Shift + wheel: sideways
                cv.xview_scroll(step, 'units')
            else:
                cv.yview_scroll(step, 'units')
            return None
        for seq in ('<MouseWheel>', '<Shift-MouseWheel>', '<Button-4>', '<Button-5>'):
            self.root.bind_all(seq, wheel, add='+')

    # ------------------------------------------------------------------ tab: chat
    def build_chat_tab(self):
        tk, ttk = self.tk, self.ttk
        f = self.add_tab('  ' + T('Чат и сообщения') + '  ', padding=4)
        # chat on top, the message / call fields below it (packed first, so they keep their size and only
        # the chat shrinks when the window is small)
        self.build_compose(f)
        bar = ttk.Frame(f)
        bar.pack(side='bottom', fill='x', pady=(2, 2))
        # channel row: SCAN + 6 channel buttons (captions from the channel table; right click renames).
        # A grid of equal columns: the buttons share the window width, so all 6 stay visible in a narrow window
        crow = ttk.Frame(f)
        crow.pack(side='bottom', fill='x', pady=(4, 0))
        self.tb_scan = ttk.Checkbutton(crow, text=T('СКАН'), style='Toolbutton', variable=self.var['scan_btn'],
                                       command=self.toggle_scan, width=1)
        self.tb_scan.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        crow.columnconfigure(0, weight=1, uniform='ch', minsize=60)
        self.chan_btns = []
        for i in range(A.SCAN_CHANNELS):
            b = ttk.Radiobutton(crow, text=str(i + 1), style='Toolbutton', variable=self.var['chan_sel'], value=i,
                                command=lambda i_=i: self.on_channel(i_), width=1)
            b.grid(row=0, column=i + 1, sticky='ew', padx=2)
            crow.columnconfigure(i + 1, weight=1, uniform='ch', minsize=60)
            for ev in ('<Button-3>',) + (('<Button-2>', '<Control-Button-1>') if sys.platform == 'darwin' else ()):
                b.bind(ev, lambda e, i_=i: self.rename_channel(i_))
            self.chan_btns.append(b)
        self.refresh_channel_buttons()
        ttk.Checkbutton(bar, text=T('Только адресованные мне (фильтр ID)'), variable=self.var['only_mine'],
                        command=self.apply).pack(side='left')
        ttk.Button(bar, text=T('Очистить окно'), command=self.clear_chat).pack(side='right', padx=4)
        ttk.Button(bar, text=T('Журнал (TXT)'), command=self.open_log).pack(side='right', padx=4)
        CF = 13 if sys.platform == 'darwin' else 12
        self.CF = CF
        GREEN, GREEN_DIM, RED, YELLOW = '#33ff33', '#1f9e1f', '#ff4a4a', '#ffee33'
        CYAN, CYAN_DIM = '#4fd8ff', '#2b8099'
        mono = A.MONO_FONT
        # the chat keeps a fixed minimum size: when the window is small it scrolls instead of collapsing
        self.chat = tk.Text(f, wrap='word', state='disabled', font=(mono, CF), background='#000000', height=8,
                            foreground=GREEN, insertbackground=GREEN, selectbackground='#145214', padx=6, pady=4)
        sb = ttk.Scrollbar(f, command=self.chat.yview)
        self.chat.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self.chat.pack(fill='both', expand=True)
        c = self.chat
        c.tag_configure('tome', foreground=GREEN, font=(mono, CF, 'bold'))
        c.tag_configure('rx', foreground=CYAN)
        c.tag_configure('beacon', foreground=CYAN)
        c.tag_configure('dup_o', foreground=CYAN_DIM)
        c.tag_configure('dup', foreground=GREEN_DIM)
        c.tag_configure('mine', foreground=RED)
        c.tag_configure('sys', foreground=YELLOW, font=(mono, CF - 1, 'italic'))
        c.tag_configure('note', foreground=YELLOW, font=(mono, CF, 'bold'))
        c.bind('<Button-1>', lambda e: c.focus_set())

    def _insert(self, text, tag):
        self.chat.configure(state='normal')
        self.chat.insert('end', text + '\n', tag)
        self.chat.configure(state='disabled')
        self.chat.see('end')

    def add(self, text, tag):
        self.chat_lines.append((text, tag))
        if len(self.chat_lines) > 4000:
            del self.chat_lines[:1000]
        self._insert(text, tag)

    def clear_chat(self):
        self.chat_lines.clear()
        self.chat.configure(state='normal')
        self.chat.delete('1.0', 'end')
        self.chat.configure(state='disabled')

    @staticmethod
    def now():
        return datetime.datetime.now().strftime('%H:%M:%S')

    # ------------------------------------------------------------------ tab: new message / call
    def build_compose(self, parent):
        """HFPager (left) and HF Selcall (right) message / call fields under the chat"""
        tk, ttk = self.tk, self.ttk
        f = ttk.Frame(parent)
        f.pack(side='bottom', fill='x', pady=(4, 0))
        f.columnconfigure(0, weight=1, uniform='c')
        f.columnconfigure(1, weight=1, uniform='c')
        size = 17 if sys.platform == 'darwin' else 15
        font = (A.MONO_FONT, size)
        colors = self.colors() if self.dark else None

        h = ttk.LabelFrame(f, text=T('HFPager (PS-18)'), padding=6)
        h.grid(row=0, column=0, sticky='nsew', padx=(0, 4))
        r = ttk.Frame(h)
        r.pack(fill='x')
        ttk.Label(r, text=T('Кому (ID):')).pack(side='left')
        ttk.Entry(r, textvariable=self.var['to_id'], width=7, font=font).pack(side='left', padx=(4, 10))
        ttk.Combobox(r, textvariable=self.var['speed'], values=list(R.M.SPEEDS), width=6,
                     state='readonly').pack(side='left')
        ttk.Label(r, text=T('Бод')).pack(side='left', padx=(2, 8))
        ttk.Checkbutton(r, text=T('Запрос подтверждения'), variable=self.var['ack']).pack(side='left')
        self.msg = LimitedText(tk, h, 252, cost_hfp, on_change=self.update_counter, on_enter=self.on_send,
                               width=30, font=font, colors=colors)
        self.msg.w.configure(height=3)
        self.msg.w.pack(fill='x', pady=4)
        r = ttk.Frame(h)
        r.pack(fill='x')
        ttk.Label(r, textvariable=self.var['counter'], wraplength=330).pack(side='left')
        self.btn_stop = ttk.Button(r, text=T('Прервать'), command=self.core.abort_tx)
        self.btn_stop.pack(side='right')
        self.btn = ttk.Button(r, text=T('Отправить'), command=self.on_send)
        self.btn.pack(side='right', padx=4)
        self.btn_call = ttk.Button(r, text=T('Вызов'), command=self.on_call)
        self.btn_call.pack(side='right', padx=4)

        s = ttk.LabelFrame(f, text=T('HF Selcall (CCIR 493-4, CODAN)'), padding=6)
        s.grid(row=0, column=1, sticky='nsew', padx=(4, 0))
        r = ttk.Frame(s)
        r.pack(fill='x')
        ttk.Label(r, text=T('Кому (Selcall ID):')).pack(side='left')
        ttk.Entry(r, textvariable=self.var['sel_to_id'], width=7, font=font).pack(side='left', padx=(4, 10))
        ttk.Checkbutton(r, text=T('Транслит'), variable=self.var['sel_translit'],
                        command=lambda: (self.sel_msg.update())).pack(side='left')
        self.sel_msg = LimitedText(tk, s, SE.MAX_MSG, cost_selcall(lambda: bool(self.var['sel_translit'].get())),
                                   on_change=self.sel_update_counter, on_enter=lambda: self.sel_send(True),
                                   width=30, font=font, colors=colors)
        self.sel_msg.w.configure(height=3)
        self.sel_msg.w.pack(fill='x', pady=4)
        r = ttk.Frame(s)
        r.pack(fill='x')
        ttk.Label(r, textvariable=self.var['sel_counter'], wraplength=280).pack(side='left')
        ttk.Button(r, text=T('Прервать'), command=self.core.abort_tx).pack(side='right')
        self.sel_btn_msg = ttk.Button(r, text=T('Сообщение'), command=lambda: self.sel_send(True))
        self.sel_btn_msg.pack(side='right', padx=4)
        self.sel_btn_call = ttk.Button(r, text=T('Вызов'), command=lambda: self.sel_send(False))
        self.sel_btn_call.pack(side='right', padx=4)
        for k in ('sel_dot_seconds', 'sel_my_id', 'sel_to_id'):
            self.var[k].trace_add('write', lambda *a: self.sel_update_counter())
        self.var['speed'].trace_add('write', lambda *a: self.update_counter())
        # macro buttons (only those with a caption), above the message fields
        self.macro_bar = ttk.Frame(parent)
        self.macro_bar.pack(side='bottom', fill='x', pady=(4, 0))
        self.fill_macro_bar()

    def fill_macro_bar(self):
        ttk = self.ttk
        for w in self.macro_bar.winfo_children():
            w.destroy()
        n = 0
        for i, m in enumerate(self.core.s.get('macros') or []):
            if str(m.get('label', '')).strip():
                ttk.Button(self.macro_bar, text=m['label'], command=lambda i_=i: self.run_macro(i_)).pack(
                    side='left', padx=(0, 4))
                n += 1

    def run_macro(self, i):
        """macro: fills the fields; with «сразу» it is sent at once"""
        m = self.core.s['macros'][i]
        kind, to, text = m.get('kind', 'hfp_msg'), str(m.get('to', '')).strip(), m.get('text', '')
        if kind.startswith('hfp'):
            if to:
                self.var['to_id'].set(to)
            if kind == 'hfp_msg':
                self.msg.set(text)
        else:
            if to:
                self.var['sel_to_id'].set(to)
            if kind == 'sel_msg':
                self.sel_msg.set(text)
        if not m.get('now'):
            (self.msg if kind.startswith('hfp') else self.sel_msg).w.focus_set()
            return
        if kind == 'hfp_msg':
            self.on_send()
        elif kind == 'hfp_call':
            self.on_call()
        elif kind == 'sel_call':
            self.sel_send(False)
        else:
            self.sel_send(True)

    # ------------------------------------------------------------------ tab: HFPager
    def build_hfp_tab(self):
        ttk = self.ttk
        f = self.add_tab('  HFPager  ')
        g = ttk.LabelFrame(f, text=T('Параметры HFPager'), padding=6)
        g.pack(fill='x')
        rows = [
            (T('Мой ID (0…65535):'), ttk.Entry(g, textvariable=self.var['my_id'], width=8)),
            (T('Скорость передачи, Бод:'), ttk.Combobox(g, textvariable=self.var['speed'], values=list(R.M.SPEEDS),
                                                         width=7, state='readonly')),
            (T('Тон 0, Гц (300…2000):'), ttk.Entry(g, textvariable=self.var['f0'], width=8)),
            (T('Порог приёма, дБ (1…20):'), ttk.Entry(g, textvariable=self.var['sens_db'], width=8)),
            (T('Преамбула при передаче, с (0 = стандартная):'),
             ttk.Entry(g, textvariable=self.var['hfp_pre_seconds'], width=8)),
        ]
        for i, (lbl, w) in enumerate(rows):
            ttk.Label(g, text=lbl).grid(row=i, column=0, sticky='e', padx=4, pady=3)
            w.grid(row=i, column=1, sticky='w')
        pr = ttk.Frame(g)
        pr.grid(row=len(rows) - 1, column=2, sticky='w', padx=8)
        ttk.Button(pr, text=T('Для сканирования'), command=self.pre_for_scan).pack(side='left')
        ttk.Label(pr, textvariable=self.var['pre_info'], foreground=self.colors()['dim']).pack(side='left', padx=8)
        self.var['speed'].trace_add('write', lambda *a: self.update_pre_info())
        self.var['hfp_pre_seconds'].trace_add('write', lambda *a: self.update_pre_info())
        self.update_pre_info()
        o = ttk.Frame(g)
        o.grid(row=len(rows), column=0, columnspan=3, sticky='w', pady=4)
        ttk.Checkbutton(o, text=T('АПЧ'), variable=self.var['afc']).pack(side='left', padx=4)
        ttk.Checkbutton(o, text=T('Запрос подтверждения'), variable=self.var['ack']).pack(side='left', padx=8)
        ttk.Checkbutton(o, text=T('Автоподтверждение'), variable=self.var['auto_ack']).pack(side='left', padx=8)
        ttk.Checkbutton(o, text=T('Фильтр ID'), variable=self.var['only_mine']).pack(side='left', padx=8)
        styles = [T(t) for _k, t in SE.RING_STYLES]
        g = ttk.LabelFrame(f, text=T('Вызов и сообщения на мой ID'), padding=6)
        g.pack(fill='x', pady=(8, 0))
        r = ttk.Frame(g)
        r.pack(fill='x')
        ttk.Label(r, text=T('Текст вызова (кнопка «Вызов»):')).pack(side='left', padx=4)
        ttk.Entry(r, textvariable=self.var['call_text'], width=10).pack(side='left')
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Звонок при вызове'), variable=self.var['hfp_ring']).pack(side='left', padx=4)
        ttk.Combobox(r, textvariable=self.var['hfp_ring_style'], values=styles, width=22,
                     state='readonly').pack(side='left', padx=4)
        ttk.Label(r, text=T('длительность, с:')).pack(side='left', padx=(8, 2))
        ttk.Entry(r, textvariable=self.var['hfp_ring_seconds'], width=5).pack(side='left')
        ttk.Button(r, text=T('Проверить звонок'), command=lambda: self.test_ring('hfp_')).pack(side='left', padx=8)
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Звук входящего сообщения'), variable=self.var['hfp_msg_sound']).pack(
            side='left', padx=4)
        ttk.Combobox(r, textvariable=self.var['hfp_msg_style'], values=styles, width=22,
                     state='readonly').pack(side='left', padx=4)
        ttk.Button(r, text=T('Прослушать'), command=lambda: self.preview('hfp_msg_style')).pack(side='left', padx=4)
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Ответ в эфир на вызов (один раз, уровень TX):'),
                        variable=self.var['hfp_ring_air']).pack(side='left', padx=4)
        ttk.Combobox(r, textvariable=self.var['hfp_answer_style'], values=styles, width=22,
                     state='readonly').pack(side='left', padx=4)
        ttk.Button(r, text=T('Прослушать'), command=lambda: self.preview('hfp_answer_style')).pack(side='left',
                                                                                                padx=4)
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Слушать эфир после вызова, с:'),
                        variable=self.var['hfp_listen_after_call']).pack(side='left', padx=4)
        ttk.Entry(r, textvariable=self.var['hfp_listen_seconds'], width=5).pack(side='left')
        ttk.Checkbutton(r, text=T('Включать внешнее устройство при вызове'),
                        variable=self.var['hfp_ext_enabled']).pack(side='left', padx=(16, 4))
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Отвечать мелодией в эфир на сообщение'), variable=self.var['bcn_req_enable']
                        ).pack(side='left', padx=4)
        ttk.Entry(r, textvariable=self.var['bcn_req_text'], width=10).pack(side='left')
        ttk.Label(r, text=T('(только на мой ID):')).pack(side='left', padx=4)
        ttk.Combobox(r, textvariable=self.var['bcn_req_style'], values=styles, width=22,
                     state='readonly').pack(side='left', padx=4)
        b = ttk.Frame(f)
        b.pack(fill='x', pady=8)
        ttk.Button(b, text=T('Применить'), command=self.apply).pack(side='left')
        ttk.Button(b, text=T('Отложенные сообщения (QRU?)…'), command=self.open_outbox_window).pack(side='left',
                                                                                                  padx=8)
        ttk.Label(f, text=T('Мой ID, скорость и тон 0 должны совпадать с настройками корреспондентов. '
                            'Порог приёма: больше — меньше ложных срабатываний, меньше — чувствительнее. '
                            'Звуковые устройства, уровень TX, PTT, устройство звонка и внешнее устройство — на вкладке '
                            '«Трансивер и аудио». Ответ в эфир и ответ на BCN REQ — автоматическая передача.'),
                  foreground=self.colors()['dim'], wraplength=900).pack(anchor='w')

    # ------------------------------------------------------------------ tab: Selcall
    def build_selcall_tab(self):
        ttk = self.ttk
        f = self.add_tab('  HF Selcall  ')
        g = ttk.LabelFrame(f, text=T('Параметры Selcall'), padding=6)
        g.pack(fill='x')
        r = ttk.Frame(g)
        r.pack(fill='x')
        ttk.Checkbutton(r, text=T('Приём Selcall'), variable=self.var['sel_enable'],
                        command=self.restart_rx).pack(side='left', padx=4)
        ttk.Label(r, text=T('Мой Selcall ID:')).pack(side='left', padx=(12, 4))
        ttk.Entry(r, textvariable=self.var['sel_my_id'], width=8).pack(side='left')
        ttk.Label(r, text=T('Точки (фазирование), с:')).pack(side='left', padx=(12, 4))
        ttk.Entry(r, textvariable=self.var['sel_dot_seconds'], width=5).pack(side='left')
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Транслит'), variable=self.var['sel_translit']).pack(side='left', padx=4)
        ttk.Checkbutton(r, text=T('АПЧ'), variable=self.var['sel_afc']).pack(side='left', padx=(12, 4))
        ttk.Label(r, text=T('центр без АПЧ, Гц:')).pack(side='left', padx=(2, 4))
        ttk.Entry(r, textvariable=self.var['sel_center'], width=6).pack(side='left')
        ttk.Label(r, textvariable=self.var['sel_centers'], foreground=self.colors()['dim']).pack(side='left', padx=8)

        g = ttk.LabelFrame(f, text=T('Вызов на мой ID'), padding=6)
        g.pack(fill='x', pady=8)
        styles = [T(t) for _k, t in SE.RING_STYLES]
        r = ttk.Frame(g)
        r.pack(fill='x')
        ttk.Checkbutton(r, text=T('Звонок'), variable=self.var['sel_ring']).pack(side='left', padx=4)
        ttk.Combobox(r, textvariable=self.var['sel_ring_style'], values=styles, width=22,
                     state='readonly').pack(side='left', padx=4)
        ttk.Label(r, text=T('длительность, с:')).pack(side='left', padx=(8, 2))
        ttk.Entry(r, textvariable=self.var['sel_ring_seconds'], width=5).pack(side='left')
        ttk.Button(r, text=T('Проверить звонок'), command=self.test_ring).pack(side='left', padx=8)
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Ответ в эфир (вызывающий слышит, что вызов принят; один раз, уровень TX):'),
                        variable=self.var['sel_ring_air']).pack(side='left', padx=4)
        ttk.Combobox(r, textvariable=self.var['sel_answer_style'], values=styles, width=22,
                     state='readonly').pack(side='left', padx=4)
        ttk.Button(r, text=T('Прослушать'), command=self.test_answer).pack(side='left', padx=4)
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Слушать эфир после вызова на мой ID, с:'),
                        variable=self.var['sel_listen_after_call']).pack(side='left', padx=4)
        ttk.Entry(r, textvariable=self.var['sel_listen_seconds'], width=5).pack(side='left')
        ttk.Checkbutton(r, text=T('после своей передачи (ответ станции), с:'),
                        variable=self.var['sel_listen_after_tx']).pack(side='left', padx=(12, 4))
        ttk.Entry(r, textvariable=self.var['sel_listen_after_tx_seconds'], width=5).pack(side='left')
        self.btn_listen = ttk.Button(r, text=T('Слушать'), width=12, command=self.core.toggle_listen)
        self.btn_listen.pack(side='left', padx=10)
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(4, 0))
        ttk.Checkbutton(r, text=T('Включать внешнее устройство (настройка — на вкладке «Трансивер и аудио»)'),
                        variable=self.var['sel_ext_enabled']).pack(side='left', padx=4)
        b = ttk.Frame(f)
        b.pack(fill='x')
        ttk.Button(b, text=T('Применить'), command=self.apply).pack(side='left')
        ttk.Label(f, text=T('Selcall передаётся через тот же выход, с тем же уровнем TX и тем же PTT/CAT. '
                            'Частоты: 1700/1870 Гц (центр 1785 Гц, USB). Звонок и прослушивание идут на выбранное '
                            'устройство (например, динамики компьютера).'),
                  foreground=self.colors()['dim'], wraplength=900).pack(anchor='w', pady=6)

    # ------------------------------------------------------------------ tab: transceiver & audio
    def build_rig_tab(self):
        tk, ttk = self.tk, self.ttk
        f = self.add_tab('  ' + T('Трансивер и аудио') + '  ')
        dim = self.colors()['dim']

        a = ttk.LabelFrame(f, text=T('Звуковой интерфейс'), padding=6)
        a.pack(fill='x')
        ttk.Label(a, text=T('Вход (приём):')).grid(row=0, column=0, sticky='e', padx=4, pady=3)
        self.cb_in = ttk.Combobox(a, textvariable=self.var['in_dev'], width=48, state='readonly')
        self.cb_in.grid(row=0, column=1, sticky='w')
        self.cb_in.bind('<<ComboboxSelected>>', lambda e: self.restart_rx())
        ttk.Label(a, text=T('канал:')).grid(row=0, column=2, sticky='e', padx=(8, 2))
        cb = ttk.Combobox(a, textvariable=self.var['in_channel'], values=self.in_channels(), width=22,
                          state='readonly')
        cb.grid(row=0, column=3, sticky='w')
        cb.bind('<<ComboboxSelected>>', lambda e: self.apply())
        ttk.Label(a, text=T('Выход (передача):')).grid(row=1, column=0, sticky='e', padx=4, pady=3)
        self.cb_out = ttk.Combobox(a, textvariable=self.var['out_dev'], width=48, state='readonly')
        self.cb_out.grid(row=1, column=1, sticky='w')
        ttk.Label(a, text=T('Звонок и прослушивание:')).grid(row=4, column=0, sticky='e', padx=4, pady=3)
        self.cb_ring = ttk.Combobox(a, textvariable=self.var['sel_ring_dev'], width=48, state='readonly')
        self.cb_ring.grid(row=4, column=1, sticky='w')
        o = ttk.Frame(a)
        o.grid(row=2, column=0, columnspan=4, sticky='w', pady=3)
        ttk.Label(o, text=T('Уровень TX:')).pack(side='left', padx=4)
        ttk.Scale(o, from_=0.05, to=1.0, variable=self.var['tx_level'], length=140).pack(side='left')
        ttk.Label(o, text=T('Задержка PTT/VOX, с:')).pack(side='left', padx=(12, 4))
        ttk.Entry(o, textvariable=self.var['ptt_delay'], width=5).pack(side='left')
        ttk.Button(o, text=T('Обновить список'), command=lambda: (self.refresh_devices(), self.restart_rx())).pack(
            side='left', padx=(16, 4))
        ttk.Button(o, text=T('Применить'), command=self.apply).pack(side='left', padx=4)
        ttk.Label(a, text=T('Перегрузка входа: отсчёты достигают 98 % полной шкалы (−0,2 dBFS). Держите пики '
                            'сигнала в зелёной зоне (ниже −12 dBFS), жёлтая −12…−3, красная выше −3 dBFS.'),
                  foreground=dim, wraplength=880).grid(row=3, column=0, columnspan=4, sticky='w', padx=4)

        pf = ttk.LabelFrame(f, text=T('Управление передачей (PTT)'), padding=6)
        pf.pack(fill='x', pady=8)
        r = ttk.Frame(pf)
        r.pack(fill='x', pady=2)
        ttk.Label(r, text=T('Метод:')).pack(side='left', padx=4)
        cb_pm = ttk.Combobox(r, textvariable=self.var['ptt_method'], values=P.METHODS, width=11, state='readonly')
        cb_pm.pack(side='left')
        cb_pm.bind('<<ComboboxSelected>>',
                   lambda e: self.var['ptt_baud'].set(str(P.DEFAULT_BAUD.get(self.var['ptt_method'].get(), 9600))))
        ttk.Label(r, text=T('COM-порт:')).pack(side='left', padx=(10, 4))
        self.cb_pp = ttk.Combobox(r, textvariable=self.var['ptt_port'], width=30)
        self.cb_pp.pack(side='left')
        ttk.Button(r, text='⟳', width=3, command=self.refresh_ports).pack(side='left', padx=2)
        ttk.Label(r, text=T('Скорость:')).pack(side='left', padx=(10, 4))
        ttk.Combobox(r, textvariable=self.var['ptt_baud'], values=[str(b) for b in P.BAUDS], width=7).pack(side='left')
        ttk.Checkbutton(r, text=T('Инверсия (линия)'), variable=self.var['ptt_invert']).pack(side='left', padx=8)
        r = ttk.Frame(pf)
        r.pack(fill='x', pady=2)
        ttk.Label(r, text=T('ICOM модель:')).pack(side='left', padx=4)
        cb_im = ttk.Combobox(r, textvariable=self.var['icom_model'], values=list(P.ICOM_MODELS), width=16,
                             state='readonly')
        cb_im.pack(side='left')

        def on_icom(*_):
            ad = P.ICOM_MODELS.get(self.var['icom_model'].get())
            if ad is not None:
                self.var['icom_addr'].set('%02X' % ad)
        cb_im.bind('<<ComboboxSelected>>', on_icom)
        ttk.Label(r, text=T('CI-V адрес (hex):')).pack(side='left', padx=(8, 4))
        ttk.Entry(r, textvariable=self.var['icom_addr'], width=5).pack(side='left')
        ttk.Label(r, text=T('KENWOOD команда:')).pack(side='left', padx=(12, 4))
        ttk.Combobox(r, textvariable=self.var['kenwood_variant'], values=P.KENWOOD_VARIANTS, width=6,
                     state='readonly').pack(side='left')
        self.btn_ptt_test = ttk.Button(r, text=T('Тест PTT (1 с, без звука)'), command=self.ptt_test)
        self.btn_ptt_test.pack(side='left', padx=14)
        ttk.Label(pf, text=T('RTS/DTR: «1» на линии COM-порта на время передачи. YAESU: TX1;/TX0;  '
                             'YAESU-OLD: 5-байтовый CAT (FT-817/857/897)  KENWOOD/ELECRAFT: TX;/RX;  '
                             'ICOM: CI-V 1C 00. «Выключено» в списке портов — порт не используется. '
                             'Сначала проверяйте на эквиваленте нагрузки.'),
                  foreground=dim, wraplength=880).pack(anchor='w', padx=4)

        cf = ttk.LabelFrame(f, text=T('Трансивер (CAT): частота, режим, сценарии'), padding=6)
        cf.pack(fill='x')
        r = ttk.Frame(cf)
        r.pack(fill='x', pady=2)
        ttk.Label(r, text=T('Протокол:')).pack(side='left', padx=4)
        ttk.Combobox(r, textvariable=self.var['rig_proto'], values=G.RIG_PROTOS, width=11,
                     state='readonly').pack(side='left')
        ttk.Label(r, text=T('COM-порт:')).pack(side='left', padx=(10, 4))
        self.cb_rp = ttk.Combobox(r, textvariable=self.var['rig_port'], width=30)
        self.cb_rp.pack(side='left')
        ttk.Label(r, text=T('Скорость:')).pack(side='left', padx=(10, 4))
        ttk.Combobox(r, textvariable=self.var['rig_baud'], values=[str(b) for b in P.BAUDS], width=7).pack(
            side='left')

        def same_as_ptt():
            self.pull()
            m = self.core.s['ptt_method']
            if m in G.RIG_PROTOS:
                self.var['rig_proto'].set(m)
            self.var['rig_port'].set(self.var['ptt_port'].get())
            self.var['rig_baud'].set(str(self.core.s['ptt_baud']))
        ttk.Button(r, text=T('Как в PTT'), command=same_as_ptt).pack(side='left', padx=8)
        r = ttk.Frame(cf)
        r.pack(fill='x', pady=3)
        ttk.Label(r, text=T('Частота, МГц:')).pack(side='left', padx=4)
        ttk.Entry(r, textvariable=self.var['rig_freq'], width=11).pack(side='left')
        ttk.Label(r, text=T('Режим:')).pack(side='left', padx=(10, 4))
        ttk.Combobox(r, textvariable=self.var['rig_mode'], values=G.MODES, width=7, state='readonly').pack(
            side='left')
        ttk.Button(r, text=T('Установить'), command=lambda: self.rig_run('FRQ %s %s' % (
            self.var['rig_freq'].get().strip() or '0', self.var['rig_mode'].get()))).pack(side='left', padx=6)
        ttk.Button(r, text=T('Только режим'), command=lambda: self.rig_run('MODE %s' % self.var['rig_mode'].get())
                   ).pack(side='left')
        ttk.Button(r, text=T('Прочитать частоту'), command=self.rig_read).pack(side='left', padx=10)
        ttk.Label(r, textvariable=self.var['rig_cur'], font=(A.MONO_FONT, 12, 'bold')).pack(side='left', padx=4)
        r = ttk.Frame(cf)
        r.pack(fill='x', pady=3)
        ttk.Label(r, text=T('Диапазон, м:')).pack(side='left', padx=4)
        for bnd in G.BANDS:
            ttk.Button(r, text=str(bnd), width=4, command=lambda b_=bnd: self.rig_run('BND %d' % b_)).pack(side='left')
        r = ttk.Frame(cf)
        r.pack(fill='x', pady=3)
        ttk.Label(r, text=T('Шаг, кГц:')).pack(side='left', padx=4)
        for lbl, act in (('−10', 'DOWN 10'), ('−1', 'DOWN 1'), ('−0.1', 'DOWN 0.1'),
                         ('+0.1', 'UP 0.1'), ('+1', 'UP 1'), ('+10', 'UP 10')):
            ttk.Button(r, text=lbl, width=5, command=lambda a_=act: self.rig_run(a_)).pack(side='left')
        ttk.Button(r, text=T('Сценарии…'), command=self.open_rig_window).pack(side='left', padx=16)

        sf = ttk.LabelFrame(f, text=T('Сканирование каналов (через CAT)'), padding=6)
        sf.pack(fill='x', pady=(8, 0))
        grid = ttk.Frame(sf)
        grid.pack(fill='x')
        for col, (t, w) in enumerate(((T('№'), 3), (T('Подпись кнопки'), 14), (T('Скан'), 7),
                                      (T('Частота, МГц'), 12), (T('Режим'), 9), (T('Задержка на канале, с'), 18))):
            ttk.Label(grid, text=t, width=w).grid(row=0, column=col, sticky='w', padx=2)
        self.scan_vars = []
        for i, c in enumerate(self.core.s['scan_channels']):
            cv = dict(name=tk.StringVar(value=str(c.get('name', ''))), on=tk.BooleanVar(value=bool(c.get('on'))),
                      freq=tk.StringVar(value=str(c.get('freq', ''))), mode=tk.StringVar(value=c.get('mode') or 'USB'),
                      dwell=tk.StringVar(value='%g' % float(c.get('dwell') or A.SCAN_DWELL_DEFAULT)))
            self.scan_vars.append(cv)
            ttk.Label(grid, text=str(i + 1), width=3).grid(row=i + 1, column=0, sticky='w', padx=2)
            ttk.Entry(grid, textvariable=cv['name'], width=14).grid(row=i + 1, column=1, sticky='w', padx=2, pady=1)
            ttk.Checkbutton(grid, variable=cv['on']).grid(row=i + 1, column=2, sticky='w', padx=2)
            ttk.Entry(grid, textvariable=cv['freq'], width=12).grid(row=i + 1, column=3, sticky='w', padx=2)
            ttk.Combobox(grid, textvariable=cv['mode'], values=G.MODES, width=8, state='readonly').grid(
                row=i + 1, column=4, sticky='w', padx=2)
            ttk.Entry(grid, textvariable=cv['dwell'], width=6).grid(row=i + 1, column=5, sticky='w', padx=2)
        r = ttk.Frame(sf)
        r.pack(fill='x', pady=(6, 0))
        ttk.Label(r, text=T('Возобновить сканирование после тишины, с:')).pack(side='left', padx=4)
        ttk.Entry(r, textvariable=self.var['scan_resume'], width=6).pack(side='left')
        self.btn_scan = ttk.Button(r, text=T('Начать сканирование'), command=self.toggle_scan, width=24)
        self.btn_scan.pack(side='left', padx=12)
        ttk.Button(r, text=T('Подобрать преамбулу и точки'), command=self.pre_for_scan).pack(side='left', padx=4)
        ttk.Label(sf, text=T('Отметьте от 2 до 6 каналов. Программа перестраивает трансивер по кругу; если на канале '
                             'начинается приём (преамбула HFPager или точки Selcall) или идёт передача, сканирование '
                             'останавливается на этом канале и возобновляется после заданного времени тишины. '
                             'Сигнал обнаруживается через 0,3 с после перехода, поэтому хватает задержки 1 с на канал. '
                             'Худший случай — вызов начался сразу после ухода с канала: сканер вернётся через обход '
                             'остальных каналов, (N − 1) × (задержка + перестройка). Поэтому вызывающая станция должна '
                             'передавать точки Selcall не короче этого времени + 0,6 с, а преамбулу HFPager — + 2,3 с '
                             '(приёмнику нужно услышать ~2 с преамбулы). Время перестройки сканер измеряет сам. '
                             'Кнопка «Подобрать» считает длины по таблице. Кнопка «СКАН» есть и на главной странице.'),
                  foreground=dim, wraplength=880).pack(anchor='w', padx=4, pady=(4, 0))
        ttk.Label(sf, textvariable=self.var['scan_calc'], font=(A.MONO_FONT, 11)).pack(anchor='w', padx=4,
                                                                                    pady=(4, 0))

        ef = ttk.LabelFrame(f, text=T('Внешнее устройство (сирена, лампа, реле) — отдельный COM-порт'), padding=6)
        ef.pack(fill='x', pady=8)
        r = ttk.Frame(ef)
        r.pack(fill='x')
        ttk.Label(r, text=T('COM-порт:')).pack(side='left', padx=4)
        self.cb_ext = ttk.Combobox(r, textvariable=self.var['sel_ext_port'], width=14)
        self.cb_ext.pack(side='left')
        ttk.Label(r, text=T('линия:')).pack(side='left', padx=(8, 4))
        ttk.Combobox(r, textvariable=self.var['sel_ext_line'], values=SE.EXT_LINES, width=8,
                     state='readonly').pack(side='left')
        ttk.Checkbutton(r, text=T('инверсия'), variable=self.var['sel_ext_invert']).pack(side='left', padx=8)
        ttk.Label(r, text=T('время, с (1–60):')).pack(side='left', padx=(6, 2))
        ttk.Entry(r, textvariable=self.var['sel_ext_seconds'], width=4).pack(side='left')
        ttk.Button(r, text=T('Импульс'), command=self.test_ext).pack(side='left', padx=(10, 2))
        self.btn_ext = ttk.Button(r, text=T('Внешн.'), width=12, command=self.ext_toggle)
        self.btn_ext.pack(side='left', padx=2)
        ttk.Label(ef, text=T('Порт PTT и порт CAT для внешнего устройства не используются. Если на компьютере один '
                             'COM-порт и он нужен для PTT — выберите здесь «Выключено».'),
                  foreground=dim, wraplength=880).pack(anchor='w', padx=4, pady=(4, 0))

    # ------------------------------------------------------------------ tab: beacon & macros
    def build_beacon_tab(self):
        tk, ttk = self.tk, self.ttk
        f = self.add_tab('  ' + T('Маяк и макросы') + '  ')
        self.beacon_tab = self.tab_outer[-1]
        dim = self.colors()['dim']
        g = ttk.LabelFrame(f, text=T('Маяк'), padding=6)
        g.pack(fill='x')
        r = ttk.Frame(g)
        r.pack(fill='x')
        ttk.Checkbutton(r, text=T('Маяк включён'), variable=self.var['bcn_enable'], command=self.apply).pack(
            side='left', padx=4)
        ttk.Radiobutton(r, text=T('каждые, мин:'), variable=self.var['bcn_mode'], value='interval').pack(
            side='left', padx=(16, 2))
        ttk.Entry(r, textvariable=self.var['bcn_interval'], width=6).pack(side='left')
        ttk.Radiobutton(r, text=T('в заданное время UTC (ЧЧ:ММ через пробел):'), variable=self.var['bcn_mode'],
                        value='times').pack(side='left', padx=(16, 2))
        ttk.Entry(r, textvariable=self.var['bcn_times'], width=30).pack(side='left')
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(6, 0))
        ttk.Label(r, text=T('Что передавать:')).pack(side='left', padx=4)
        ttk.Combobox(r, textvariable=self.var['bcn_kind'], width=24, state='readonly',
                     values=[T(t) for k, t in self.KINDS if k != 'hfp_call']).pack(side='left')
        ttk.Label(r, text=T('кому (ID):')).pack(side='left', padx=(12, 4))
        ttk.Entry(r, textvariable=self.var['bcn_to'], width=8).pack(side='left')
        ttk.Label(r, text=T('CW: скорость, WPM:')).pack(side='left', padx=(12, 4))
        ttk.Entry(r, textvariable=self.var['bcn_cw_wpm'], width=4).pack(side='left')
        ttk.Label(r, text=T('тон, Гц:')).pack(side='left', padx=(8, 4))
        ttk.Entry(r, textvariable=self.var['bcn_cw_tone'], width=5).pack(side='left')
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(6, 0))
        ttk.Label(r, text=T('Текст маяка:')).pack(side='left', padx=4)
        ttk.Entry(r, textvariable=self.var['bcn_text'], width=60).pack(side='left', fill='x', expand=True)
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(6, 0))
        ttk.Button(r, text=T('Применить'), command=self.apply).pack(side='left', padx=4)
        ttk.Button(r, text=T('Передать маяк сейчас'), command=self.beacon_now).pack(side='left', padx=4)
        ttk.Label(r, textvariable=self.var['bcn_next'], foreground=dim).pack(side='left', padx=12)
        ttk.Label(g, text=T('Маяк не начинает передачу, пока идёт приём сигнала или своя передача — ждёт. '
                            '«HFPager: кадр маяк» — как маяк приложения HFPager (тип 0x06, всем). Пустой текст: '
                            '«Beacon from <мой ID>». Selcall: вызов или сообщение на ID «кому». CW — текст '
                            'телеграфом (латиница, цифры, русские буквы).'),
                  foreground=dim, wraplength=900).pack(anchor='w', padx=4, pady=(4, 0))

        g = ttk.LabelFrame(f, text=T('Макросы (кнопки под чатом)'), padding=6)
        g.pack(fill='both', expand=True, pady=8)
        hdr = ttk.Frame(g)
        hdr.pack(fill='x')
        for col, (t, w) in enumerate(((T('№'), 3), (T('Подпись кнопки'), 14), (T('Что'), 22), (T('Кому (пусто — из поля)'), 18),
                                      (T('Текст'), 40), (T('Сразу'), 6))):
            ttk.Label(hdr, text=t, width=w).grid(row=0, column=col, sticky='w', padx=2)
        self.macro_vars = []
        kinds = [T(t) for k, t in self.KINDS if k in A.MACRO_KINDS]
        for i, m in enumerate(self.core.s['macros']):
            mv = dict(label=tk.StringVar(value=m.get('label', '')), kind=tk.StringVar(value=self.kind_label(
                m.get('kind', 'hfp_msg'))), to=tk.StringVar(value=str(m.get('to', ''))),
                      text=tk.StringVar(value=m.get('text', '')), now=tk.BooleanVar(value=bool(m.get('now'))))
            self.macro_vars.append(mv)
            ttk.Label(hdr, text=str(i + 1), width=3).grid(row=i + 1, column=0, sticky='w', padx=2)
            ttk.Entry(hdr, textvariable=mv['label'], width=14).grid(row=i + 1, column=1, sticky='w', padx=2, pady=1)
            ttk.Combobox(hdr, textvariable=mv['kind'], values=kinds, width=22, state='readonly').grid(
                row=i + 1, column=2, sticky='w', padx=2)
            ttk.Entry(hdr, textvariable=mv['to'], width=18).grid(row=i + 1, column=3, sticky='w', padx=2)
            ttk.Entry(hdr, textvariable=mv['text'], width=40).grid(row=i + 1, column=4, sticky='we', padx=2)
            ttk.Checkbutton(hdr, variable=mv['now']).grid(row=i + 1, column=5, padx=2)
        hdr.columnconfigure(4, weight=1)
        r = ttk.Frame(g)
        r.pack(fill='x', pady=(6, 0))
        ttk.Button(r, text=T('Сохранить макросы'), command=self.save_macros).pack(side='left', padx=4)
        ttk.Label(r, text=T('Кнопка показывается, если у макроса есть подпись. «Сразу» — нажатие сразу передаёт; '
                            'без галочки — только заполняет поля под чатом.'), foreground=dim,
                  wraplength=700).pack(side='left', padx=8)

    def save_macros(self):
        out = []
        for mv in self.macro_vars:
            out.append(dict(label=mv['label'].get().strip(), kind=self.kind_key(mv['kind'].get()) or 'hfp_msg',
                            to=mv['to'].get().strip(), text=mv['text'].get().strip(), now=bool(mv['now'].get())))
        self.core.s['macros'] = out
        self.core.save()
        self.fill_macro_bar()

    def scan_from_vars(self):
        out = []
        for cv in getattr(self, 'scan_vars', []):
            try:
                d = max(1.0, min(120.0, float(cv['dwell'].get().replace(',', '.'))))
            except ValueError:
                d = A.SCAN_DWELL_DEFAULT
            out.append(dict(name=cv['name'].get().strip(), on=bool(cv['on'].get()), freq=cv['freq'].get().strip(),
                            mode=cv['mode'].get() or 'USB', dwell=d))
        return out

    def toggle_scan(self):
        if self.core.scan_on:
            self.core.stop_scan()
            self.update_scan_ui()
            return
        self.apply()
        err = self.core.start_scan()
        if err:
            self.mb.showwarning(T('Сканирование'), err)
        self.update_scan_ui()

    def refresh_channel_buttons(self):
        for i, b in enumerate(getattr(self, 'chan_btns', [])):
            t = A.channel_caption(self.core.s['scan_channels'][i], i)
            if b.cget('text') != t:
                b.configure(text=t)

    def on_channel(self, i):
        self.pull()
        err = self.core.tune_channel(i)
        if err:
            self.mb.showwarning(T('Канал'), err)
        self.update_scan_ui()

    def rename_channel(self, i):
        from tkinter import simpledialog
        ch = self.core.s['scan_channels'][i]
        new = simpledialog.askstring(T('Канал'), T('Подпись кнопки канала %d (%s %s):') % (
            i + 1, ch.get('freq', ''), ch.get('mode', '')), initialvalue=ch.get('name', ''), parent=self.root)
        if new is None:
            return 'break'
        ch['name'] = new.strip()
        if getattr(self, 'scan_vars', None):
            self.scan_vars[i]['name'].set(ch['name'])
        self.core.save()
        self.refresh_channel_buttons()
        return 'break'

    def toggle_hfp(self):
        self.core.set_hfp_decoder(bool(self.var['hfp_enable'].get()))
        self.core.save()
        self.add('[%s] • %s' % (self.now(), T('Декодер HFPager включён') if self.core.s['hfp_enable'] else
                                T('Декодер HFPager выключен')), 'sys')
        self.update_decoder_buttons()

    def toggle_sel(self):
        self.restart_rx()                       # pull() takes sel_enable from the same variable
        self.add('[%s] • %s' % (self.now(), T('Декодер Selcall включён') if self.core.s['sel_enable'] else
                                T('Декодер Selcall выключен')), 'sys')
        self.update_decoder_buttons()

    def update_decoder_buttons(self):
        try:
            self.tb_hfp.configure(text=('HFPager ' + (T('ВКЛ') if self.var['hfp_enable'].get() else T('ВЫКЛ'))))
            self.tb_sel.configure(text=('Selcall ' + (T('ВКЛ') if self.var['sel_enable'].get() else T('ВЫКЛ'))))
        except Exception:
            pass

    def update_scan_calc(self):
        c = self.core
        n = len(c.scan_list())
        if n < 2:
            self.var['scan_calc'].set(T('Отмечено каналов: %d (нужно от 2 до 6)') % n)
            return
        self.var['scan_calc'].set(
            T('Каналов %d, цикл %.1f с, перестройка %.2f с%s. Вызывающему нужно: преамбула HFPager ≥ %.1f с, '
              'точки Selcall ≥ %.1f с. Стандартных 6 с точек CODAN хватает на %d кан.') % (
                n, c.scan_cycle_seconds(), c.scan_retune_seconds(),
                '' if c.scan_retune is not None else T(' (оценка, измерится при сканировании)'),
                c.preamble_for_scan(), c.dots_for_scan(), c.max_channels_for(6.0, A.SEL_DOTS_MARGIN)))

    def update_scan_ui(self):
        c = self.core
        try:
            self.btn_scan.configure(text=T('Остановить сканирование') if c.scan_on else T('Начать сканирование'))
            if bool(self.var['scan_btn'].get()) != c.scan_on:
                self.var['scan_btn'].set(c.scan_on)
            ch_ = c.s['scan_channels'][c.scan_ch] if (c.scan_on and c.scan_ch is not None) else None
            want = c.cur_channel if c.cur_channel is not None else -1
            if self.var['chan_sel'].get() != want:
                self.var['chan_sel'].set(want)
            self.tb_scan.configure(text=(T('СКАН') + (' %d' % (c.scan_ch + 1) if ch_ else '') +
                                         (' ■' if c.scan_state == 'hold' else '')) if c.scan_on else T('СКАН'))
        except Exception:
            pass
        try:
            self.pull_scan_only()
            self.update_scan_calc()
        except Exception:
            pass
        if not c.scan_on or c.scan_ch is None:
            self.var['scan_info'].set('')
            return
        ch = c.s['scan_channels'][c.scan_ch]
        what = T('СТОП на канале') if c.scan_state == 'hold' else T('скан')
        self.var['scan_info'].set('%s %d «%s»: %s %s' % (what, c.scan_ch + 1, A.channel_caption(ch, c.scan_ch),
                                                         ch['freq'], ch.get('mode')))

    def update_pre_info(self):
        try:
            sp = self.var['speed'].get()
            std = A.standard_preamble_seconds(sp)
            want = float(str(self.var['hfp_pre_seconds'].get()).replace(',', '.') or 0)
            real = max(std, want) if want else std
            self.var['pre_info'].set(T('стандартная на %s Бод: %.1f с; будет %.1f с') % (sp, std, real))
        except Exception:
            self.var['pre_info'].set('')

    def pre_for_scan(self):
        """preamble (HFPager) and dots (Selcall) long enough for a station scanning the channels of the table"""
        self.pull()
        if len(self.core.scan_list()) < 2:
            self.mb.showinfo(T('Сканирование'), T('Отметьте в таблице сканирования хотя бы 2 канала.'))
            return
        v, d = self.core.preamble_for_scan(), self.core.dots_for_scan()
        self.var['hfp_pre_seconds'].set('%g' % v)
        self.var['sel_dot_seconds'].set('%g' % d)
        self.apply()
        self.add('[%s] • %s' % (self.now(), T('Сканирование %d каналов: преамбула HFPager %.1f с, точки Selcall '
                                              '%.1f с (обход остальных каналов + 2,3 с / + 0,6 с)') % (
            len(self.core.scan_list()), v, d)), 'sys')
        self.update_scan_calc()

    def pull_scan_only(self):
        if getattr(self, 'scan_vars', None):
            self.core.s['scan_channels'] = self.scan_from_vars()
        self.refresh_channel_buttons()

    def beacon_now(self):
        self.apply()
        err = self.core.send_beacon()
        if err:
            self.mb.showwarning(T('Маяк'), err)
        else:
            self.core.bcn_last = time.time()

    def update_beacon_info(self):
        nxt = self.core.bcn_next
        if not self.core.s.get('bcn_enable') or nxt is None:
            self.var['bcn_next'].set(T('маяк выключен') if not self.core.s.get('bcn_enable') else '')
            return
        left = max(0, int(nxt - time.time()))
        self.var['bcn_next'].set(T('следующий маяк через %d:%02d (в %s UTC)') % (
            left // 60, left % 60, datetime.datetime.utcfromtimestamp(nxt).strftime('%H:%M')))

    # ------------------------------------------------------------------ tab: program
    def build_program_tab(self):
        ttk = self.ttk
        f = self.add_tab('  ' + T('Программа') + '  ')
        g = ttk.LabelFrame(f, text=T('Вид'), padding=6)
        g.pack(fill='x')
        ttk.Label(g, text=T('Язык интерфейса:')).grid(row=0, column=0, sticky='e', padx=4, pady=3)
        cl = ttk.Combobox(g, textvariable=self.var['lang'], values=['Русский', 'English'], width=14,
                          state='readonly')
        cl.grid(row=0, column=1, sticky='w')
        cl.bind('<<ComboboxSelected>>', lambda e: self.set_lang('en' if self.var['lang'].get() == 'English'
                                                                else 'ru'))
        ttk.Label(g, text=T('Тема:')).grid(row=1, column=0, sticky='e', padx=4, pady=3)
        ct = ttk.Combobox(g, textvariable=self.var['theme'], values=[T('Светлая'), T('Тёмная')], width=14,
                          state='readonly')
        ct.grid(row=1, column=1, sticky='w')
        ct.bind('<<ComboboxSelected>>', lambda e: self.set_theme('dark' if self.var['theme'].get() == T('Тёмная')
                                                                 else 'light'))
        ttk.Label(g, text=T('Вторые часы (первые — UTC):')).grid(row=2, column=0, sticky='e', padx=4, pady=3)
        cz = ttk.Combobox(g, textvariable=self.var['clock_tz'], values=[tz_label(k) for k, _l, _h in TIME_ZONES],
                          width=22, state='readonly')
        cz.grid(row=2, column=1, sticky='w')

        def on_tz(*_):
            lbl = self.var['clock_tz'].get()
            for k, _l, _h in TIME_ZONES:
                if tz_label(k) == lbl:
                    self.core.s['clock_tz'] = k
            self.core.save()
            self.tick_clock()
        cz.bind('<<ComboboxSelected>>', on_tz)

        g = ttk.LabelFrame(f, text=T('Папки'), padding=6)
        g.pack(fill='x', pady=8)
        ttk.Label(g, text=T('Журнал и отложенные сообщения:')).grid(row=0, column=0, sticky='e', padx=4, pady=3)
        ttk.Entry(g, textvariable=self.var['log_dir'], width=60).grid(row=0, column=1, sticky='w')
        ttk.Button(g, text=T('Выбрать…'), command=self.choose_log_dir).grid(row=0, column=2, padx=4)
        ttk.Button(g, text=T('По умолчанию'), command=lambda: self.set_log_dir('')).grid(row=0, column=3, padx=4)
        ttk.Label(g, text=T('Настройки программы:')).grid(row=1, column=0, sticky='e', padx=4, pady=3)
        ttk.Label(g, text=A.SETTINGS_FILE, foreground=self.colors()['dim']).grid(row=1, column=1, columnspan=3,
                                                                              sticky='w')
        ttk.Label(g, text=T('Файл отложенных сообщений можно задать отдельно в окне «Отложенные сообщения».'),
                  foreground=self.colors()['dim']).grid(row=2, column=0, columnspan=4, sticky='w', padx=4)

        g = ttk.LabelFrame(f, text=T('О программе'), padding=6)
        g.pack(fill='x')
        ttk.Label(g, text='%s  v%s\n%s\n%s' % (
            A.APP_NAME, A.APP_VERSION, A.COPYRIGHT,
            T('HFPager-совместимый пейджер (PS-18) и HF Selcall CCIR 493-4 (совместимо с CODAN).'))).pack(
            anchor='w')
        b = ttk.Frame(g)
        b.pack(anchor='w', pady=4)
        ttk.Button(b, text=T('Инструкция (F1)'), command=self.open_help).pack(side='left')

    # ------------------------------------------------------------------ settings <-> widgets
    def pull(self):
        s, v = self.core.s, self.var

        def num(name, lo, hi, cast=float):
            try:
                s[name] = max(lo, min(hi, cast(str(v[name].get()).replace(',', '.'))))
            except (ValueError, KeyError):
                pass

        def port(name):
            p = v[name].get().split(' - ')[0].strip()
            return '' if p in (PORT_OFF, T(PORT_OFF)) else p
        try:
            s['my_id'] = int(v['my_id'].get())
        except ValueError:
            pass
        try:
            s['to_id'] = int(v['to_id'].get())
        except ValueError:
            pass
        s['in_dev'] = v['in_dev'].get()
        s['out_dev'] = v['out_dev'].get()
        s['speed'] = v['speed'].get()
        num('f0', 300, 2000)
        num('ptt_delay', 0.0, 5.0)
        num('sens_db', 1.0, 20.0)
        s['tx_level'] = float(v['tx_level'].get())
        for k in ('afc', 'ack', 'auto_ack', 'only_mine', 'ptt_invert', 'sel_enable', 'hfp_enable', 'sel_translit', 'sel_afc',
                  'sel_ring', 'sel_ring_air', 'sel_ext_enabled', 'sel_ext_invert', 'sel_listen_after_call',
                  'sel_listen_after_tx'):
            s[k] = bool(v[k].get())
        s['ptt_method'] = v['ptt_method'].get()
        s['ptt_port'] = port('ptt_port')
        num('ptt_baud', 300, 115200, int)
        s['icom_model'] = v['icom_model'].get()
        s['icom_addr'] = v['icom_addr'].get().strip() or '94'
        s['kenwood_variant'] = v['kenwood_variant'].get()
        chans = self.in_channels()
        s['in_channel'] = chans.index(v['in_channel'].get()) if v['in_channel'].get() in chans else 0
        # selcall
        s['sel_my_id'] = SE.digits(v['sel_my_id'].get()) or s['sel_my_id']
        s['sel_to_id'] = SE.digits(v['sel_to_id'].get())
        num('sel_dot_seconds', 0.5, 20.0)
        num('sel_center', 800.0, 2800.0)
        num('sel_ring_seconds', 3.0, 600.0)
        rev = {T(t): k for k, t in SE.RING_STYLES}
        s['sel_ring_style'] = rev.get(v['sel_ring_style'].get(), s.get('sel_ring_style', 'codan'))
        s['sel_answer_style'] = rev.get(v['sel_answer_style'].get(), s.get('sel_answer_style', 'kalinka'))
        rd = v['sel_ring_dev'].get()
        s['sel_ring_dev'] = '' if rd in (SYS_OUT, T(SYS_OUT)) else rd
        old = (s.get('sel_ext_port'), s.get('sel_ext_line'), s.get('sel_ext_invert'))
        s['sel_ext_port'] = port('sel_ext_port')
        s['sel_ext_line'] = v['sel_ext_line'].get() if v['sel_ext_line'].get() in SE.EXT_LINES else 'DTR'
        num('sel_ext_seconds', 1, 60)
        num('sel_listen_seconds', 5, 600)
        num('sel_listen_after_tx_seconds', 5, 600)
        if old != (s['sel_ext_port'], s['sel_ext_line'], s['sel_ext_invert']):
            self.core.ext.close(old[1] or 'RTS+DTR', bool(old[2]))
            self.core.ext_manual = False
        # HFPager call / ring / answer
        s['call_text'] = v['call_text'].get().strip() or 'CALL'
        for k in ('hfp_ring', 'hfp_msg_sound', 'hfp_ring_air', 'hfp_listen_after_call', 'hfp_ext_enabled',
                  'bcn_req_enable', 'bcn_enable'):
            s[k] = bool(v[k].get())
        num('hfp_ring_seconds', 3.0, 600.0)
        num('hfp_listen_seconds', 5, 600)
        for k in ('hfp_ring_style', 'hfp_msg_style', 'hfp_answer_style', 'bcn_req_style'):
            s[k] = rev.get(v[k].get(), s.get(k, 'kalinka'))
        s['bcn_req_text'] = v['bcn_req_text'].get().strip() or 'BCN REQ'
        # beacon
        s['bcn_mode'] = 'times' if v['bcn_mode'].get() == 'times' else 'interval'
        num('bcn_interval', 1, 1440)
        s['bcn_times'] = ' '.join(self.core.parse_times(v['bcn_times'].get()))
        s['bcn_kind'] = self.kind_key(v['bcn_kind'].get()) or s.get('bcn_kind', 'hfp_beacon')
        s['bcn_to'] = v['bcn_to'].get().strip() or '0'
        s['bcn_text'] = v['bcn_text'].get().strip()
        num('bcn_cw_wpm', 5, 60)
        num('bcn_cw_tone', 300, 2500)
        num('hfp_pre_seconds', 0.0, 120.0)
        num('scan_resume', 3.0, 3600.0)
        if getattr(self, 'scan_vars', None):
            s['scan_channels'] = self.scan_from_vars()
        # CAT
        s['rig_proto'] = v['rig_proto'].get()
        s['rig_port'] = port('rig_port')
        num('rig_baud', 300, 115200, int)
        try:
            s['tab'] = self.nb.index(self.nb.select())
        except Exception:
            pass
        if getattr(self, 'macro_vars', None):
            s['macros'] = [dict(label=mv['label'].get().strip(), kind=self.kind_key(mv['kind'].get()) or 'hfp_msg',
                                to=mv['to'].get().strip(), text=mv['text'].get().strip(), now=bool(mv['now'].get()))
                           for mv in self.macro_vars]

    def apply(self):
        self.pull()
        self.core.save()
        self.core.apply_live_settings()
        self.update_counter()
        self.sel_update_counter()

    def restart_rx(self):
        self.pull()
        self.core.save()
        self.core.start_rx()

    def refresh_devices(self):
        ins, outs = self.core.devices()
        self.cb_in['values'] = [l for _, l in ins]
        self.cb_out['values'] = [l for _, l in outs]
        self.cb_ring['values'] = [T(SYS_OUT)] + [l for _, l in outs]
        if not self.var['in_dev'].get() and ins:
            self.var['in_dev'].set(ins[0][1])
        if not self.var['out_dev'].get() and outs:
            self.var['out_dev'].set(outs[0][1])

    def refresh_ports(self):
        ports = P.list_ports()
        off = [T(PORT_OFF)]
        self.cb_pp['values'] = off + [lbl for _, lbl in ports]
        self.cb_rp['values'] = off + [lbl for _, lbl in ports]
        self.cb_ext['values'] = off + [dv for dv, _ in ports]

    def choose_log_dir(self):
        d = self.fd.askdirectory(initialdir=self.core.data_dir(), title=T('Папка журнала и отложенных сообщений'))
        if d:
            self.set_log_dir(d)

    def set_log_dir(self, d):
        self.core.s['log_dir'] = d
        self.core.save()
        self.var['log_dir'].set(self.core.data_dir())
        self.add('[%s] • %s' % (self.now(), T('Журнал: %s') % self.core.log_path()), 'sys')

    def open_log(self):
        e = self.core.open_log()
        if e:
            self.mb.showwarning(T('Журнал'), e)

    # ------------------------------------------------------------------ sending
    def on_send(self):
        self.pull()
        text = self.msg.get().strip()
        if self.msg.over_from() is not None:
            self.mb.showwarning(T('Отправка'), T('Текст длиннее 252 символов: лишнее выделено красным.'))
            return
        err = self.core.send(self.var['to_id'].get(), text)
        if err:
            self.mb.showwarning(T('Отправка'), err)
        else:
            self.msg.set('')
        self.update_counter()

    def on_call(self):
        self.pull()
        err = self.core.send_call(self.var['to_id'].get())
        if err:
            self.mb.showwarning(T('Вызов'), err)

    def update_counter(self):
        if not hasattr(self, 'msg'):
            return
        n = len(self.msg.get().encode('cp1251', 'replace'))
        try:
            t = A.Core.air_time(self.var['speed'].get(), max(min(n, 252), 1),
                                float(str(self.var['hfp_pre_seconds'].get()).replace(',', '.') or 0))
        except Exception:
            t = 0
        self.var['counter'].set(T('%d/252 байт · в эфире ≈ %.0f с · № %d') %
                                (n, t, int(self.core.s['counter']) & 0xFF))

    def sel_send(self, with_text):
        self.pull()
        text = self.sel_msg.get().strip() if with_text else None
        err = self.core.send_selcall(self.var['sel_to_id'].get(), text)
        if err:
            self.mb.showwarning('HF Selcall', err)
        elif with_text:
            self.sel_msg.set('')

    def sel_update_counter(self):
        if not hasattr(self, 'sel_msg'):
            return
        txt = self.sel_msg.get()
        tl = bool(self.var['sel_translit'].get())
        tr = SE.prepare_text(txt, tl) or ''
        try:
            dots = float(self.var['sel_dot_seconds'].get().replace(',', '.'))
        except ValueError:
            dots = 6.0
        me, to = self.var['sel_my_id'].get(), self.var['sel_to_id'].get()
        t_call = SE.air_time(dots, me, to, None)
        t_msg = SE.air_time(dots, me, to, txt or 'X', tl)
        over = len(SE.translit(txt) if tl else txt) > SE.MAX_MSG
        self.var['sel_counter'].set(T('%d/%d симв.%s%s · в эфире: вызов ≈ %.1f с, сообщение ≈ %.1f с') % (
            len(tr), SE.MAX_MSG, T(' (лишнее не будет передано)') if over else '',
            ('  → «%s»' % tr) if (tr and tr != txt.strip()) else '', t_call, t_msg))

    def set_tx_buttons(self, busy):
        st = ['disabled'] if busy else ['!disabled']
        for b in (self.btn, self.btn_call, self.sel_btn_call, self.sel_btn_msg):
            try:
                b.state(st)
            except Exception:
                pass

    # ------------------------------------------------------------------ incoming Selcall banner, ring, ext
    def show_banner(self, c, title, ring=True, proto='sel'):
        """incoming call / message to my ID: yellow bar; ring, external device, answer on air, listening by the
        settings of the protocol (prefix sel_ / hfp_)"""
        ttk, tk = self.ttk, self.tk
        self.banner_call = (c, title, proto)
        for w in self.banner_box.winfo_children():
            w.destroy()
        b = tk.Frame(self.banner_box, background='#ffd84d')
        b.pack(fill='x', padx=8, pady=(4, 0))
        txt = '☎  %s%s %s %s' % ('HFPager ' if proto == 'hfp' else 'Selcall ', T(title), T('от'), c['from'])
        if c['message']:
            txt += ':  ' + c['message']
        tk.Label(b, text=txt, background='#ffd84d', foreground='#000000',
                 font=('Helvetica', 14, 'bold')).pack(side='left', padx=10, pady=6)
        ttk.Button(b, text=T('Сбросить'), command=self.dismiss).pack(side='right', padx=6, pady=4)
        ttk.Button(b, text=T('Ответить'), command=self.answer).pack(side='right', padx=6, pady=4)
        if not ring:
            return
        try:
            self.root.deiconify()
            self.root.lift()
            if sys.platform.startswith('win'):
                import ctypes
                ctypes.windll.user32.FlashWindow(int(self.root.wm_frame(), 16), True)
        except Exception:
            pass
        core, p = self.core, proto + '_'
        if core.s.get(p + 'ring'):
            err = core.ring(prefix=p)
            if err:
                self.add('[%s] • %s %s' % (self.now(), T('Звонок:'), err), 'sys')
        if core.s.get(p + 'ext_enabled') and core.s.get('sel_ext_port'):
            core.ext_pulse()
        listen = core.s.get(p + 'listen_after_call', True)
        lsec = float(core.s.get(p + 'listen_seconds') or 60)
        if listen and not core.s.get(p + 'ring_air'):
            core.start_listen(lsec)
        if core.s.get(p + 'ring_air'):
            frm = c['from']
            label = 'HFPager' if proto == 'hfp' else 'SELCALL'

            def air():          # the calling station has time to switch to receive (HFPager: after an auto-ACK)
                core.listen_pending = lsec if listen else None
                err = core.send_answer(frm, style=core.ring_style(p, answer=True), label=label)
                if err:
                    core.listen_pending = None
                    self.q.put(('sys', err))
                    if listen:
                        core.start_listen(lsec)
            core.after_tx(air, delay=2.0 if proto == 'hfp' else 1.0)

    def dismiss(self):
        self.core.ringer.stop()
        self.banner_call = None
        for w in self.banner_box.winfo_children():
            w.destroy()

    def answer(self):
        if self.banner_call:
            if self.banner_call[2] == 'hfp':
                self.var['to_id'].set(self.banner_call[0]['from'])
                self.nb.select(0)
                self.msg.w.focus_set()
                self.dismiss()
                return
            self.var['sel_to_id'].set(self.banner_call[0]['from'])
            self.nb.select(0)
            self.sel_msg.w.focus_set()
        self.dismiss()

    def test_ring(self, prefix='sel_'):
        self.apply()
        if self.core.ringer.active:
            self.core.ringer.stop()
            return
        err = self.core.ringer.start(self.core.ring_dev(), self.core.ring_style(prefix),
                                     self.core.s['sel_ring_volume'], 3.0)
        if err:
            self.mb.showwarning(T('Звонок'), err)

    def preview(self, key):
        """play a melody / signal from the settings once, on the ring device (not on air)"""
        self.apply()
        err = self.core.play_once(self.core.s.get(key, 'kalinka'))
        if err:
            self.mb.showwarning(T('Звонок'), err)

    def test_answer(self):
        self.apply()
        err = self.core.ring(answer=True)
        if err:
            self.mb.showwarning(T('Сигнал ответа'), err)

    def test_ext(self):
        self.apply()
        if not self.core.s.get('sel_ext_port'):
            self.mb.showwarning(T('Внешнее устройство'), T('Укажите COM-порт внешнего устройства.'))
            return
        self.core.ext_pulse()

    def ext_toggle(self):
        self.apply()
        if not self.core.s.get('sel_ext_port'):
            self.mb.showwarning(T('Внешнее устройство'), T('Укажите COM-порт внешнего устройства.'))
            return
        self.core.ext_toggle()

    def update_sel_buttons(self):
        core = self.core
        if core.listener.active:
            self.btn_listen.configure(text=T('Слушаю ■') if core.listen_manual else T('Слушаю…'))
        else:
            self.btn_listen.configure(text=T('Слушать'))
        self.btn_ext.configure(text=T('Внешн. ВКЛ') if core.ext.on else T('Внешн.'))

    # ------------------------------------------------------------------ PTT / CAT actions
    def ptt_test(self):
        self.apply()
        if self.core.s['ptt_method'] == 'none':
            self.mb.showinfo('PTT', T('Метод PTT = none: управлять нечем.'))
            return
        if not self.mb.askokcancel(T('Тест PTT'), T('Трансивер включится на передачу примерно на 1 секунду '
                                                    '(звука не будет). Нагрузка подключена, диапазон свободен?')):
            return
        self.btn_ptt_test.state(['disabled'])
        threading.Thread(target=lambda: self.q.put(('ptt_test', self.core.ptt_test(1.0))), daemon=True).start()

    def rig_run(self, text):
        self.apply()
        threading.Thread(target=lambda: self.core.run_actions_logged(text, T('панель')), daemon=True).start()

    def rig_read(self):
        self.apply()

        def work():
            try:
                hz = self.core.rig.read_freq(self.core.rig_cfg())
                self.q.put(('rig_freq', T('%s МГц') % G.fmt_mhz(hz)))
            except G.RigError as ex:
                self.q.put(('rig_freq', T('ошибка: %s') % ex))
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------ scenarios window
    def open_rig_window(self):
        tk, ttk, core, mb = self.tk, self.ttk, self.core, self.mb
        w0 = self.rig_ui.get('win')
        if w0 is not None:
            try:
                w0.deiconify()
                w0.lift()
                return
            except Exception:
                self.rig_ui.clear()
        w = tk.Toplevel(self.root)
        w.title(T('Сценарии: действия при получении сообщения'))
        self.rig_ui['win'] = w
        rv = dict(enable=tk.BooleanVar(value=core.s['rig_scen_enable']), on=tk.BooleanVar(value=True),
                  trig=tk.StringVar(), frm=tk.StringVar(), act=tk.StringVar(), test=tk.StringVar(),
                  status=tk.StringVar(value=''), proto=tk.StringVar(value=T('оба')), sfrm=tk.StringVar())
        PROTOS = [('both', T('оба')), ('hfp', 'HFPager'), ('sel', 'Selcall')]
        p2l, l2p = dict(PROTOS), {l_: k_ for k_, l_ in PROTOS}
        self.rig_ui['status'] = rv['status']

        def sync():
            self.pull()
            core.s['rig_scen_enable'] = bool(rv['enable'].get())
            core.save()

        sf = ttk.Frame(w, padding=8)
        sf.pack(fill='both', expand=True)
        ttk.Checkbutton(sf, text=T('Выполнять сценарии при получении сообщений на мой ID (HFPager — мой ID, '
                                   'Selcall — мой Selcall ID, сообщение с текстом)'),
                        variable=rv['enable'], command=sync).pack(anchor='w', padx=4, pady=2)
        tv = ttk.Treeview(sf, columns=('n', 'on', 'proto', 'trigger', 'from', 'sfrom', 'action'), show='headings',
                          height=10)
        for c, t, wd in (('n', '№', 32), ('on', T('Вкл'), 40), ('proto', T('Протокол'), 80),
                         ('trigger', T('Текст сообщения (* = любое слово)'), 220),
                         ('from', T('От ID HFPager'), 110), ('sfrom', T('От Selcall ID'), 110),
                         ('action', T('Действие'), 300)):
            tv.heading(c, text=t)
            tv.column(c, width=wd, anchor='w')
        tv.pack(fill='both', expand=True, padx=4, pady=2)

        def fill(sel=None):
            for i in tv.get_children():
                tv.delete(i)
            for n, r in enumerate(core.s['scenarios']):
                tv.insert('', 'end', iid=str(n), values=(n + 1, '✔' if r.get('on', True) else '',
                                                         p2l.get(r.get('proto', 'both'), T('оба')),
                                                         r.get('trigger', ''), r.get('from', ''),
                                                         r.get('sel_from', ''), r.get('action', '')))
            if sel is not None and str(sel) in tv.get_children():
                tv.selection_set(str(sel))

        def selected():
            sel = tv.selection()
            return int(sel[0]) if sel else None

        def on_select(*_):
            n = selected()
            if n is None or n >= len(core.s['scenarios']):
                return
            r = core.s['scenarios'][n]
            rv['on'].set(bool(r.get('on', True)))
            rv['trig'].set(r.get('trigger', ''))
            rv['frm'].set(str(r.get('from', '')))
            rv['sfrm'].set(str(r.get('sel_from', '')))
            rv['proto'].set(p2l.get(r.get('proto', 'both'), T('оба')))
            rv['act'].set(r.get('action', ''))

        def form():
            return {'on': bool(rv['on'].get()), 'trigger': rv['trig'].get().strip().upper(),
                    'from': rv['frm'].get().strip(), 'sel_from': rv['sfrm'].get().strip(),
                    'proto': l2p.get(rv['proto'].get(), 'both'), 'action': rv['act'].get().strip()}

        def valid(row):
            if not row['trigger'] or not row['action']:
                mb.showwarning(T('Сценарий'), T('Заполните текст сообщения и действие.'), parent=w)
                return False
            return True

        def add_row():
            r = form()
            if valid(r):
                core.s['scenarios'].append(r)
                core.save()
                fill(len(core.s['scenarios']) - 1)

        def replace_row():
            n, r = selected(), form()
            if n is None:
                mb.showinfo(T('Сценарий'), T('Выберите строку таблицы.'), parent=w)
            elif valid(r):
                core.s['scenarios'][n] = r
                core.save()
                fill(n)

        def delete_row():
            n = selected()
            if n is not None:
                del core.s['scenarios'][n]
                core.save()
                fill()

        def move_row(d):
            n = selected()
            sc = core.s['scenarios']
            if n is None or not (0 <= n + d < len(sc)):
                return
            sc[n], sc[n + d] = sc[n + d], sc[n]
            core.save()
            fill(n + d)

        def defaults_rows():
            if mb.askokcancel(T('Сценарии'), T('Заменить таблицу стандартным набором сценариев?'), parent=w):
                core.s['scenarios'] = copy.deepcopy(G.DEFAULT_SCENARIOS)
                core.save()
                fill()

        tv.bind('<<TreeviewSelect>>', on_select)
        ef = ttk.Frame(sf)
        ef.pack(fill='x', pady=2)
        ttk.Checkbutton(ef, text=T('Вкл'), variable=rv['on']).pack(side='left', padx=4)
        ttk.Combobox(ef, textvariable=rv['proto'], values=[l_ for _k, l_ in PROTOS], width=8,
                     state='readonly').pack(side='left', padx=2)
        ttk.Label(ef, text=T('Сообщение:')).pack(side='left')
        ttk.Entry(ef, textvariable=rv['trig'], width=20).pack(side='left', padx=2)
        ttk.Label(ef, text=T('От ID:')).pack(side='left', padx=(6, 0))
        ttk.Entry(ef, textvariable=rv['frm'], width=8).pack(side='left', padx=2)
        ttk.Label(ef, text=T('От Selcall ID:')).pack(side='left', padx=(6, 0))
        ttk.Entry(ef, textvariable=rv['sfrm'], width=8).pack(side='left', padx=2)
        ttk.Label(ef, text=T('Действие:')).pack(side='left', padx=(6, 0))
        ttk.Entry(ef, textvariable=rv['act'], width=30).pack(side='left', padx=2)
        bf = ttk.Frame(sf)
        bf.pack(fill='x', pady=2)
        for t, c in ((T('Добавить'), add_row), (T('Заменить'), replace_row), (T('Удалить'), delete_row),
                     ('▲', lambda: move_row(-1)), ('▼', lambda: move_row(1)), (T('Стандартные'), defaults_rows)):
            ttk.Button(bf, text=t, command=c, width=11 if len(t) > 2 else 4).pack(side='left', padx=3)
        tf = ttk.Frame(sf)
        tf.pack(fill='x', pady=3)
        ttk.Label(tf, text=T('Проверка (имитация сообщения):')).pack(side='left', padx=4)
        ttk.Entry(tf, textvariable=rv['test'], width=28).pack(side='left')

        def test_msg():
            sync()
            text = rv['test'].get().strip()

            def work():
                res = core.run_scenario(text, None, manual=True)
                self.q.put(('rig_status', T('нет подходящего сценария') if res is None else T('выполнено: ') + res))
            threading.Thread(target=work, daemon=True).start()
        ttk.Button(tf, text=T('Выполнить'), command=test_msg).pack(side='left', padx=6)
        ttk.Label(tf, textvariable=rv['status'], foreground=self.colors()['dim']).pack(side='left', padx=4)
        ttk.Label(sf, text=T('Действия (через «;»): BND <м> · FRQ <МГц> [режим] · MODE <режим> · UP/DOWN <кГц> · '
                             'WAIT <с>.  Параметры из сообщения: {1}, {2}…  Режимы: ') + ' '.join(G.MODES) +
                  T('.  Передатчик сценарии не включают. Выполняется только первый подходящий сценарий '
                    '(порядок сверху вниз); для защиты укажите «От ID». Связь с трансивером — на вкладке '
                    '«Трансивер и аудио».'),
                  foreground=self.colors()['dim'], wraplength=820).pack(anchor='w', padx=4, pady=2)
        fill()

        def close():
            sync()
            self.rig_ui.clear()
            w.destroy()
        w.protocol('WM_DELETE_WINDOW', close)

    # ------------------------------------------------------------------ deferred messages window
    def open_outbox_window(self):
        tk, ttk, core, mb = self.tk, self.ttk, self.core, self.mb
        w0 = self.ob_ui.get('win')
        if w0 is not None:
            try:
                w0.deiconify()
                w0.lift()
                return
            except Exception:
                self.ob_ui.clear()
        w = tk.Toplevel(self.root)
        w.title(T('Отложенные сообщения'))
        self.ob_ui['win'] = w
        ov = dict(enable=tk.BooleanVar(value=core.s['outbox_enable']),
                  reply=tk.BooleanVar(value=core.s['outbox_reply_none']),
                  trig=tk.StringVar(value=core.s['outbox_trigger']),
                  tmo=tk.StringVar(value=str(core.s['outbox_ack_timeout'])),
                  file=tk.StringVar(value=core.outbox_path()),
                  to=tk.StringVar(value=''), text=tk.StringVar(value=''), info=tk.StringVar(value=''))
        default_path = os.path.join(core.data_dir(), 'outbox.txt')

        def sync():
            core.s['outbox_enable'] = bool(ov['enable'].get())
            core.s['outbox_reply_none'] = bool(ov['reply'].get())
            core.s['outbox_trigger'] = ov['trig'].get().strip() or 'QRU?'
            try:
                core.s['outbox_ack_timeout'] = max(10.0, min(600.0, float(ov['tmo'].get().replace(',', '.'))))
            except ValueError:
                pass
            path = ov['file'].get().strip()
            core.s['outbox_file'] = '' if path == default_path else path
            core.save()

        top2 = ttk.LabelFrame(w, text=T('Режим «QRU?»'), padding=6)
        top2.pack(fill='x', padx=8, pady=6)
        ttk.Checkbutton(top2, text=T('При получении запроса от ID отправлять ему его отложенные сообщения'),
                        variable=ov['enable'], command=sync).pack(anchor='w', padx=4)
        r1 = ttk.Frame(top2)
        r1.pack(fill='x', pady=2)
        ttk.Label(r1, text=T('Текст запроса:')).pack(side='left', padx=4)
        ttk.Entry(r1, textvariable=ov['trig'], width=10).pack(side='left')
        ttk.Label(r1, text=T('Ждать подтверждение, с:')).pack(side='left', padx=(12, 4))
        ttk.Entry(r1, textvariable=ov['tmo'], width=5).pack(side='left')
        ttk.Checkbutton(r1, text=T('Если для него ничего нет — отвечать «QRU»'), variable=ov['reply'],
                        command=sync).pack(side='left', padx=12)
        r2 = ttk.Frame(top2)
        r2.pack(fill='x', pady=2)
        ttk.Label(r2, text=T('TXT-файл:')).pack(side='left', padx=4)
        ttk.Entry(r2, textvariable=ov['file'], width=62).pack(side='left')

        def browse():
            p = self.fd.asksaveasfilename(parent=w, initialfile=os.path.basename(core.outbox_path()),
                                          initialdir=os.path.dirname(core.outbox_path()),
                                          defaultextension='.txt', filetypes=[('TXT', '*.txt')])
            if p:
                ov['file'].set(p)
                reload_file()
        ttk.Button(r2, text=T('Выбрать…'), command=browse).pack(side='left', padx=4)

        tv = ttk.Treeview(w, columns=('n', 'to', 'text'), show='headings', height=10)
        for c, t, wd in (('n', '№', 36), ('to', T('Кому (ID)'), 90), ('text', T('Текст сообщения'), 620)):
            tv.heading(c, text=t)
            tv.column(c, width=wd, anchor='w')
        tv.pack(fill='both', expand=True, padx=8, pady=4)

        def fill(sel=None):
            for i in tv.get_children():
                tv.delete(i)
            for n, it in enumerate(core.outbox):
                tv.insert('', 'end', iid=str(n), values=(n + 1, it['to'], it['text']))
            if sel is not None and str(sel) in tv.get_children():
                tv.selection_set(str(sel))
            ov['info'].set(T('Сообщений в очереди: %d') % len(core.outbox))

        def selected():
            sel = tv.selection()
            return int(sel[0]) if sel else None

        def on_select(*_):
            n = selected()
            if n is not None and n < len(core.outbox):
                ov['to'].set(str(core.outbox[n]['to']))
                ov['text'].set(core.outbox[n]['text'])

        def read_form():
            to, text = ov['to'].get().strip(), ov['text'].get().strip()
            if not (to.isdigit() and 0 <= int(to) <= 65535):
                mb.showwarning(T('Отложенные'), T('ID получателя: число 0…65535.'), parent=w)
                return None
            n = len(text.encode('cp1251', 'replace'))
            if not (1 <= n <= 252):
                mb.showwarning(T('Отложенные'), T('Длина текста: 1…252 байта (сейчас %d).') % n, parent=w)
                return None
            return dict(to=int(to), text=text.replace('\n', ' '))

        def save_back():
            err = core.outbox_save()
            if err:
                mb.showwarning(T('Отложенные'), err, parent=w)

        def add_item():
            it = read_form()
            if it:
                core.outbox_load()
                core.outbox.append(it)
                save_back()
                fill(len(core.outbox) - 1)

        def replace_item():
            n, it = selected(), read_form()
            if n is None:
                mb.showinfo(T('Отложенные'), T('Выберите строку.'), parent=w)
            elif it:
                core.outbox[n] = it
                save_back()
                fill(n)

        def delete_item():
            n = selected()
            if n is not None:
                del core.outbox[n]
                save_back()
                fill()

        def send_now():
            n = selected()
            if n is None:
                mb.showinfo(T('Отложенные'), T('Выберите строку.'), parent=w)
                return
            it = dict(core.outbox[n])
            threading.Thread(target=lambda: core.outbox_send([it], first_delay=0.0), daemon=True).start()

        def reload_file():
            sync()
            err = core.outbox_load()
            fill()
            if err:
                mb.showwarning(T('Отложенные'), err, parent=w)

        def open_file():
            sync()
            if not os.path.exists(core.outbox_path()):
                save_back()
            try:
                if sys.platform.startswith('win'):
                    os.startfile(core.outbox_path())
                else:
                    import subprocess
                    subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', core.outbox_path()])
            except Exception as ex:
                mb.showwarning(T('Отложенные'), T('Не удалось открыть файл: %s') % ex, parent=w)

        tv.bind('<<TreeviewSelect>>', on_select)
        ef = ttk.Frame(w)
        ef.pack(fill='x', padx=8, pady=2)
        ttk.Label(ef, text=T('Кому (ID):')).pack(side='left')
        ttk.Entry(ef, textvariable=ov['to'], width=8).pack(side='left', padx=3)
        ttk.Label(ef, text=T('Текст:')).pack(side='left', padx=(8, 0))
        ttk.Entry(ef, textvariable=ov['text'], width=60).pack(side='left', padx=3)
        bf = ttk.Frame(w)
        bf.pack(fill='x', padx=8, pady=2)
        for t, c in ((T('Добавить'), add_item), (T('Заменить'), replace_item), (T('Удалить'), delete_item),
                     (T('Отправить сейчас'), send_now), (T('Перечитать файл'), reload_file),
                     (T('Открыть TXT'), open_file)):
            ttk.Button(bf, text=t, command=c).pack(side='left', padx=3)
        ttk.Label(w, textvariable=ov['info'], foreground=self.colors()['dim']).pack(anchor='w', padx=10)
        ttk.Label(w, text=T('Формат файла (UTF-8): одна строка = одно сообщение,  ID|текст.  Сообщение удаляется из '
                            'очереди только после подтверждения доставки. Строки с # игнорируются. Файл перечитывается '
                            'при изменении; отправленные строки переносятся в outbox_sent.txt.'),
                  foreground=self.colors()['dim'], wraplength=780).pack(anchor='w', padx=10, pady=(0, 6))
        core.outbox_load()
        fill()
        self.ob_ui['fill'] = fill

        def watch():
            if self.ob_ui.get('win') is not w:
                return
            try:
                if core.outbox_changed_on_disk():
                    core.outbox_load()
                    fill()
                self.root.after(3000, watch)
            except Exception:
                pass
        self.root.after(3000, watch)

        def close():
            sync()
            self.ob_ui.clear()
            w.destroy()
        w.protocol('WM_DELETE_WINDOW', close)

    # ------------------------------------------------------------------ help / about
    def open_help(self):
        import help_text
        tk, ttk = self.tk, self.ttk
        w = tk.Toplevel(self.root)
        w.title(T('Инструкция') + ' — ' + A.APP_NAME)
        w.geometry('860x640')
        t = tk.Text(w, wrap='word', padx=12, pady=10, font=('Helvetica', 12))
        if self.dark:
            t.configure(background=DARK['field'], foreground=DARK['fg'])
        sb = ttk.Scrollbar(w, command=t.yview)
        t.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        t.pack(fill='both', expand=True)
        t.tag_configure('h1', font=('Helvetica', 17, 'bold'), spacing1=6, spacing3=6)
        t.tag_configure('h2', font=('Helvetica', 14, 'bold'), spacing1=10, spacing3=4)
        for line in help_text.get(i18n.LANG).splitlines():
            if line.startswith('## '):
                t.insert('end', line[3:] + '\n', 'h2')
            elif line.startswith('# '):
                t.insert('end', line[2:] + '\n', 'h1')
            else:
                t.insert('end', line + '\n')
        t.insert('end', '\n%s  v%s\n' % (A.COPYRIGHT, A.APP_VERSION))
        t.configure(state='disabled')

    def about(self):
        self.mb.showinfo(T('О программе'), '%s  v%s\n\n%s\n\n%s\n%s' % (
            A.APP_NAME, A.APP_VERSION,
            T('HFPager-совместимый пейджер (PS-18) и HF Selcall CCIR 493-4 (совместимо с CODAN).'),
            A.COPYRIGHT, T('Настройки: %s') % A.SETTINGS_FILE))

    # ------------------------------------------------------------------ events from the Core
    def handle(self, item):
        kind = item[0]
        core = self.core
        add, now = self.add, self.now
        if kind == 'sys':
            add('[%s] • %s' % (now(), item[1]), 'sys')
        elif kind == 'rx':
            fr, info, dup = item[1], item[2], item[3]
            mine = int(core.s['my_id'])
            text = fr['text'].decode('cp1251', 'replace')
            hide = bool(core.s.get('only_mine')) and (fr['b0'] == 0x06 or fr['dest'] != mine)
            if hide:
                pass
            elif fr['b0'] == 0x06:
                add('[%s] ★ %s %d: %s  (%s %s)' % (now(), T('Маяк от'), fr['sender'], text, fr['speed'], T('Бод')),
                    'beacon')
            else:
                tome = fr['dest'] == mine
                tag = ('dup' if tome else 'dup_o') if dup else ('tome' if tome else 'rx')
                add(T('[%s] %d → %d  №%d  (%s Бод, АПЧ %.0f Гц): %s%s') % (
                    now(), fr['sender'], fr['dest'], fr['counter'], fr['speed'], info.get('afc_hz', 0.0), text,
                    T('   (повтор)') if dup else ''), tag)
                if (fr['b1'] & 0x02) and fr['dest'] == mine and not dup:
                    add('      ' + (T('запрошено подтверждение доставки – отправляю') if core.s.get('auto_ack') else
                                    T('запрошено подтверждение доставки (автоподтверждение выключено)')), 'sys')
            self.var['info'].set(T('Последний кадр: центр %.0f Гц, диапазон АПЧ %.1f Гц') %
                                 (info.get('center_hz', 0), info.get('afc_hz', 0)))
            self.rx_state['flash_until'] = time.time() + 1.5
        elif kind == 'ack':
            fr, hit = item[1], item[3]
            who = T('ПОДТВЕРЖДЕНИЕ') if fr['kind'] == 'ack' else T('ОТКАЗ')
            if core.s.get('only_mine') and not hit and fr['dest'] != int(core.s['my_id']):
                pass
            elif hit:
                add(T('[%s] ✔ %s: сообщение №%d для %d доставлено («%s»)') % (
                    now(), who, fr['orig_counter'], hit[0], hit[1]), 'note')
            else:
                add(T('[%s] ✔ %s для ID %d (исходное сообщение №%d, CRC %04X)') % (
                    now(), who, fr['dest'], fr['orig_counter'], fr['orig_crc']), 'note')
        elif kind == 'outbox_changed':
            if self.ob_ui.get('fill') is not None:
                core.outbox_load()
                self.ob_ui['fill']()
        elif kind == 'rig_freq':
            self.var['rig_cur'].set(item[1])
        elif kind == 'rig_status':
            if self.rig_ui.get('status') is not None:
                self.rig_ui['status'].set(item[1])
        elif kind == 'ptt_test':
            self.btn_ptt_test.state(['!disabled'])
            add('[%s] • %s %s' % (now(), T('Тест PTT:'), item[1] or T('выполнен (включено и выключено)')), 'sys')
        elif kind == 'tx_ack':
            to, cnt, speed, secs = item[1:5]
            add(T('[%s] ✔ → %d  подтверждение сообщения №%d  (%s Бод, ≈ %.0f с)') % (now(), to, cnt, speed, secs),
                'mine')
            self.var['status'].set(T('Передача…'))
            self.set_tx_buttons(True)
        elif kind == 'sel_rx':
            c, when, mine, own = item[1:5]
            if core.s.get('only_mine') and not mine:
                return
            title = 'Подтверждение' if c['eos'] == 'ACK-BQ' else ('Сообщение' if c['message'] else 'Вызов')
            stamp = datetime.datetime.fromtimestamp(when).strftime('%H:%M:%S')
            line = '[%s] SELCALL %s %s → %s%s' % (stamp, T(title).upper(), c['from'], c['to'],
                                                  (': ' + c['message']) if c['message'] else '')
            line += '   (%.0f %s%s%s)' % (c['center_hz'], T('Гц'), ', LSB' if c['polarity'] == 'inverted' else '',
                                          '' if c['ecc_ok'] else ', ' + T('СОМНИТЕЛЬНО'))
            if own:
                add(line + '  ' + T('[своя передача]'), 'dup_o')
            else:
                add(line, ('tome' if mine else 'rx') if c['ecc_ok'] else 'dup_o')
            self.rx_state['flash_until'] = time.time() + 1.5
            if mine and not own and c['ecc_ok'] and c['eos'] != 'ACK-BQ':
                self.show_banner(c, title)
        elif kind == 'sel_event':
            ev, info = item[1], item[2]
            if ev == 'centers':
                self.var['sel_centers'].set((T('Selcall АПЧ: ') + ', '.join('%.0f' % f_ for f_ in info[:3]) + ' ' +
                                             T('Гц')) if (info and core.s.get('sel_afc')) else '')
            elif ev == 'error':
                add('[%s] • %s' % (now(), info['text']), 'sys')
        elif kind == 'sel_answer_start':
            to, secs = item[1], item[2]
            label = item[3] if len(item) > 3 else 'SELCALL'
            add(T('[%s] %s ОТВЕТ В ЭФИР → %s   (≈ %.1f с)') % (now(), label, to, secs), 'mine')
            self.var['status'].set(T('Ответ в эфир…'))
            self.set_tx_buttons(True)
        elif kind == 'hfp_call':
            fr = item[1]
            self.show_banner({'from': str(fr['sender']), 'message': ''}, 'Вызов', proto='hfp')
        elif kind == 'hfp_msg_to_me':
            fr = item[1]
            if core.s.get('hfp_msg_sound'):
                err = core.play_once(core.s.get('hfp_msg_style', 'beep'))
                if err:
                    add('[%s] • %s %s' % (now(), T('Звонок:'), err), 'sys')
        elif kind == 'cw_start':
            add(T('[%s] CW: %s   (передача ≈ %.0f с)') % (now(), item[1], item[2]), 'mine')
            self.var['status'].set(T('Передача CW…'))
            self.set_tx_buttons(True)
        elif kind == 'scan_state':
            self.update_scan_ui()
        elif kind in ('listen_state', 'ext_state'):
            self.update_sel_buttons()
        elif kind == 'rx_restart':
            if core.stream is not None and not core.tx_busy:
                ok_ = core.start_rx()
                add('[%s] • %s' % (now(), (T('Вход не отдаёт звук %.0f с — приём перезапущен') if ok_ else
                                           T('Вход не отдаёт звук %.0f с — перезапустить приём не удалось')) % item[1]),
                    'sys')
        elif kind == 'sel_tx_start':
            me, to, text, secs = item[1:5]
            add(T('[%s] SELCALL %s %s → %s%s   (передача ≈ %.0f с)') % (
                now(), T('СООБЩЕНИЕ') if text else T('ВЫЗОВ'), me, to, (': ' + text) if text else '', secs), 'mine')
            self.var['status'].set(T('Передача Selcall…'))
            self.set_tx_buttons(True)
        elif kind == 'tx_start':
            my, to, cnt, text, speed, secs = item[1:7]
            add(T('[%s] %d → %d  №%d  (%s Бод, передача ≈ %.0f с): %s') % (now(), my, to, cnt, speed, secs, text),
                'mine')
            self.var['status'].set(T('Передача…'))
            self.set_tx_buttons(True)
        elif kind == 'tx_done':
            self.set_tx_buttons(False)
            self.var['status'].set(T('Ожидание'))
            self.update_counter()
            if item[1]:
                add('[%s] • %s %s' % (now(), T('Ошибка передачи:'), item[1]), 'sys')
        elif kind == 'event':
            ev, info = item[1], item[2]
            if ev == 'spectrum':
                self.on_spectrum(info['db'])
            elif ev == 'state' and not core.tx_busy:
                self.rx_state['state'] = info['state']
                self.var['status'].set({'idle': T('Ожидание'), 'receiving': T('Приём сигнала…'),
                                        'decoding': T('Декодирование…')}.get(info['state'], ''))
            elif ev == 'fail':
                # a Selcall (FSK) signal also wakes the HFPager detector: do not report it as a failed frame
                def report(info=info, t_fail=time.time()):
                    if core.last_sel_rx < t_fail - info['seconds'] - 3:
                        add('[%s] • %s' % (now(), T('Принят сигнал (%.0f с), но кадр HFPager не удалось декодировать '
                                                    '(слишком слабый или искажён)') % info['seconds']), 'sys')
                self.root.after(3500, report)
            elif ev == 'error':
                add('[%s] • %s %s' % (now(), T('Внутренняя ошибка:'), info['text']), 'sys')

    def poll(self):
        try:
            while True:
                try:
                    self.handle(self.q.get_nowait())
                except queue.Empty:
                    raise
                except Exception as ex:             # a failing handler must never stop the UI loop
                    import traceback
                    self.core.log('%s  UI ERROR: %s' % (self.core._stamp(),
                                                        traceback.format_exc().replace('\n', ' | ')))
                    try:
                        self.add('[%s] • %s %s' % (self.now(), T('Ошибка интерфейса:'), ex), 'sys')
                    except Exception:
                        pass
        except queue.Empty:
            pass
        try:
            self.update_lamps()
            self.update_meter()
            t = time.time()
            if int(t) != getattr(self, '_last_sec', None):
                self._last_sec = int(t)
                self.tick_clock()
                self.update_beacon_info()
                self.pull_scan_only()
                self.update_scan_calc()
        except Exception:
            pass
        self.root.after(100, self.poll)

    def on_close(self):
        core = self.core
        try:
            self.pull()
            try:
                core.s['geometry'] = self.root.geometry()
            except Exception:
                pass
            core.save()
            if core.scan_on:                     # stop and give the transceiver its frequency back first
                core.stop_scan()
                th = core._scan_thread
                if th is not None:
                    th.join(5.0)
            core.stop_rx()
            core.ringer.stop()
            core.listener.stop()
            core.ext_reset()
            core.ptt.close()
            core.rig.close()
        finally:
            self.root.destroy()

    def start(self):
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        if A.sd is None:
            self.add('• %s %s' % (T('Библиотека sounddevice/PortAudio недоступна:'), A.SD_ERROR), 'sys')
            self.add('• ' + T('Установите: pip install sounddevice numpy'), 'sys')
        else:
            self.add('• ' + T('Передача и приём идут через выбранные звуковые устройства.'), 'sys')
            self.restart_rx()
        self.poll()


def _here():
    return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))


def run():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    import tkinter.font as tkfont
    root = tk.Tk()
    for fname in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont'):
        try:
            tkfont.nametofont(fname).configure(size=13 if sys.platform == 'darwin' else 11)
        except Exception:
            pass
    app = App(root, tk, ttk, messagebox, filedialog, tkfont)
    geo = app.core.s.get('geometry') or ''
    try:
        sh = int(root.winfo_screenheight())
        sw = int(root.winfo_screenwidth())
        root.geometry(geo if geo else '%dx%d' % (max(800, min(1160, sw - 40)), max(560, min(820, sh - 90))))
        root.minsize(640, 420)
    except Exception:
        pass
    app.start()
    root.mainloop()
