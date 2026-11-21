"""
Headless check of HFP+SELCALL (no sound card, no GUI):
  1. one input stream feeds both receivers: an HFPager frame and a Selcall call in the same audio
     are both decoded;
  2. the Selcall transmitter (through Core.send_selcall and the common _tx_run) produces audio that
     the Selcall decoder reads back, with PTT/RX-pause handled;
  3. the real CODAN recording from ra4pvj/SELCALL is decoded through the shared stream;
  4. features from SELCALL 0.3.x: repeated identical calls, calls from our own ID vs our echo,
     answer on air, listening after a call, external device port check, stereo input channel pick.

    python tests/test_combined.py
"""
import os
import datetime
import queue
import sys
import tempfile
import time

import numpy as np

try:                                     # Windows consoles (cp1252/cp866) cannot print the arrows/quotes
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import hfp_selcall_app as A      # noqa: E402
import selcall as S              # noqa: E402
import selcall_engine as SE      # noqa: E402


class FakeStream:
    def __init__(self, callback=None, **kw):
        self.callback = callback
        self.samplerate = kw.get('samplerate')

    def start(self):
        FakeSD.streams.append(self)

    def stop(self):
        pass

    def abort(self):
        pass

    def close(self):
        pass


class FakeOut(FakeStream):
    def start(self):
        FakeSD.outs.append(self)


class FakeSD:
    """just enough of sounddevice for Core"""
    streams = []
    outs = []
    played = []
    in_channels = 1
    InputStream = FakeStream
    OutputStream = FakeOut

    @staticmethod
    def check_input_settings(**kw):
        if kw.get('samplerate') != 48000:
            raise ValueError('only 48 kHz here')

    @classmethod
    def query_devices(cls, *a, **kw):
        d = {'name': 'Fake', 'default_samplerate': 48000, 'max_input_channels': cls.in_channels,
             'max_output_channels': 2, 'hostapi': 0}
        return [d] if not a and not kw else d

    @staticmethod
    def query_hostapis():
        return [{'name': 'Fake API'}]

    @classmethod
    def play(cls, audio, fs, device=None):
        cls.played.append((np.asarray(audio).copy(), fs))

    @staticmethod
    def wait():
        pass

    @staticmethod
    def stop():
        pass


def push(core, x, fs, block=0.05, nch=1, chan=0):
    cb = FakeSD.streams[-1].callback
    n = int(block * fs)
    sel = core.sel
    done = 0
    for i in range(0, len(x), n):
        b = x[i:i + n].astype(np.float32)
        blk = np.zeros((len(b), nch), np.float32)
        blk[:, chan] = b
        cb(blk, len(b), None, None)
        done += len(b)
        if done >= fs:                       # Selcall decoder runs once per second of audio
            sel.process_now()
            done = 0
            time.sleep(0.005)


def drain(q, timeout):
    out = []
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            out.append(q.get(timeout=0.2))
        except queue.Empty:
            pass
    return out


def make_core(tmp):
    A.SETTINGS_FILE = os.path.join(tmp, 'settings.json')
    A.LOG_FILE = os.path.join(tmp, 'messages.txt')
    q = queue.Queue()
    core = A.Core(q, sd_module=FakeSD)
    core.s.update(my_id=10048, sel_my_id='1234', speed='23.44', f0=1000.0, ptt_delay=0.2, tx_level=0.3)
    return core, q


def test_both_receivers(tmp):
    core, q = make_core(tmp)
    A.sd = FakeSD
    assert core.start_rx(), 'start_rx failed'
    core.sel.stop()                          # drive the Selcall decoder by hand (faster than real time)
    fs = core.fs
    hfp = core.build_audio(10048, 3, 7, 'HELLO'.encode('cp1251'), '23.44', 1000.0, 0.3, 0.0, False)
    _, sel = SE.build_audio('1234', '5678', 'TEST 73', fs, dot_seconds=3.0, level=0.3, lead=0, tail=0)
    rng = np.random.default_rng(1)
    gap = np.zeros(int(3 * fs), dtype=np.float32)
    x = np.concatenate([gap, hfp, gap, sel, gap, gap, gap, gap, gap, gap, gap, gap]).astype(np.float32)
    x += (0.01 * rng.standard_normal(len(x))).astype(np.float32)
    push(core, x, fs)
    core.sel.process_now(flush=True)
    items = drain(q, 8.0)
    core.stop_rx()
    rx = [i for i in items if i[0] == 'rx']
    srx = [i for i in items if i[0] == 'sel_rx']
    assert any(i[1]['text'] == b'HELLO' and i[1]['sender'] == 3 for i in rx), 'HFPager frame not decoded: %r' % rx
    assert any(i[1]['from'] == '5678' and i[1]['to'] == '1234' and i[1]['message'] == 'TEST 73' and i[3]
               for i in srx), 'Selcall not decoded: %r' % srx
    print('OK  shared input: HFPager "HELLO" 3→10048 and Selcall 5678→1234 «TEST 73» both decoded')


