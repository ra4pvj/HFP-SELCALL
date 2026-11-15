"""
Headless check of HFP+SELCALL (no sound card, no GUI):
  1. one input stream feeds both receivers: an HFPager frame and a Selcall call in the same audio
     are both decoded;
  2. the Selcall transmitter (through Core.send_selcall and the common _tx_run) produces audio that
     the Selcall decoder reads back, with PTT/RX-pause handled;
  3. the real CODAN recording from ra4pvj/SELCALL is decoded through the shared stream.

    python tests/test_combined.py
"""
import os
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


class FakeSD:
    """just enough of sounddevice for Core"""
    streams = []
    played = []
    InputStream = FakeStream
    OutputStream = FakeStream

    @staticmethod
    def check_input_settings(**kw):
        if kw.get('samplerate') != 48000:
            raise ValueError('only 48 kHz here')

    @staticmethod
    def query_devices(*a, **kw):
        return {'default_samplerate': 48000}

    @staticmethod
    def query_hostapis():
        return []

    @classmethod
    def play(cls, audio, fs, device=None):
        cls.played.append((np.asarray(audio).copy(), fs))

    @staticmethod
    def wait():
        pass

    @staticmethod
    def stop():
        pass


def push(core, x, fs, block=0.05):
    cb = FakeSD.streams[-1].callback
    n = int(block * fs)
    sel = core.sel
    done = 0
    for i in range(0, len(x), n):
        b = x[i:i + n].astype(np.float32)
        cb(b.reshape(-1, 1), len(b), None, None)
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
    x = np.interp(np.arange(int(len(x) * fs / fs_w)) * fs_w / fs, np.arange(len(x)), x).astype(np.float32)
    x = np.concatenate([x, np.zeros(3 * fs, dtype=np.float32)])
    push(core, x, fs)
    core.sel.process_now(flush=True)
    items = drain(q, 2.0)
    core.stop_rx()
    srx = [i for i in items if i[0] == 'sel_rx']
    assert any(i[1]['from'] == '1111' and i[1]['to'] == '1234' and i[3] for i in srx), srx
    print('OK  real CODAN recording: 1111→1234 decoded through the shared input (resampled to 48 kHz)')


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp:
        test_selcall_tx(tmp)
        test_real_recording(tmp)
        test_both_receivers(tmp)
    print('ALL OK')
