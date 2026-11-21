#!/usr/bin/env python3
"""
HFP+SELCALL: HFPager-compatible messenger (PS-18) and CODAN-compatible HF Selcall (CCIR 493-4)
in one program.  Windows / macOS / Linux.

Both receivers listen to the same sound-card input at the same time; both transmitters use the same
output and the same PTT / CAT control.  Based on ra4pvj/HFP (hfpager_app.py) and ra4pvj/SELCALL.

Requires: Python 3.8+, numpy, sounddevice, pyserial (tkinter is part of Python).

    pip install -r requirements.txt
    python hfp_selcall_app.py
"""
import os
import sys
import json
import time
import queue
import threading
import datetime

import numpy as np

import hfpager_modem as M
import hfpager_rx as R
import hfpager_ptt as P
import hfpager_rig as G
import selcall_engine as SE
import cw as CW
from i18n import T
import copy

try:
    import sounddevice as sd
    SD_ERROR = None
except Exception as _ex:           # PortAudio missing etc.
    sd = None
    SD_ERROR = _ex

def _app_dir():
    if sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'HFPSelcallApp')
    if sys.platform.startswith('win'):
        return os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'HFPSelcallApp')
    return os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config')),
                        'HFPSelcallApp')


APP_VERSION = '0.3.0-beta4'
APP_NAME = 'HFP+SELCALL'
COPYRIGHT = '© 2026 RA4PVJ'
APP_DIR = _app_dir()
MONO_FONT = 'Menlo' if sys.platform == 'darwin' else ('Consolas' if sys.platform.startswith('win') else 'DejaVu Sans Mono')
SETTINGS_FILE = os.path.join(APP_DIR, 'settings.json')
def _log_dir():
    docs = os.path.join(os.path.expanduser('~'), 'Documents')
    return os.path.join(docs if os.path.isdir(docs) else os.path.expanduser('~'), 'HFPSelcallApp')


OUTBOX_DEFAULT = os.path.join(_log_dir(), 'outbox.txt')
LOG_FILE = os.path.join(_log_dir(), 'messages.txt')      # human-readable journal of ALL messages

DEFAULTS = dict(my_id=1, to_id=1, in_dev='', out_dev='', speed='5.86', f0=1611.4, tx_level=0.5,
                ptt_delay=0.5, afc=True, ack=False, counter=0, sens_db=4.0, auto_ack=False, only_mine=False,
                ptt_method='none', ptt_port='', ptt_baud=9600, ptt_invert=False,
                icom_model='IC-7300', icom_addr='94', kenwood_variant='TX;',
                rig_proto='ICOM', rig_port='', rig_baud=19200, rig_scen_enable=False, scenarios=None,
                outbox_enable=False, outbox_reply_none=False, outbox_ack_timeout=60, outbox_trigger='QRU?', outbox_file='',
                # ---- HF Selcall (CCIR 493-4, CODAN)
                sel_enable=True, sel_my_id='1234', sel_to_id='', sel_dot_seconds=6.0, sel_translit=True,
                sel_afc=True, sel_center=SE.S.F_CENTER, sel_ring=True, sel_ring_style='codan',
                sel_ring_volume=0.5, sel_ring_seconds=30.0, sel_ring_dev='', sel_tab=0,
                sel_ring_air=True, sel_answer_style='kalinka',
                sel_ext_enabled=False, sel_ext_port='', sel_ext_line='DTR', sel_ext_invert=False, sel_ext_seconds=5.0,
                sel_listen_after_call=True, sel_listen_seconds=60.0,
                sel_listen_after_tx=True, sel_listen_after_tx_seconds=60.0, sel_listen_level=1.0,
                # input channel of the sound card: 0 = auto (the one with signal), 1 = left, 2 = right
                in_channel=0,
                # ---- program (stage 1 of 0.3): look, language, clocks, folders
                lang='ru', theme='light', clock_tz='MSK', log_dir='', tab=0, geometry='',
                # ---- HFPager call / ring / answer (stage 2 of 0.3), same as for Selcall
                call_text='CALL', hfp_ring=True, hfp_ring_style='codan', hfp_ring_seconds=30.0,
                hfp_msg_sound=True, hfp_msg_style='beep', hfp_ring_air=True, hfp_answer_style='kalinka',
                hfp_listen_after_call=True, hfp_listen_seconds=60.0, hfp_ext_enabled=False,
                # answer with a melody on air to the message "BCN REQ" addressed to my ID (not to ID 0)
                bcn_req_enable=True, bcn_req_text='BCN REQ', bcn_req_style='kalinka',
                # message / call macros: 10 buttons under the chat
                macros=None,
                # beacon: every N minutes or at given UTC times; HFPager beacon / message, Selcall call / message, CW
                bcn_enable=False, bcn_mode='interval', bcn_interval=30.0, bcn_times='00:00 06:00 12:00 18:00',
                bcn_kind='hfp_beacon', bcn_to='0', bcn_text='', bcn_cw_wpm=20.0, bcn_cw_tone=800.0)

MACRO_KINDS = ['hfp_msg', 'hfp_call', 'sel_call', 'sel_msg']
BEACON_KINDS = ['hfp_beacon', 'hfp_msg', 'sel_call', 'sel_msg', 'cw']


def default_macros():
    return [dict(label='CQ', kind='hfp_msg', to='0', text='CQ CQ DE RA4PVJ', now=False),
            dict(label='QRU?', kind='hfp_msg', to='', text='QRU?', now=True),
            dict(label='73', kind='hfp_msg', to='', text='73!', now=False),
            dict(label='CALL', kind='hfp_call', to='', text='', now=True),
            dict(label='Selcall', kind='sel_call', to='', text='', now=True)] + \
        [dict(label='', kind='hfp_msg', to='', text='', now=False) for _ in range(5)]


CLIP_LEVEL = 0.98      # |sample| >= 0.98 of full scale (-0.18 dBFS) = input overload (also in hfpager_rx)


def read_peak(core):
    """peak input level in dBFS since the last call (for the level meter)"""
    pk, core.peak_max = core.peak_max, 0.0
    return 20 * np.log10(pk) if pk > 1e-6 else -90.0