def test_selcall_tx(tmp):
    core, q = make_core(tmp)
    FakeSD.played.clear()
    core.fs = 48000
    for msg, title in ((None, 'вызов'), ('Привет', 'сообщение')):
        err = core.send_selcall('4321', msg)
        assert err is None, err
        core._tx_thread.join(10)
        assert not core.tx_busy
        audio, fs = FakeSD.played[-1]
        calls = S.decode(SE.Downsampler(fs).push(audio), SE.RX_FS)
        want = SE.translit(msg) if msg else ''
        assert any(c['from'] == '1234' and c['to'] == '4321' and (c['message'] or '') == want and c['ecc_ok']
                   for c in calls), calls
        print('OK  Selcall TX (%s) 1234→4321%s: decoded back' % (title, (' «%s»' % want) if want else ''))
    assert core.send_selcall('', None), 'empty ID must be rejected'
    items = drain(q, 0.3)
    assert [i for i in items if i[0] == 'sel_tx_start'] and [i for i in items if i[0] == 'tx_done']


def test_real_recording(tmp):
    core, q = make_core(tmp)
    assert core.start_rx()
    core.sel.stop()
    x, fs_w = S.read_wav(os.path.join(ROOT, 'testdata', 'SELCALL_from_1111_to_1234.wav'))
    fs = core.fs
    # float arange: on Windows numpy 1.x the default int is 32-bit and n * 44100 would overflow
    x = np.interp(np.arange(int(len(x) * fs / fs_w), dtype=np.float64) * fs_w / fs,
                  np.arange(len(x), dtype=np.float64), x).astype(np.float32)
    x = np.concatenate([x, np.zeros(3 * fs, dtype=np.float32)])
    push(core, x, fs)
    core.sel.process_now(flush=True)
    items = drain(q, 2.0)
    core.stop_rx()
    srx = [i for i in items if i[0] == 'sel_rx']
    assert any(i[1]['from'] == '1111' and i[1]['to'] == '1234' and i[3] for i in srx), srx
    print('OK  real CODAN recording: 1111→1234 decoded through the shared input (resampled to 48 kHz)')


def test_selcall_03x(tmp):
    """repeat fix, own-ID calls vs echo, stereo channel pick (one input stream, 2 channels, signal on #2)"""
    core, q = make_core(tmp)
    FakeSD.in_channels = 2
    try:
        assert core.start_rx()
    finally:
        FakeSD.in_channels = 1
    assert core.in_channels == 2
    core.sel.stop()
    fs = core.fs
    _, a = SE.build_audio('1234', '5678', None, fs, dot_seconds=3.0, level=0.3, lead=0, tail=0)
    _, own = SE.build_audio('4321', '1234', 'ECHO', fs, dot_seconds=3.0, level=0.3, lead=0, tail=0)
    _, frm = SE.build_audio('1234', '1234', 'SELF', fs, dot_seconds=3.0, level=0.3, lead=0, tail=0)
    gap = np.zeros(int(4 * fs), np.float32)
    seq = [gap, a, gap, gap, a, gap, gap]                 # the same call twice, ~15 s apart
    t_own = 3 + sum(len(v) for v in seq) / fs
    seq += [own, gap, gap, frm] + [gap] * 8
    now = time.time()
    core.tx_history = [('4321', 'ECHO', now + t_own - 1, now + t_own + len(own) / fs + 1)]
    core.sel.t0 = now
    push(core, np.concatenate([gap[:3 * fs]] + seq), fs, nch=2, chan=1)
    core.sel.process_now(flush=True)
    items = drain(q, 1.0)
    core.stop_rx()
    assert core.active_channel == 2, core.active_channel
    srx = [(i[1]['from'], i[1]['to'], i[1]['message'] or '', i[3], i[4]) for i in items if i[0] == 'sel_rx']
    calls = [r for r in srx if r[:2] == ('5678', '1234')]
    assert len(calls) == 2 and all(r[3] and not r[4] for r in calls), srx
    assert ('1234', '4321', 'ECHO', False, True) in srx, srx                # our own transmission: echo
    assert ('1234', '1234', 'SELF', True, False) in srx, srx                # call FROM our ID: a real call
    print('OK  stereo input: channel 2 picked; same call twice → 2 calls, no duplicates; '
          'echo of own TX vs call from own ID told apart')


