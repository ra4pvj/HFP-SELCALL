"""
Window smoke test without a display: a stand-in tkinter (tests/tkstub) lets the whole GUI be built and
driven — tabs, events from the Core, sending, Selcall banner, language and theme switching, help.
A failing event handler is caught by App.poll() and written to the journal as 'UI ERROR', so the test
fails on any such line.

    python tests/test_gui.py
"""
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tkstub'))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import tkinter                      # noqa: E402  (the stub)
from tkinter import ttk, messagebox, filedialog   # noqa: E402
import tkinter.font as tkfont       # noqa: E402
import test_combined as TC          # noqa: E402
import hfp_selcall_app as A         # noqa: E402
import hfp_selcall_gui as GUI       # noqa: E402
import i18n                         # noqa: E402


def run_afters(name):
    for f, a in list(tkinter.AFTERS):
        if getattr(f, '__name__', '') == name:
            tkinter.AFTERS.remove((f, a))
            f(*a)


def main():
    tmp = tempfile.mkdtemp()
    A.SETTINGS_FILE = os.path.join(tmp, 'settings.json')
    A.LOG_FILE = os.path.join(tmp, 'messages.txt')
    A.sd = TC.FakeSD
    orig = A.Core.__init__

    def init(self, q, sd_module=None):
        orig(self, q, sd_module=TC.FakeSD)
    A.Core.__init__ = init

    root = tkinter.Tk()
    app = GUI.App(root, tkinter, ttk, messagebox, filedialog, tkfont)
    core = app.core
    core.s.update(sel_ring_air=True)
    app.start()
    assert core.stream is not None, 'reception not started'

    # message field limit: 260 characters -> the excess from #252 is marked
    app.msg.set('Ж' * 260)
    assert app.msg.over_from() == 252
    app.on_send()
    assert messagebox.SHOWN and not core.tx_busy, 'an over-long message must not be sent'
    app.msg.set('HFP TEST')
    app.var['to_id'].set('3')
    app.on_send()
    core._tx_thread.join(60)
    app.sel_msg.set('Привет')
    assert app.sel_msg.over_from() is None
    app.sel_msg.set('Щ' * 30)                  # translit: Щ -> SCH, 3 per char -> over from char 21
    assert app.sel_msg.over_from() == 21, app.sel_msg.over_from()
    app.sel_msg.set('TEST')
    app.var['sel_to_id'].set('4321')
    app.sel_send(True)
    core._tx_thread.join(10)

    # events from the receivers
    c = {'to': core.s['sel_my_id'], 'from': '5678', 'message': 'HI', 'eos': 'EOS', 'ecc_ok': True,
         'center_hz': 1785.0, 'polarity': 'normal', 'time': 1.0}
    core._on_sel_call(c, time.time())
    core._on_sel_event('centers', [1785.0])
    core.q.put(('event', 'fail', {'seconds': 5.0}))
    core.q.put(('event', 'spectrum', {'db': [-80.0] * 270}))
    core.q.put(('event', 'state', {'state': 'receiving'}))
    fr = dict(kind='msg', b0=0x05, b1=0xA2, dest=int(core.s['my_id']), sender=3, counter=7, text=b'QRU?',
              speed='5.86', length=4, hdr_crc=0)
    core.q.put(('rx', fr, {'afc_hz': 1.0, 'center_hz': 1700}, False))
    core.q.put(('rx', dict(fr, b0=0x06, text=b'Beacon from RA4PVJ'), {}, False))
    core.q.put(('rx_restart', 5.0))
    core.q.put(('listen_state',))
    app.poll()
    run_afters('report')
    run_afters('air')                           # answer on air after the call
    if core._tx_thread:
        core._tx_thread.join(10)
    app.poll()
    assert app.banner_call is not None, 'Selcall banner not shown'
    app.answer()
    assert app.var['sel_to_id'].get() == '5678' and app.banner_call is None

    # stage 2: HFPager call -> banner (HFPager), answer on air after the auto-ACK pause; macros; beacon tab
    t0 = time.time()                                       # the Selcall answer from above: started and finished
    while time.time() - t0 < 20 and (core.tx_busy or not any('SELCALL' in t and '5678' in t and '≈' in t
                                                               for t, _g in app.chat_lines)):
        time.sleep(0.1)
        app.poll()
    time.sleep(0.6)
    app.poll()
    core.q.put(('hfp_call', dict(fr, text=b'CALL', counter=9)))
    core.q.put(('hfp_msg_to_me', dict(fr, counter=10)))
    app.poll()
    assert app.banner_call is not None and app.banner_call[2] == 'hfp', app.banner_call
    t0 = time.time()
    while time.time() - t0 < 10 and not any('HFPager' in t and '→ 3' in t for t, _g in app.chat_lines):
        time.sleep(0.1)
        app.poll()
    if core._tx_thread:
        core._tx_thread.join(10)
    app.poll()
    assert any('HFPager' in t and '→ 3' in t for t, _tag in app.chat_lines), 'no HFPager answer on air'
    app.answer()
    assert app.var['to_id'].get() == '3'
    app.macro_vars[0]['label'].set('M1')
    app.macro_vars[0]['text'].set('MACRO TEXT')
    app.macro_vars[0]['now'].set(False)
    app.save_macros()
    app.run_macro(0)
    assert app.msg.get() == 'MACRO TEXT', app.msg.get()
    app.var['bcn_kind'].set(app.kind_label('cw'))
    app.var['bcn_text'].set('RA4PVJ BCN')
    app.var['bcn_enable'].set(True)
    app.apply()
    assert core.s['bcn_kind'] == 'cw' and core.s['bcn_enable']
    app.beacon_now()
    core._tx_thread.join(20)
    app.update_beacon_info()
    core.s['bcn_enable'] = False
    app.on_call()
    core._tx_thread.join(60)
    app.poll()

    # stage 3: preamble for scanning, scan button with a fake CAT
    core.rig.run_actions = lambda cfg, act: [(act, True, 'ok')]
    app.var['rig_port'].set('COM9')
    app.pre_for_scan()
    assert core.s['hfp_pre_seconds'] == core.preamble_for_scan() > 0
    assert core.s['sel_dot_seconds'] == core.dots_for_scan() >= 6.0
    app.toggle_scan()
    time.sleep(0.5)
    assert core.scan_on
    app.poll()
    assert app.var['scan_info'].get(), 'scan status not shown'
    app.toggle_scan()
    time.sleep(3.5)
    app.poll()
    assert not core.scan_on and app.var['scan_info'].get() == ''
    core.s['hfp_pre_seconds'] = 0.0
    app.var['hfp_pre_seconds'].set('0')

    # level meter / clocks
    core.peak_max = 0.5
    app.update_meter()
    core.clip_time = time.time()
    core.peak_max = 0.99
    app.update_meter()
    assert app.var['clip'].get(), 'overload not indicated'
    app.tick_clock()

    # ports: «Выключено» is stored as no port
    app.var['ptt_port'].set(GUI.T(GUI.PORT_OFF))
    app.var['sel_ext_port'].set(GUI.T(GUI.PORT_OFF))
    app.apply()
    assert core.s['ptt_port'] == '' and core.s['sel_ext_port'] == ''

    # windows
    app.open_rig_window()
    app.open_outbox_window()
    app.open_help()
    app.about()

    # language and theme: the window is rebuilt, the chat survives
    n_lines = len(app.chat_lines)
    app.set_lang('en')
    assert i18n.LANG == 'en' and core.s['lang'] == 'en'
    app.set_theme('dark')
    assert len(app.chat_lines) == n_lines
    core.q.put(('sys', 'after rebuild'))
    core._on_sel_call(dict(c, message=''), time.time())
    app.poll()
    app.open_help()
    app.set_lang('ru')
    app.set_theme('light')
    app.on_close()

    log = open(A.LOG_FILE, encoding='utf-8').read()
    assert 'UI ERROR' not in log, log[log.find('UI ERROR') - 200:][:3000]
    print('OK  GUI: built, events handled, limits marked, Selcall and HFPager call banners/answers, macros, '
          'beacon (CW), preamble for scanning, scan start/stop, meter/overload, «Выключено» ports, scenarios, help, RU/EN and light/dark rebuild — '
          'no UI errors')


if __name__ == '__main__':
    main()