# ============================================================================== non-GUI core
class Core:
    """Settings, audio streams, receiver engine, transmitter.  Talks to the GUI via a queue."""

    def __init__(self, ui_queue, sd_module=None):
        self.q = ui_queue
        self.sd = sd_module if sd_module is not None else sd
        self.s = dict(DEFAULTS)
        self.load()
        if not isinstance(self.s.get('scenarios'), list) or not self.s['scenarios']:
            self.s['scenarios'] = copy.deepcopy(G.DEFAULT_SCENARIOS)
        m = self.s.get('macros')
        if not isinstance(m, list) or len(m) != 10:
            self.s['macros'] = default_macros()
        self.engine = None
        self.stream = None
        self.fs = 48000
        self.tx_busy = False
        self._seen = {}
        self._tx_thread = None
        self.pending = {}          # (counter, header crc) -> (dest, text, time) awaiting an ACK
        self.ptt = P.PttController()
        self.last_tx_error = None
        self.last_key = None
        self._deferred = {}           # (counter, header crc) -> Event set when the ACK arrives
        self.outbox = []              # deferred messages: dict(to, text, added)
        self._outbox_mtime = None
        self._outbox_lock = threading.RLock()
        self._qru_busy = set()
        self.rig = G.RigController(self.ptt, ptt_cfg=self.ptt_cfg, ptt_open=self.ptt_apply)
        self.sel = None               # SelcallEngine, shares the input stream with self.engine
        self.ringer = SE.Ringer(self.sd)
        self.last_sel_rx = 0.0        # unix time of the last decoded Selcall (see 'fail' events)
        self.listener = SE.Listener(self.sd)       # input -> loudspeaker after a call
        self.listen_manual = False
        self.listen_timer = None
        self.listen_pending = None    # seconds of listening to start when the current TX ends
        self.ext = SE.ExtControl(P.serial)        # external device on its own COM port
        self.ext_manual = False
        self.ext_timer = None
        self.tx_history = []          # (to, text, start, end) of own Selcall TX: tells our echo from a call
        self._tx_meta = None
        self.in_channels = 1
        self.active_channel = 1
        self.ch_energy = None
        self.last_audio = time.time()
        self.last_restart = 0.0
        self.peak_max = 0.0           # max |sample| since the GUI last read it (level meter, dBFS)
        self.clip_time = 0.0          # last time the input reached the overload level
        self.bcn_last = time.time()       # beacon: time of the last one (interval mode counts from here)
        self.bcn_minute = None            # beacon: 'HH:MM' already served (time mode)
        self.bcn_next = None              # beacon: unix time of the next one, for the GUI
        threading.Thread(target=self._rx_watchdog, daemon=True).start()
        threading.Thread(target=self._beacon_loop, daemon=True).start()

    # ---- settings
    def load(self):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                self.s.update(json.load(f))
        except Exception:
            pass

    def save(self):
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.s, f, ensure_ascii=False, indent=1)
        except Exception as ex:
            self.sys(T('Не удалось сохранить настройки: %s') % ex)

    def data_dir(self):
        """folder of the journal and of the deferred messages (setting 'log_dir', default Documents/HFPSelcallApp)"""
        return self.s.get('log_dir') or os.path.dirname(LOG_FILE)

    def log_path(self):
        return os.path.join(self.s['log_dir'], 'messages.txt') if self.s.get('log_dir') else LOG_FILE

    def log(self, line):
        try:
            os.makedirs(os.path.dirname(self.log_path()), exist_ok=True)
            with open(self.log_path(), 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except Exception:
            pass

    def open_log(self):
        """open the journal in the default text editor; returns error text or None"""
        try:
            if not os.path.exists(self.log_path()):
                self.log(T('%s  Журнал создан') % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            if sys.platform.startswith('win'):
                os.startfile(self.log_path())
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.Popen(['open', self.log_path()])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', self.log_path()])
            return None
        except Exception as ex:
            return T('Не удалось открыть %s: %s') % (self.log_path(), ex)

    @staticmethod
    def _stamp():
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def sys(self, text):
        self.q.put(('sys', text))

    # ---- devices
    def devices(self):
        """returns (inputs, outputs): lists of (index, label)"""
        ins, outs = [], []
        if self.sd is None:
            return ins, outs
        try:
            apis = self.sd.query_hostapis()
            for i, d in enumerate(self.sd.query_devices()):
                api = apis[d['hostapi']]['name'] if d.get('hostapi') is not None else ''
                label = '%d: %s [%s]' % (i, d['name'], api)
                if d['max_input_channels'] > 0:
                    ins.append((i, label))
                if d['max_output_channels'] > 0:
                    outs.append((i, label))
        except Exception as ex:
            self.sys(T('Ошибка опроса звуковых устройств: %s') % ex)
        return ins, outs

    @staticmethod
    def _idx(label):
        try:
            return int(str(label).split(':')[0])
        except Exception:
            return None

    # ---- receiving
    def start_rx(self):
        self.stop_rx()
        if self.sd is None:
            self.sys(T('Звуковая библиотека недоступна: %s') % SD_ERROR)
            return False
        dev = self._idx(self.s['in_dev'])
        # up to 2 channels, ONE of them is used (not the average): on a stereo interface the transceiver is
        # usually on one input, and mixing with an empty channel halves the signal
        try:
            info = self.sd.query_devices(dev, 'input')
            nch = 2 if int(info.get('max_input_channels', 1)) >= 2 else 1
        except Exception:
            nch = 1
        fs = None
        for cand in (48000, 44100):
            try:
                self.sd.check_input_settings(device=dev, channels=1, samplerate=cand)
                fs = cand
                break
            except Exception:
                continue
        if fs is None:
            try:
                info = self.sd.query_devices(dev, 'input')
                fs = int(info['default_samplerate'])
            except Exception:
                fs = 48000
        self.fs = fs
        self.engine = R.RxEngine(fs, self._on_frame, self._on_event, afc=bool(self.s['afc']))
        self.engine.pk_margin = float(self.s.get('sens_db', 4.0))
        self.engine.start()
        if self.s.get('sel_enable', True):
            self.sel = SE.SelcallEngine(fs, self._on_sel_call, self._on_sel_event, afc=bool(self.s['sel_afc']),
                                        fixed_center=float(self.s['sel_center']))
            self.sel.start()
        engine, sel, listener = self.engine, self.sel, self.listener

        def cb(indata, frames, time_info, status):
            self.last_audio = time.time()
            x = indata[:, self._pick_channel(indata)]
            pk = float(np.max(np.abs(x))) if len(x) else 0.0
            if pk > self.peak_max:
                self.peak_max = pk
            if pk >= CLIP_LEVEL:
                self.clip_time = self.last_audio
            engine.feed(x)
            if sel is not None:
                sel.feed(x)
            if listener.active and not self.tx_busy:
                listener.feed(x)
        self.stream = None
        last = None
        for ch in ((nch, 1) if nch > 1 else (1,)):
            try:
                st = self.sd.InputStream(samplerate=fs, device=dev, channels=ch, dtype='float32',
                                         blocksize=int(0.05 * fs), callback=cb)
                self.in_channels, self.ch_energy = ch, None
                self.last_audio = time.time()
                st.start()
                self.stream = st
                break
            except Exception as ex:
                last = ex
        if self.stream is None:
            self.sys(T('Не удалось открыть вход звуковой карты: %s') % last)
            return False
        self.sys(T('Приём запущен (%d Гц). HFPager: все скорости, АПЧ %s.  Selcall: %s.') %
                 (fs, T('включена') if self.s['afc'] else T('выключена'),
                  (T('мой ID %s, АПЧ %s') % (self.s['sel_my_id'], T('включена') if self.s['sel_afc'] else
                                          T('выключена, центр %.0f Гц') % float(self.s['sel_center'])))
                  if self.sel is not None else T('выключен')))
        return True

    def stop_rx(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        if self.engine is not None:
            self.engine.stop()
            self.engine = None
        if self.sel is not None:
            self.sel.stop()
            self.sel = None

    def _pick_channel(self, indata):
        """index of the input channel to decode: fixed, or auto = the one with signal (with hysteresis)"""
        nch = indata.shape[1]
        want = int(self.s.get('in_channel') or 0)
        if want > 0:
            sel = min(want, nch) - 1
        elif nch > 1:
            e = np.mean(indata[::4].astype(np.float64) ** 2, axis=0)
            if self.ch_energy is None or len(self.ch_energy) != nch:
                self.ch_energy = np.zeros(nch)
            self.ch_energy = self.ch_energy * 0.9 + e
            best = int(np.argmax(self.ch_energy))
            cur = self.active_channel - 1
            sel = cur if (cur < nch and self.ch_energy[cur] * 2 >= self.ch_energy[best]) else best
        else:
            sel = 0
        self.active_channel = sel + 1
        return sel

    def _rx_watchdog(self):
        """the input gives no audio for > 4 s (USB codec 'fell asleep', IC-705) -> restart, at most every 10 s"""
        while True:
            time.sleep(1.0)
            now = time.time()
            if self.stream is not None and now - self.last_audio > 4 and now - self.last_restart > 10:
                self.last_restart = now
                self.q.put(('rx_restart', now - self.last_audio))

    def apply_live_settings(self):
        if self.engine is not None:
            self.engine.afc = bool(self.s['afc'])
            self.engine.pk_margin = float(self.s.get('sens_db', 4.0))
        if self.sel is not None:
            self.sel.afc = bool(self.s['sel_afc'])
            self.sel.fixed_center = float(self.s['sel_center'])

    # ---- HF Selcall reception
    def _on_sel_event(self, kind, info):
        self.q.put(('sel_event', kind, info))

    def _on_sel_call(self, c, when):
        """a Selcall / Message call was decoded (worker thread)"""
        self.last_sel_rx = time.time()
        mine = SE.same_id(c['to'], self.s['sel_my_id'])
        # a call FROM our own ID is a normal call (happens in practice); only our own transmission is an echo:
        # same addressee and text, at the time of our transmission
        own = SE.same_id(c['from'], self.s['sel_my_id']) and any(
            SE.same_id(t[0], c['to']) and t[1] == (c['message'] or '') and t[2] - 3 <= when <= t[3] + 3
            for t in self.tx_history)
        if c['eos'] == 'ACK-BQ':
            kind = T('ПОДТВЕРЖДЕНИЕ')
        elif c['message']:
            kind = T('СООБЩЕНИЕ')
        else:
            kind = T('ВЫЗОВ')
        self.log('%s  SELCALL %s  %s → %s%s%s: %s' % (
            datetime.datetime.fromtimestamp(when).strftime('%Y-%m-%d %H:%M:%S'), kind, c['from'], c['to'],
            '' if c['ecc_ok'] else T(' [СОМНИТЕЛЬНО]'), T(' [своя передача]') if own else '', c['message'] or '—'))
        self.q.put(('sel_rx', c, when, mine, own))
        if (self.s.get('rig_scen_enable') and mine and not own and c['ecc_ok'] and c['message']
                and c['eos'] != 'ACK-BQ'):
            threading.Thread(target=self.run_scenario, args=(c['message'], c['from']),
                             kwargs=dict(proto='sel'), daemon=True).start()

    def ring_dev(self):
        return self._idx(self.s.get('sel_ring_dev')) if self.s.get('sel_ring_dev') else None

    def ring(self, answer=False, prefix='sel_'):
        """start the incoming-call ring (answer=True: play the answer signal once, as a preview);
        prefix 'sel_' = Selcall settings, 'hfp_' = HFPager; returns error text or None"""
        return self.ringer.start(self.ring_dev(), self.ring_style(prefix, answer),
                                 float(self.s.get('sel_ring_volume', 0.5)),
                                 float(self.s.get(prefix + 'ring_seconds', 30.0)), answer=answer)

    def send_answer(self, to_id, style=None, label='SELCALL'):
        """answer on air: the answer signal once (melody ~2.9 s or tones 2.5 s) so the calling station hears
        that the call was received; returns error text or None"""
        if self.tx_busy:
            return T('Ответ в эфир не передан: идёт передача.')
        if self.sd is None:
            return T('Звуковая библиотека недоступна: %s') % SD_ERROR
        style = style or self.s.get('sel_answer_style', 'kalinka')
        sig = SE.answer_pattern(style, self.fs, float(self.s['tx_level']))
        lead = np.zeros(int(float(self.s['ptt_delay']) * self.fs), np.float32)
        audio = np.concatenate((lead, sig, np.zeros(int(0.3 * self.fs), np.float32))).astype(np.float32)
        self.last_tx_error = None
        self.tx_busy = True
        self._tx_meta = None
        self.q.put(('sel_answer_start', SE.digits(to_id), len(audio) / self.fs, label))
        self._tx_thread = threading.Thread(target=self._tx_run, args=(audio, self._idx(self.s['out_dev'])),
                                           daemon=True)
        self._tx_thread.start()
        self.log(T('%s  %s ОТВЕТ В ЭФИР → %s') % (self._stamp(), label, SE.digits(to_id)))
        return None

    def after_tx(self, fn, delay=1.0, timeout=120.0):
        """run fn() in a thread once the transmitter is free (after `delay` s); e.g. answer after an auto-ACK"""
        def work():
            time.sleep(delay)
            t0 = time.time()
            while self.tx_busy and time.time() - t0 < timeout:
                time.sleep(0.3)
            if self.tx_busy:
                return
            time.sleep(0.5)
            fn()
        threading.Thread(target=work, daemon=True).start()

    def ring_style(self, prefix, answer=False):
        return self.s.get(prefix + ('answer_style' if answer else 'ring_style'), 'kalinka' if answer else 'codan')

    def play_once(self, style):
        """incoming-message sound: the pattern once, on the ring device"""
        return self.ringer.start(self.ring_dev(), style, float(self.s.get('sel_ring_volume', 0.5)), 5.0, answer=True)

    # ---- listening to the air after a call (voice message / the station's reply)
    def start_listen(self, seconds=None):
        """input -> loudspeaker for 5 s … 10 min; a manual 'Слушать' is not interrupted"""
        if self.listen_manual:
            return
        self.ringer.stop()                      # the ring has done its job: now listen to the caller
        if self.stream is None:
            self.q.put(('sys', T('Прослушивание: приём выключен.')))
            return
        err = self.listener.start(self.ring_dev(), self.fs, float(self.s.get('sel_listen_level', 1.0)))
        if err:
            self.q.put(('sys', T('Прослушивание: %s') % err))
            return
        if self.listen_timer is not None:
            self.listen_timer.cancel()
        sec = min(600.0, max(5.0, float(seconds or self.s.get('sel_listen_seconds') or 60)))
        self.q.put(('sys', T('Прослушивание эфира включено на %.0f с') % sec))

        def off():
            if not self.listen_manual:
                self.listener.stop()
                self.q.put(('listen_state',))
        self.listen_timer = threading.Timer(sec, off)
        self.listen_timer.daemon = True
        self.listen_timer.start()
        self.q.put(('listen_state',))

    def toggle_listen(self):
        """the 'Слушать' button: on until pressed again"""
        if self.listen_timer is not None:
            self.listen_timer.cancel()
            self.listen_timer = None
        self.listen_pending = None
        if self.listener.active:
            self.listen_manual = False
            self.listener.stop()
        else:
            self.ringer.stop()
            err = self.listener.start(self.ring_dev(), self.fs, float(self.s.get('sel_listen_level', 1.0)))
            if err:
                self.q.put(('sys', T('Прослушивание: %s') % err))
            else:
                self.listen_manual = True
        self.q.put(('listen_state',))

    # ---- external device (siren, lamp, relay) on a separate COM port
    def ext_conflict(self):
        p = self.s.get('sel_ext_port') or ''
        busy = set()
        if self.s.get('ptt_method', 'none') != 'none':
            busy.add(self.s.get('ptt_port') or '')
        busy.add(self.s.get('rig_port') or '')
        return bool(p) and p in busy

    def _ext_set(self, on):
        if on and self.ext_conflict():
            self.q.put(('sys', T('Внешнее устройство: порт %s занят PTT/CAT — выберите другой COM-порт')
                        % self.s['sel_ext_port']))
            return False
        err = self.ext.set(on, self.s.get('sel_ext_port') or '', self.s.get('sel_ext_line') or 'DTR',
                           bool(self.s.get('sel_ext_invert')))
        if err:
            self.q.put(('sys', err))
            return False
        self.q.put(('ext_state',))
        return True

    def ext_pulse(self, seconds=None):
        """'1' on the line for 1…60 s; a manual switch-on is not interrupted"""
        if self.ext_manual or not self._ext_set(True):
            return
        if self.ext_timer is not None:
            self.ext_timer.cancel()
        sec = min(60.0, max(1.0, float(seconds or self.s.get('sel_ext_seconds') or 5)))

        def off():
            if not self.ext_manual:
                self._ext_set(False)
        self.ext_timer = threading.Timer(sec, off)
        self.ext_timer.daemon = True
        self.ext_timer.start()

    def ext_toggle(self):
        if self.ext_timer is not None:
            self.ext_timer.cancel()
            self.ext_timer = None
        if self.ext.on:
            self.ext_manual = False
            self._ext_set(False)
        elif self._ext_set(True):
            self.ext_manual = True
        self.q.put(('ext_state',))

    def ext_reset(self):
        if self.ext_timer is not None:
            self.ext_timer.cancel()
            self.ext_timer = None
        self.ext_manual = False
        self.ext.close(self.s.get('sel_ext_line') or 'RTS+DTR', bool(self.s.get('sel_ext_invert')))

    def _on_event(self, kind, info):
        self.q.put(('event', kind, info))

    def _on_frame(self, fr, info):
        now = time.time()
        stamp = datetime.datetime.now().isoformat(timespec='seconds')
        if fr.get('kind') in ('ack', 'nak'):
            mine = int(self.s['my_id'])
            hit = self.pending.pop((fr['orig_counter'], fr['orig_crc']), None) if fr['dest'] == mine else None
            ev = self._deferred.get((fr['orig_counter'], fr['orig_crc']))
            if ev is not None and fr['dest'] == mine and fr['kind'] == 'ack':
                ev.set()
            self.q.put(('ack', fr, info, hit))
            self.log(T('%s  %s       для ID %d, исходное сообщение №%d%s') % (
                self._stamp(), T('ПОДТВЕРЖДЕНИЕ') if fr['kind'] == 'ack' else T('ОТКАЗ'), fr['dest'],
                fr['orig_counter'], T(' (доставлено: «%s»)') % hit[1] if hit else ''))
            return
        key = (fr['sender'], fr['dest'], fr['counter'], fr['text'])
        dup = key in self._seen and now - self._seen[key] < 120
        self._seen[key] = now
        for k in [k for k, t in self._seen.items() if now - t > 600]:
            del self._seen[k]
        self.q.put(('rx', fr, info, dup))
        self.log(T('%s  %s  %d → %d  №%d  (%s Бод)%s: %s') % (
            self._stamp(), T('МАЯК  ') if fr.get('b0') == 0x06 else T('ПРИЁМ  '), fr['sender'], fr['dest'],
            fr['counter'], fr['speed'], T(' [повтор]') if dup else '', fr['text'].decode('cp1251', 'replace')))
        text_n = ' '.join(fr['text'].decode('cp1251', 'replace').upper().split())
        to_me = fr.get('kind') == 'msg' and fr['dest'] == int(self.s['my_id'])
        if (self.s.get('rig_scen_enable') and to_me and not dup):
            threading.Thread(target=self.run_scenario,
                             args=(fr['text'].decode('cp1251', 'replace'), fr['sender']), daemon=True).start()
        if to_me and not dup:
            is_call = text_n == ' '.join(str(self.s.get('call_text') or 'CALL').upper().split())
            self.q.put(('hfp_call' if is_call else 'hfp_msg_to_me', fr))
        bq = ' '.join(str(self.s.get('bcn_req_text') or 'BCN REQ').upper().split())
        if (self.s.get('bcn_req_enable') and fr.get('kind') == 'msg' and not dup and text_n == bq
                and fr['dest'] == int(self.s['my_id'])):
            snd = fr['sender']
            self.sys(T('Запрос %s от ID %d — отвечаю мелодией в эфир') % (bq, snd))
            self.after_tx(lambda: self._answer_or_log(snd, self.s.get('bcn_req_style', 'kalinka'), 'HFPager ' + bq),
                          delay=1.5)
        if (self.s.get('outbox_enable') and fr.get('kind') == 'msg' and fr['dest'] == int(self.s['my_id'])
                and not dup and ' '.join(fr['text'].decode('cp1251', 'replace').upper().split())
                == ' '.join(str(self.s.get('outbox_trigger', 'QRU?')).upper().split())):
            threading.Thread(target=self.on_qru, args=(fr['sender'],), daemon=True).start()
        if (self.s.get('auto_ack') and fr.get('kind') == 'msg' and (fr['b1'] & 0x02)
                and fr['dest'] == int(self.s['my_id']) and not dup):
            threading.Timer(1.5, self.send_ack, args=(fr,)).start()

    # ---- deferred messages (sent when the addressee asks "QRU?") -----------------------------------
    OUTBOX_HEADER = (T('# HFPager: отложенные сообщения. Одна строка = одно сообщение:  ID получателя|текст\n'
                     '# Строки с # и пустые игнорируются. Кодировка UTF-8. Файл можно править вручную или из другой программы:\n'
                     '# приложение перечитывает его при изменении и при запросе QRU?. Отправленные строки удаляются\n'
                     '# отсюда и дописываются в outbox_sent.txt в формате  дата время|ID|текст\n'))

    def outbox_path(self):
        return self.s.get('outbox_file') or os.path.join(self.data_dir(), 'outbox.txt')

    def outbox_sent_path(self):
        return os.path.join(os.path.dirname(self.outbox_path()), 'outbox_sent.txt')

    @staticmethod
    def parse_outbox(text):
        items = []
        for line in text.replace('\ufeff', '').splitlines():
            line = line.strip('\r\n')
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            sep = '|' if '|' in line else ('\t' if '\t' in line else None)
            if sep is None:
                continue
            a, b = line.split(sep, 1)
            a, b = a.strip(), b.strip()
            if a.isdigit() and 0 <= int(a) <= 65535 and b:
                items.append(dict(to=int(a), text=b))
        return items

    def outbox_load(self):
        """read the file (missing file = empty list); returns error text or None"""
        with self._outbox_lock:
            path = self.outbox_path()
            try:
                if not os.path.exists(path):
                    self.outbox, self._outbox_mtime = [], None
                    return None
                with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
                    self.outbox = self.parse_outbox(f.read())
                self._outbox_mtime = os.path.getmtime(path)
                return None
            except Exception as ex:
                return T('Не удалось прочитать %s: %s') % (path, ex)

    def outbox_save(self):
        with self._outbox_lock:
            path = self.outbox_path()
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                tmp = path + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    f.write(self.OUTBOX_HEADER)
                    for it in self.outbox:
                        f.write('%d|%s\n' % (it['to'], it['text'].replace('\n', ' ').replace('\r', ' ')))
                os.replace(tmp, path)
                self._outbox_mtime = os.path.getmtime(path)
                return None
            except Exception as ex:
                return T('Не удалось записать %s: %s') % (path, ex)

    def outbox_changed_on_disk(self):
        try:
            m = os.path.getmtime(self.outbox_path()) if os.path.exists(self.outbox_path()) else None
        except Exception:
            return False
        return m != self._outbox_mtime

    def outbox_mark_sent(self, item):
        """remove the item from the file (re-reading it first, so edits made by other programs survive)
        and append it to outbox_sent.txt"""
        with self._outbox_lock:
            self.outbox_load()
            for i, it in enumerate(self.outbox):
                if it['to'] == item['to'] and it['text'] == item['text']:
                    del self.outbox[i]
                    break
            self.outbox_save()
            try:
                with open(self.outbox_sent_path(), 'a', encoding='utf-8') as f:
                    f.write('%s|%d|%s\n' % (self._stamp(), item['to'], item['text']))
            except Exception:
                pass
        self.q.put(('outbox_changed',))

    def outbox_send(self, items, first_delay=2.0, gap=2.0):
        """transmit the given deferred messages one after another (blocking; run in a thread)"""
        time.sleep(first_delay)
        sent = 0
        for it in items:
            t0 = time.time()
            while self.tx_busy and time.time() - t0 < 120:
                time.sleep(0.3)
            need_ack = not it.get('noack')
            err = self.send(it['to'], it['text'], force_ack=need_ack)
            key = self.last_key
            ev = threading.Event()
            if need_ack and key:
                self._deferred[key] = ev
            if err:
                self.sys(T('Отложенное сообщение для %d не отправлено: %s') % (it['to'], err))
                break
            while self.tx_busy:                 # wait until the transmission has really finished
                time.sleep(0.3)
            if self.last_tx_error:              # PTT / sound failure: keep the message in the queue
                self.sys(T('Отложенное сообщение для %d НЕ отправлено (останется в очереди): %s') % (
                    it['to'], self.last_tx_error))
                break
            if need_ack:
                tmo = float(self.s.get('outbox_ack_timeout', 60))
                self.sys(T('Отложенное сообщение для %d передано, жду подтверждение до %.0f с…') % (it['to'], tmo))
                got = ev.wait(tmo)
                self._deferred.pop(key, None)
                if not got:
                    self.sys(T('Подтверждения от ID %d нет – сообщение остаётся в очереди '
                             '(будет отправлено снова при следующем запросе).') % it['to'])
                    self.log(T('%s  ОТЛОЖЕННОЕ БЕЗ ПОДТВЕРЖДЕНИЯ  → %d: %s') % (self._stamp(), it['to'], it['text']))
                    break
                self.outbox_mark_sent(it)
                self.sys(T('Подтверждение от ID %d получено – сообщение удалено из очереди.') % it['to'])
            sent += 1
            self.log(T('%s  ОТЛОЖЕННОЕ ДОСТАВЛЕНО  → %d: %s') % (self._stamp(), it['to'], it['text']))
            time.sleep(gap)
        return sent

    def on_qru(self, sender):
        """the station `sender` asked "QRU?" - send everything waiting for it (max 5 messages)"""
        if sender in self._qru_busy:
            return
        self._qru_busy.add(sender)
        try:
            err = self.outbox_load()
            if err:
                self.sys(err)
            items = [dict(it) for it in self.outbox if it['to'] == sender][:5]
            self.log(T('%s  ЗАПРОС %s от ID %d: отложенных сообщений %d') % (
                self._stamp(), self.s.get('outbox_trigger', 'QRU?'), sender, len(items)))
            if items:
                self.sys(T('Запрос %s от ID %d – отправляю отложенные сообщения: %d') % (
                    self.s.get('outbox_trigger', 'QRU?'), sender, len(items)))
                self.outbox_send(items)
            elif self.s.get('outbox_reply_none'):
                self.sys(T('Запрос %s от ID %d – отложенных нет, отвечаю QRU') % (
                    self.s.get('outbox_trigger', 'QRU?'), sender))
                self.outbox_send([dict(to=sender, text='QRU', noack=True)])
            else:
                self.sys(T('Запрос %s от ID %d – отложенных сообщений для него нет') % (
                    self.s.get('outbox_trigger', 'QRU?'), sender))
        finally:
            self._qru_busy.discard(sender)

    # ---- transceiver CAT control / scenarios
    def rig_cfg(self):
        try:
            addr = P.parse_hex_addr(self.s.get('icom_addr', '94'))
        except Exception:
            addr = 0x94
        return dict(proto=self.s.get('rig_proto', 'ICOM'), port=self.s.get('rig_port', ''),
                    baud=int(self.s.get('rig_baud') or 9600), icom_addr=addr)

    def run_actions_logged(self, actions, why):
        """waits for the end of own transmission, then executes; returns True if all succeeded"""
        t0 = time.time()
        while self.tx_busy and time.time() - t0 < 30:
            time.sleep(0.2)
        if self.tx_busy:
            self.sys(T('Сценарий пропущен: идёт передача.'))
            return False
        ok = True
        for a, good, msg in self.rig.run_actions(self.rig_cfg(), actions):
            ok = ok and good
            line = '%s: %s – %s' % (why, a, ('OK, ' + msg) if good else T('ОШИБКА: ') + msg)
            self.sys(T('Трансивер  ') + line)
            self.log(T('%s  ТРАНСИВЕР  %s') % (self._stamp(), line))
        return ok

    def scenario_rows(self, proto):
        """rows usable for a message of protocol 'hfp' / 'sel': the sender check of a Selcall message uses
        the 'Selcall ID' column (Selcall IDs are compared as numbers, 0123 == 123)"""
        rows = []
        for r in self.s['scenarios']:
            p = r.get('proto', 'both')
            if p not in ('both', proto):
                rows.append(dict(r, on=False))          # keep the indexes = table row numbers
                continue
            rows.append(dict(r, **{'from': r.get('sel_from', '')}) if proto == 'sel' else r)
        return rows

    def run_scenario(self, text, sender, manual=False, proto='hfp'):
        """find the first matching scenario for a message and execute it; returns a status string"""
        try:
            if proto == 'sel' and sender is not None:
                sender = int(SE.digits(sender) or 0)
            rows = self.s['scenarios'] if manual else self.scenario_rows(proto)
            hit = G.match_rows(rows, text, None if manual else sender)
        except G.RigError as ex:
            self.sys(T('Сценарий: %s') % ex)
            return str(ex)
        if not hit:
            return None
        idx, actions = hit
        self.run_actions_logged(actions, T('сценарий %d «%s»') % (idx + 1, text))
        return actions

    def _answer_or_log(self, to, style, label):
        err = self.send_answer(str(to), style=style, label=label)
        if err:
            self.sys(err)

    def send_ack(self, fr):
        """experimental: confirm delivery of a received message"""
        if self.tx_busy or self.sd is None:
            return
        own = int(self.s['counter']) & 0xFF
        with R.MODEM_LOCK:
            M.set_speed(fr['speed'])
            nib = M.tx_nibbles(M.ack_frame_nibbles(fr['sender'], fr['counter'], fr['hdr_crc'],
                                                   orig_len=fr['length'], own_counter=own))
            audio = M.synth(M.nibbles_to_tones(nib), fs=self.fs, f0=float(self.s['f0']),
                            amp=float(self.s['tx_level']), lead=float(self.s['ptt_delay']), tail=0.3)
        self.s['counter'] = (own + 1) & 0xFF
        self.save()
        self.log(T('%s  ПОДТВЕРЖДЕНИЕ ОТПРАВЛЕНО  для ID %d, сообщение №%d') % (self._stamp(), fr['sender'], fr['counter']))
        self.tx_busy = True
        self.q.put(('tx_ack', fr['sender'], fr['counter'], fr['speed'], len(audio) / self.fs))
        self._tx_thread = threading.Thread(target=self._tx_run,
                                           args=(audio.astype(np.float32), self._idx(self.s['out_dev'])),
                                           daemon=True)
        self._tx_thread.start()

    # ---- transmitting
    @staticmethod
    def air_time(speed, nbytes):
        sp = R.M.SPEEDS[speed]
        nsb = 1 + (nbytes + 11) // 12
        return (sp['pre'] + 1 + 60 * nsb + 2) / sp['baud']

    def build_audio(self, dest, sender, counter, text_bytes, speed, f0, level, ptt_delay, ack, b0=0x05):
        with R.MODEM_LOCK:
            M.set_speed(speed)
            nib = M.tx_nibbles(M.frame_nibbles(dest, sender, counter, text_bytes, b0=b0,
                                               b1=0xA2 if ack else 0xA0))
            tones = M.nibbles_to_tones(nib)
            audio = M.synth(tones, fs=self.fs, f0=f0, amp=level, lead=ptt_delay, tail=0.3)
        return audio.astype(np.float32)

    def send_call(self, to_id):
        """HFPager call: the message CALL (text configurable) sent at once"""
        return self.send(to_id, str(self.s.get('call_text') or 'CALL'))

    def send_hfp_beacon(self, text):
        """HFPager beacon frame (type 0x06, destination 0), like the HFPager app's \"Beacon from …\""""
        return self.send(0, text, beacon=True)

    def send_cw(self, text):
        if self.tx_busy:
            return T('Передача уже идёт.')
        if self.sd is None:
            return T('Звуковая библиотека недоступна: %s') % SD_ERROR
        if not CW.morse(text):
            return T('CW: нет передаваемых символов.')
        audio = CW.cw_audio(text, self.fs, wpm=float(self.s.get('bcn_cw_wpm', 20)),
                            tone=float(self.s.get('bcn_cw_tone', 800)), level=float(self.s['tx_level']),
                            lead=float(self.s['ptt_delay']))
        self.last_tx_error = None
        self.tx_busy = True
        self._tx_meta = None
        self.q.put(('cw_start', text, len(audio) / self.fs))
        self._tx_thread = threading.Thread(target=self._tx_run, args=(audio, self._idx(self.s['out_dev'])),
                                           daemon=True)
        self._tx_thread.start()
        self.log(T('%s  CW: %s') % (self._stamp(), text))
        return None

    # ---- beacon (by interval or at given UTC times)
    @staticmethod
    def parse_times(text):
        out = []
        for tok in str(text).replace(',', ' ').replace(';', ' ').split():
            try:
                h, m = tok.split(':')
                h, m = int(h), int(m)
                if 0 <= h < 24 and 0 <= m < 60:
                    out.append('%02d:%02d' % (h, m))
            except ValueError:
                pass
        return sorted(set(out))

    def beacon_text(self):
        t = str(self.s.get('bcn_text') or '').strip()
        if t:
            return t
        return 'Beacon from %s' % (self.s.get('my_id'),)

    def send_beacon(self):
        """one beacon of the configured kind; returns error text or None"""
        kind, text, to = self.s.get('bcn_kind', 'hfp_beacon'), self.beacon_text(), str(self.s.get('bcn_to') or '0')
        if kind == 'hfp_beacon':
            return self.send_hfp_beacon(text)
        if kind == 'hfp_msg':
            return self.send(to, text)
        if kind == 'sel_call':
            return self.send_selcall(to, None)
        if kind == 'sel_msg':
            return self.send_selcall(to, text)
        return self.send_cw(text)

    def beacon_due(self, now=None):
        """(due now?, unix time of the next beacon or None)"""
        now = time.time() if now is None else now
        if self.s.get('bcn_mode') == 'times':
            times = self.parse_times(self.s.get('bcn_times', ''))
            if not times:
                return False, None
            u = datetime.datetime.utcfromtimestamp(now)
            hm = u.strftime('%H:%M')
            due = hm in times and self.bcn_minute != u.strftime('%Y-%m-%d ') + hm
            nxt = None
            for d in (0, 1):
                day = u.date() + datetime.timedelta(days=d)
                for t in times:
                    h, m = map(int, t.split(':'))
                    cand = (datetime.datetime(day.year, day.month, day.day, h, m) -
                            datetime.datetime(1970, 1, 1)).total_seconds()
                    if cand > now - 60 and (nxt is None or cand < nxt):
                        nxt = cand
            return due, nxt
        iv = max(1.0, float(self.s.get('bcn_interval') or 30)) * 60
        return now - self.bcn_last >= iv, self.bcn_last + iv

    def _beacon_loop(self):
        while True:
            time.sleep(2.0)
            try:
                if not self.s.get('bcn_enable'):
                    self.bcn_next = None
                    continue
                due, self.bcn_next = self.beacon_due()
                if not due:
                    continue
                # do not transmit over a signal being received or our own transmission: wait (up to the next check)
                busy = self.tx_busy or (self.engine is not None and getattr(self.engine, '_seg', None) is not None)
                if busy:
                    continue
                now = time.time()
                self.bcn_last = now
                self.bcn_minute = datetime.datetime.utcfromtimestamp(now).strftime('%Y-%m-%d %H:%M')
                err = self.send_beacon()
                self.sys(T('Маяк: %s') % (err or T('передан')))
            except Exception as ex:
                self.sys(T('Маяк: ошибка %s') % ex)

    def send(self, to_id, text, force_ack=False, beacon=False):
        """validate and start transmission; returns error text or None"""
        if self.tx_busy:
            return T('Передача уже идёт.')
        if self.sd is None:
            return T('Звуковая библиотека недоступна: %s') % SD_ERROR
        try:
            my = int(self.s['my_id'])
            to = int(to_id)
        except Exception:
            return T('ID должны быть числами.')
        if not (0 <= my <= 65535) or not (0 <= to <= 65535):
            return T('ID должен быть в диапазоне 0…65535.')
        data = text.encode('cp1251', 'replace')
        if not (1 <= len(data) <= 252):
            return T('Длина текста: от 1 до 252 символов (сейчас %d).') % len(data)
        speed = self.s['speed']
        f0 = float(self.s['f0'])
        if not (300 <= f0 <= 2000):
            return T('Частота нулевого тона должна быть в диапазоне 300…2000 Гц.')
        counter = int(self.s['counter']) & 0xFF
        out = self._idx(self.s['out_dev'])
        want_ack = (bool(self.s['ack']) or bool(force_ack)) and not beacon
        audio = self.build_audio(to, my, counter, data, speed, f0, float(self.s['tx_level']),
                                 float(self.s['ptt_delay']), want_ack, b0=0x06 if beacon else 0x05)
        self.last_key = None
        if want_ack:
            crc = M.header_crc(to, my, counter, data, b1=0xA2)
            self.pending[(counter, crc)] = (to, text, time.time())
            self.last_key = (counter, crc)
        self.s['counter'] = (counter + 1) & 0xFF
        if not beacon:
            self.s['to_id'] = to
        self.save()
        self.last_tx_error = None
        self.tx_busy = True
        self.q.put(('tx_start', my, to, counter, text, speed, len(audio) / self.fs))
        self._tx_thread = threading.Thread(target=self._tx_run, args=(audio, out), daemon=True)
        self._tx_thread.start()
        self.log(T('%s  ПЕРЕДАЧА  %d → %d  №%d  (%s Бод)%s: %s') % (
            self._stamp(), my, to, counter, speed, T(' [запрос подтверждения]') if want_ack else '', text))
        return None

    def send_selcall(self, to_id, message=None):
        """HF Selcall: individual call (message=None) or Message call; returns error text or None"""
        if self.tx_busy:
            return T('Передача уже идёт.')
        if self.sd is None:
            return T('Звуковая библиотека недоступна: %s') % SD_ERROR
        err = SE.check_ids(self.s['sel_my_id'], to_id)
        if err:
            return err
        if message is not None and not message.strip():
            return T('Введите текст сообщения (до %d символов).') % SE.MAX_MSG
        dots = float(self.s['sel_dot_seconds'])
        if not (0.5 <= dots <= 20):
            return T('Длительность точек (фазирования) должна быть 0.5…20 с.')
        me, to = SE.digits(self.s['sel_my_id']), SE.digits(to_id)
        text, audio = SE.build_audio(to, me, message, self.fs, dot_seconds=dots,
                                     level=float(self.s['tx_level']), lead=float(self.s['ptt_delay']),
                                     tail=0.3, use_translit=bool(self.s['sel_translit']))
        self.s['sel_to_id'] = to
        self.save()
        self.last_tx_error = None
        self.tx_busy = True
        self._tx_meta = (to, text, len(audio) / self.fs)
        if self.s.get('sel_listen_after_tx', True):          # then listen: to hear the station's reply
            self.listen_pending = float(self.s.get('sel_listen_after_tx_seconds') or 60)
        self.q.put(('sel_tx_start', me, to, text, len(audio) / self.fs))
        self._tx_thread = threading.Thread(target=self._tx_run, args=(audio, self._idx(self.s['out_dev'])),
                                           daemon=True)
        self._tx_thread.start()
        self.log(T('%s  SELCALL ПЕРЕДАЧА  %s %s → %s%s') % (
            self._stamp(), T('СООБЩЕНИЕ') if text else T('ВЫЗОВ'), me, to, (': ' + text) if text else ''))
        return None

    def ptt_cfg(self):
        try:
            addr = P.parse_hex_addr(self.s.get('icom_addr', '94'))
        except Exception:
            addr = 0x94
        return dict(method=self.s.get('ptt_method', 'none'), port=self.s.get('ptt_port', ''),
                    baud=int(self.s.get('ptt_baud') or 9600), invert=bool(self.s.get('ptt_invert')),
                    icom_addr=addr, kenwood_variant=self.s.get('kenwood_variant', 'TX;'))

    def ptt_apply(self):
        """open / reconfigure the PTT port; returns error text or None"""
        cfg = self.ptt_cfg()
        if cfg['method'] != 'none' and cfg.get('port') and cfg['port'] == self.ext.port:
            self.ext_reset()                   # PTT wins over the external device on the same port
        return self.ptt.configure(cfg)

    def ptt_test(self, seconds=1.0):
        """key the transmitter for a short time (no audio!) – blocking, call from a worker thread"""
        if self.tx_busy:
            return T('Передача уже идёт.')
        self.tx_busy = True
        try:
            err = self.ptt_apply() or self.ptt.key(True)
            if err:
                return err
            time.sleep(seconds)
            return None
        finally:
            self.ptt.unkey_safe()
            self.tx_busy = False

    def _tx_run(self, audio, out):
        self.ringer.stop()
        meta, self._tx_meta = self._tx_meta, None
        if meta is not None:
            now = time.time()
            self.tx_history = [t for t in self.tx_history if now - t[3] < 120]
            self.tx_history.append((meta[0], meta[1], now, now + meta[2]))
        if self.engine is not None:
            self.engine.pause(True)
        sel = self.sel
        if sel is not None:
            sel.mute(True)
        err = None
        keyed = False
        try:
            if self.ptt_cfg()['method'] != 'none':
                pp = self.s.get('ptt_port') or ''
                if pp and self.ext.port == pp:          # the same COM port was taken by the external device
                    self.ext_reset()
                err = self.ptt_apply() or self.ptt.key(True)
                if err:
                    err = T('PTT: %s – передача отменена') % err
                    return
                keyed = True
            self.sd.play(audio, self.fs, device=out)
            self.sd.wait()
        except Exception as ex:
            err = str(ex)
        finally:
            if keyed or self.ptt.keyed:
                time.sleep(0.15)
                uerr = self.ptt.unkey_safe()
                if uerr:
                    err = ((err + '; ') if err else '') + T('НЕ УДАЛОСЬ СНЯТЬ PTT: %s – выключите передачу вручную!') % uerr
            time.sleep(0.4)
            if self.engine is not None:
                self.engine.pause(False)
            if sel is not None:
                sel.mute(False)
            self.last_tx_error = err
            self.tx_busy = False
            self.q.put(('tx_done', err))
            sec, self.listen_pending = self.listen_pending, None
            if sec and not err:
                self.start_listen(sec)

    def abort_tx(self):
        try:
            self.sd.stop()
        except Exception:
            pass
        # _tx_run releases PTT right after the stream stops; extra safety if it is stuck
        if self.ptt.keyed and not self.tx_busy:
            self.ptt.unkey_safe()


# ============================================================================== GUI
def run_gui():
    import hfp_selcall_gui
    hfp_selcall_gui.run()


if __name__ == '__main__':
    run_gui()