def test_answer_listen_ext(tmp):
    core, q = make_core(tmp)
    FakeSD.played.clear()
    core.fs = 48000
    core.s['sel_answer_style'] = 'kalinka'
    core.listen_pending = 7
    assert core.start_rx()
    assert core.send_answer('5678') is None
    core._tx_thread.join(10)
    audio, fs = FakeSD.played[-1]
    want = 16 * SE.KALINKA_QUARTER + core.s['ptt_delay'] + 0.3
    assert abs(len(audio) / fs - want) < 0.03 and np.abs(audio).max() <= core.s['tx_level'] + 0.01, len(audio) / fs
    assert core.listener.active and core.listen_timer is not None, 'listening must start after the answer'
    core.toggle_listen()                       # manual: stops the timed listening
    assert not core.listener.active
    core.toggle_listen()
    assert core.listener.active and core.listen_manual
    core.toggle_listen()
    assert not core.listener.active
    # HFPager message → listening to the station's reply; a beacon frame → no listening
    core.s.update(hfp_listen_after_tx=True, hfp_listen_after_tx_seconds=33)
    assert core.send(5, 'REPLY?') is None
    core._tx_thread.join(30)
    assert core.listener.active and core.listen_timer is not None, 'listening must start after an HFPager TX'
    core.toggle_listen()
    assert not core.listener.active
    assert core.send_hfp_beacon('BCN') is None
    core._tx_thread.join(30)
    assert not core.listener.active, 'no listening after a beacon frame'
    core.stop_rx()
    print('OK  answer on air: Kalinka once (%.2f s with PTT delay/tail) → then listening; manual «Слушать»'
          % (len(audio) / fs))
    core.s.update(ptt_method='RTS', ptt_port='COM3', sel_ext_port='COM3')
    core.ext_pulse(2)
    assert core.ext_conflict() and not core.ext.on
    core.s.update(sel_ext_port='COM9', rig_port='COM9')
    assert core.ext_conflict()
    core.s.update(rig_port='')
    assert not core.ext_conflict()
    print('OK  external device: the PTT / CAT port is refused, a separate port is accepted')
    for st in ('codan', 'vertex', 'beep', 'kalinka'):
        x = SE.answer_pattern(st, 8000, 0.5)
        assert 2.0 < len(x) / 8000 < 3.2 and np.abs(x).max() <= 0.5 + 1e-6, (st, len(x) / 8000)


def test_stage2(tmp):
    """HFPager CALL / BCN REQ, scenarios for both protocols, CW, beacon (frame type 0x06 decoded back)"""
    import cw as CWm
    core, q = make_core(tmp)
    core.fs = 48000
    FakeSD.played.clear()
    my = int(core.s['my_id'])
    fr = dict(kind='msg', b0=0x05, b1=0xA0, dest=my, sender=3, counter=1, text=b'call', speed='5.86', length=4,
              hdr_crc=0)
    core._on_frame(dict(fr), {})
    core._on_frame(dict(fr, counter=2, text=b'HELLO'), {})
    items = drain(q, 0.3)
    kinds = [i[0] for i in items]
    assert 'hfp_call' in kinds and 'hfp_msg_to_me' in kinds, kinds
    print('OK  HFPager: «CALL» to my ID → call event; other text → incoming-message event')

    core.s.update(bcn_req_enable=True, bcn_req_style='kalinka')
    core._on_frame(dict(fr, counter=3, text=b'BCN REQ', dest=0), {})        # to all: ignored
    time.sleep(3.0)
    assert not FakeSD.played and not core.tx_busy, 'BCN REQ to ID 0 must not be answered'
    core._on_frame(dict(fr, counter=4, text=b'BCN  req'), {})                  # to my ID
    t0 = time.time()
    while not FakeSD.played and time.time() - t0 < 6:
        time.sleep(0.1)
    if core._tx_thread:
        core._tx_thread.join(10)
    assert FakeSD.played, 'no melody after BCN REQ'
    audio, fs = FakeSD.played[-1]
    want = 16 * SE.KALINKA_QUARTER + core.s['ptt_delay'] + 0.3
    assert abs(len(audio) / fs - want) < 0.03, len(audio) / fs
    print('OK  BCN REQ to my ID → melody on air, %.2f s; to ID 0 → ignored' % (len(audio) / fs))

    ran = []
    core.run_actions_logged = lambda actions, why: ran.append(actions) or True
    core.s['scenarios'] = [dict(on=True, proto='hfp', trigger='QSY *', **{'from': '3'}, sel_from='', action='A {1}'),
                           dict(on=True, proto='sel', trigger='QSY *', **{'from': ''}, sel_from='0055',
                                action='B {1}'),
                           dict(on=True, proto='both', trigger='HOME', **{'from': ''}, sel_from='', action='C')]
    assert core.run_scenario('QSY 7.1', 3, proto='hfp') == 'A 7.1'
    assert core.run_scenario('QSY 7.1', '55', proto='sel') == 'B 7.1'          # 0055 == 55
    assert core.run_scenario('QSY 7.1', '56', proto='sel') is None
    assert core.run_scenario('QSY 7.1', 4, proto='hfp') is None
    assert core.run_scenario('HOME', '1234', proto='sel') == 'C' and core.run_scenario('HOME', 9) == 'C'
    print('OK  scenarios: protocol column, HFPager ID and Selcall ID columns')

    x = CWm.cw_audio('PARIS', 8000, wpm=20, tone=800, level=0.5, lead=0, tail=0)
    assert abs(len(x) / 8000 - 43 * 0.06) < 0.01, len(x) / 8000
    assert CWm.morse('SOS ПРИВЕТ') == '... --- ... / .--. .-. .. .-- . -'
    print('OK  CW: PARIS = 43 units at 20 WPM (2.58 s); Russian Morse')

    core.s.update(bcn_mode='times', bcn_times='12:00 06:30')
    noon = (datetime.datetime(2026, 1, 1, 12, 0, 10) - datetime.datetime(1970, 1, 1)).total_seconds()
    due, nxt = core.beacon_due(noon)
    assert due and nxt is not None
    core.bcn_minute = '2026-01-01 12:00'
    assert not core.beacon_due(noon)[0], 'the same minute must not repeat'
    core.s.update(bcn_mode='interval', bcn_interval=10)
    core.bcn_last = noon - 599
    assert not core.beacon_due(noon)[0] and core.beacon_due(noon + 2)[0]
    print('OK  beacon schedule: UTC times (once per minute) and interval')

    # beacon frame through the receiver
    assert core.start_rx()
    core.sel.stop()
    core.s.update(speed='23.44', bcn_kind='hfp_beacon', bcn_text='Beacon from RA4PVJ')
    FakeSD.played.clear()
    assert core.send_beacon() is None
    core._tx_thread.join(30)
    audio, fs = FakeSD.played[-1]
    gap = np.zeros(3 * fs, np.float32)
    push(core, np.concatenate([gap, audio, gap, gap]), fs)
    items = drain(q, 6.0)
    core.stop_rx()
    rx = [i for i in items if i[0] == 'rx']
    assert any(i[1]['b0'] == 0x06 and i[1]['text'] == b'Beacon from RA4PVJ' for i in rx), rx
    print('OK  HFPager beacon frame (type 0x06) transmitted and decoded back')


def test_stage3(tmp):
    """long HFPager preamble on TX, decoding when only the end of it is heard (scanning), the scanner"""
    core, q = make_core(tmp)
    # no listening after this TX: listening holds the scanner on its channel (tested below)
    core.s.update(speed='23.44', hfp_pre_seconds=12.0, ptt_delay=0.0, hfp_listen_after_tx=False)
    assert core.start_rx()
    core.sel.stop()
    fs = core.fs
    FakeSD.played.clear()
    assert core.send(3, 'LONG PRE') is None
    core._tx_thread.join(60)
    audio, _ = FakeSD.played[-1]
    want = A.Core.air_time('23.44', 8, 12.0)
    assert abs(len(audio) / fs - 0.3 - want) < 0.1, (len(audio) / fs, want)
    # heard from second 8 of the 12 s preamble (as when a scanning receiver lands on the channel)
    gap = np.zeros(3 * fs, np.float32)
    push(core, np.concatenate([gap, audio[8 * fs:], gap, gap]), fs)
    items = drain(q, 8.0)
    core.stop_rx()
    rx = [i for i in items if i[0] == 'rx']
    assert any(i[1]['text'] == b'LONG PRE' for i in rx), rx
    print('OK  preamble 12 s (standard 3.2 s at 23.44 Bd): %.1f s on air; decoded when heard from second 8'
          % (len(audio) / fs))

    # scanner with a fake CAT
    tuned = []
    core.rig.run_actions = lambda cfg, act: (tuned.append((time.time(), act)), [(act, True, 'ok')])[1]
    core.rig.read_freq = lambda cfg: 7185000
    core.s.update(rig_port='COM9', scan_resume=2.0, scan_channels=[
        dict(on=True, freq='7.100', mode='LSB', dwell=1.0), dict(on=False, freq='9.000', mode='USB', dwell=1.0),
        dict(on=True, freq='10.140', mode='USB', dwell=1.0), dict(on=True, freq='14.100', mode='USB', dwell=1.0)] +
        [dict(on=False, freq='', mode='USB', dwell=3.0)] * 4)
    # 3 channels of 1 s, retune not measured yet (0.2 s): back after 2 x 1.2 s -> preamble 2.4 + 2.3, dots >= 6
    assert core.preamble_for_scan() == 4.7 and core.dots_for_scan() == 6.0, (core.preamble_for_scan(),
                                                                           core.dots_for_scan())
    core.last_activity = 0.0
    assert core.start_scan() is None
    t0 = time.time()
    while len(tuned) < 3 and time.time() - t0 < 10:
        time.sleep(0.05)
    seq = [a for _t, a in tuned]
    assert seq[:3] == ['FRQ 7.100 LSB', 'FRQ 10.140 USB', 'FRQ 14.100 USB'], seq
    # activity on the current channel -> hold (dwell made long so the test is not timing-sensitive)
    for c in core.s['scan_channels'][:4]:
        c['dwell'] = 5.0
    t0 = time.time()
    while time.time() - t0 < 10 and not (core.scan_state == 'scan' and time.time() > core.scan_ignore_until + 0.1
                                         and time.time() - tuned[-1][0] < 3.0):
        time.sleep(0.05)
    core.last_activity = time.time()
    t0 = time.time()
    while core.scan_state != 'hold' and time.time() - t0 < 2:
        time.sleep(0.05)
    assert core.scan_state == 'hold', core.scan_state
    n = len(tuned)
    core.last_activity = time.time()
    time.sleep(1.0)
    assert len(tuned) == n, 'must stay on the channel while it is not quiet'
    t0 = time.time()                              # 2 s of silence -> resume
    while len(tuned) == n and time.time() - t0 < 6:
        time.sleep(0.05)
    assert len(tuned) > n and time.time() - t0 >= 0.8, (len(tuned), n, time.time() - t0)
    core.stop_scan()
    t0 = time.time()
    while core.scan_state != 'off' and time.time() - t0 < 8:
        time.sleep(0.05)
    assert core.scan_state == 'off'
    assert tuned[-1][1] == 'FRQ 7.18500', tuned[-1]           # back where the transceiver was before the scan
    assert core.scan_retune is not None and core.scan_retune < 0.1
    core.s['scan_channels'] = [dict(on=True, freq='7.1', mode='USB', dwell=1.0)] * 6 + \
        [dict(on=False, freq='', mode='USB', dwell=1.0)] * 2
    assert core.max_channels_for(6.0, A.SEL_DOTS_MARGIN) == 6 and core.dots_for_scan() == 6.0
    core.s['scan_channels'] = core.s['scan_channels'][:4] + [dict(on=False, freq='', mode='USB', dwell=3.0)] * 4
    for c in core.s['scan_channels'][:4]:
        c['dwell'] = 1.0
    assert core.start_scan() is None
    core.s['scan_channels'][2]['on'] = core.s['scan_channels'][3]['on'] = False
    t0 = time.time()
    while core.scan_on and time.time() - t0 < 8:
        time.sleep(0.05)
    assert not core.scan_on, 'fewer than 2 channels must stop the scan'
    print('OK  scanning: skips unticked channels, holds on activity, resumes after %.0f s of silence, stops and '
          'returns to 7.185 MHz; 6 channels of 1 s fit the CODAN 6 s dots' % core.s['scan_resume'])

    # channel buttons: tune channel i (stops the scan, no return), captions; 8 saved channels -> 6
    core.s['scan_channels'] = A.default_scan_channels()
    assert len(core.s['scan_channels']) == 6 and A.channel_caption(core.s['scan_channels'][1], 1) == '40m'
    assert A.channel_caption(dict(name='', freq='7.1'), 0) == '7.1' and A.channel_caption({}, 2) == '3'
    tuned.clear()
    assert core.tune_channel(2) is None
    t0 = time.time()
    while not tuned and time.time() - t0 < 5:
        time.sleep(0.05)
    time.sleep(0.2)
    assert tuned[-1][1] == 'FRQ 10.140 USB' and core.cur_channel == 2, (tuned, core.cur_channel)
    assert core.start_scan() is None
    time.sleep(0.3)
    tuned.clear()
    assert core.tune_channel(4) is None               # pressed during the scan: stop there, no return home
    t0 = time.time()
    while core.scan_on or (time.time() - t0 < 1.5 and not any('18.100' in a for _t, a in tuned)):
        time.sleep(0.05)
    assert tuned[-1][1] == 'FRQ 18.100 USB' and not any('7.18500' in a for _t, a in tuned), tuned
    core.save()
    import json
    cfg = json.load(open(A.SETTINGS_FILE, encoding='utf-8'))
    cfg['scan_channels'] = cfg['scan_channels'] + [dict(on=False, freq='', mode='USB', dwell=1.0)] * 2
    json.dump(cfg, open(A.SETTINGS_FILE, 'w', encoding='utf-8'))
    c2 = A.Core(queue.Queue(), sd_module=FakeSD)
    assert len(c2.s['scan_channels']) == 6 and c2.s['scan_channels'][4]['freq'] == '18.100'
    cfg['hfp_enable'] = cfg['sel_enable'] = False
    json.dump(cfg, open(A.SETTINGS_FILE, 'w', encoding='utf-8'))
    c3 = A.Core(queue.Queue(), sd_module=FakeSD)
    assert c3.s['hfp_enable'] is True and c3.s['sel_enable'] is True, 'decoders must be on at start'
    print('OK  channel buttons: tune / stop scan without return; captions; 8 saved channels -> 6 kept; '
          'decoders on at every start')

    # HFPager decoder off: the signal is seen (activity / spectrum) but nothing is decoded and no failure reported
    core.s.update(speed='23.44', hfp_pre_seconds=0.0)
    assert core.start_rx()
    core.sel.stop()
    core.set_hfp_decoder(False)
    FakeSD.played.clear()
    assert core.send(3, 'OFF TEST') is None
    core._tx_thread.join(60)
    audio, _ = FakeSD.played[-1]
    gap = np.zeros(3 * fs, np.float32)
    drain(q, 0.2)
    core.last_activity = 0.0
    push(core, np.concatenate([gap, audio, gap, gap]), fs)
    items = drain(q, 5.0)
    core.stop_rx()
    assert not [i for i in items if i[0] == 'rx'], 'decoder off must not decode'
    assert not [i for i in items if i[0] == 'event' and i[1] == 'fail']
    assert core.last_activity > 0, 'the signal must still count as activity (scanner)'
    core.set_hfp_decoder(True)
    core.save()
    print('OK  HFPager decoder off: signal seen, nothing decoded')


def test_scan_timing():
    """the numbers the scan formula is built on: detection 0.3 s after landing, Selcall from 0.3 s of dots"""
    import hfpager_modem as M
    import hfpager_rx as R
    fs = 48000
    rng = np.random.default_rng(3)
    for speed in ('5.86', '23.44'):
        ev = []
        eng = R.RxEngine(fs, lambda fr, i: None, lambda k, i: ev.append((eng._nblocks * 0.1, k, i)))
        with R.MODEM_LOCK:
            M.set_speed(speed)
            sig = M.synth(M.nibbles_to_tones([M.PRE_NIB] * int(6 * M.BAUD)), fs=fs, f0=1611.4, amp=0.003, lead=0,
                          tail=0).astype(np.float32)
        x = np.concatenate([np.zeros(6 * fs, np.float32), sig])
        x += (0.01 * rng.standard_normal(len(x))).astype(np.float32)       # -7 dB SNR in 3 kHz
        for i in range(0, len(x), 2400):
            eng.feed(x[i:i + 2400])
            eng.process_available()
        t = [tt - 6.0 for tt, k, i in ev if k == 'state' and i.get('state') == 'receiving' and tt > 6.0]
        assert t and t[0] <= 0.5, (speed, t)
    full = S.modulate(S.build_call('1234', '5678', None), fs, 6.0, S.F_CENTER, 0.3).astype(np.float32)
    x = np.concatenate([full[int(5.7 * fs):], np.zeros(3 * fs, np.float32)])
    x += (0.01 * rng.standard_normal(len(x))).astype(np.float32)
    assert [(c['from'], c['to']) for c in S.decode(SE.Downsampler(fs).push(x), 8000)] == [('5678', '1234')]
    print('OK  scan timing: preamble detected <= 0.5 s after landing (-7 dB SNR); Selcall decoded from 0.3 s of dots')


def test_auto_ack(tmp):
    """auto-ACK: sent with the standard preamble, after our own TX if busy, once per frame, again for a repeat"""
    c2, _q2 = make_core(tmp)
    c2.s.update(my_id='5', ack=True, speed='23.44', hfp_pre_seconds=0, ptt_delay=0.0, hfp_listen_after_tx=False)
    FakeSD.played.clear()
    assert c2.send(1234, 'HELLO') is None
    c2._tx_thread.join(30)
    audio, fs = FakeSD.played[-1]
    core, q = make_core(tmp)
    core.s.update(my_id='1234', auto_ack=True, ack=False, hfp_pre_seconds=12.0, hfp_ring_air=False,
                  bcn_req_enable=False, ptt_delay=0.0, hfp_listen_after_tx=False, hfp_listen_after_call=False)
    assert core.start_rx()
    FakeSD.played.clear()
    gap = np.zeros(2 * fs, np.float32)
    push(core, np.concatenate([gap, audio, gap, gap]), fs)
    items = drain(q, 6.0)
    rx = [i[1] for i in items if i[0] == 'rx']
    assert rx and rx[0]['b1'] & 0x02 and rx[0]['dest'] == 1234, rx
    assert [i for i in items if i[0] == 'tx_ack'], [i[0] for i in items]
    ack_len = len(FakeSD.played[-1][0]) / FakeSD.played[-1][1]
    assert ack_len < A.Core.air_time('23.44', 0, 12.0) - 5, ack_len   # standard preamble, not the 12 s one
    fr = rx[0]
    # the same frame twice at once -> one ACK; we are transmitting -> the ACK goes right after that TX
    FakeSD.played.clear()
    old_gap, A.ACK_REPEAT_GAP = A.ACK_REPEAT_GAP, 2.0
    try:
        core._acked.clear()
        core.tx_busy = True
        core._on_frame(fr, {})
        core._on_frame(fr, {})
        time.sleep(2.5)
        assert not FakeSD.played, 'no ACK while transmitting'
        core.tx_busy = False
        t0 = time.time()
        while not FakeSD.played and time.time() - t0 < 5:
            time.sleep(0.1)
        core._tx_thread.join(30)
        assert len(FakeSD.played) == 1, len(FakeSD.played)
        # the sender repeats (it did not hear our ACK) -> confirmed again
        time.sleep(0.5)
        core._on_frame(fr, {})
        t0 = time.time()
        while len(FakeSD.played) < 2 and time.time() - t0 < 6:
            time.sleep(0.1)
        core._tx_thread.join(30)
        assert len(FakeSD.played) == 2, len(FakeSD.played)
    finally:
        A.ACK_REPEAT_GAP = old_gap
        core.stop_rx()
    print('OK  auto-ACK: standard preamble (%.1f s), waits for our TX, once per frame, again for a repeat' % ack_len)


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp:
        test_scan_timing()
        test_stage3(tmp)
        test_stage2(tmp)
        test_selcall_tx(tmp)
        test_real_recording(tmp)
        test_both_receivers(tmp)
        test_selcall_03x(tmp)
        test_answer_listen_ext(tmp)
        test_auto_ack(tmp)
    print('ALL OK')
