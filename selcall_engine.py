"""
HF Selcall (CCIR 493-4, CODAN-compatible) for the combined HFP+SELCALL app: non-GUI part.

Taken from ra4pvj/SELCALL (windows/hfselcall_win.py), reorganised so the Selcall receiver can share
one sound-card input stream with the HFPager receiver:

    eng = SelcallEngine(fs_in, on_call, on_event)
    eng.start()
    eng.feed(block)          # from the audio callback, any sample rate (resampled to 8 kHz here)
    eng.mute(True/False)     # during own transmission
    eng.stop()

The codec itself is selcall.py (unchanged copy from ra4pvj/SELCALL/python/selcall.py).
"""
import queue
import threading
import time

import numpy as np

import selcall as S

RX_FS = 8000
MAX_MSG = S.MAX_MSG

TRANSLIT = dict(zip("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя№",
                    ["A", "B", "V", "G", "D", "E", "E", "ZH", "Z", "I", "J", "K", "L", "M", "N", "O", "P",
                     "R", "S", "T", "U", "F", "H", "C", "CH", "SH", "SCH", "", "Y", "", "E", "YU", "YA",
                     "a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "j", "k", "l", "m", "n", "o", "p",
                     "r", "s", "t", "u", "f", "h", "c", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "N"]))

RING_STYLES = [("codan", "Двухтональный (как CODAN)"), ("vertex", "Трель (как Vertex)"),
               ("beep", "Короткие гудки")]


def translit(s):
    return "".join(TRANSLIT.get(ch, ch) for ch in s)


def digits(s):
    return "".join(ch for ch in str(s) if ch.isdigit())


def same_id(a, b):
    """CODAN IDs are compared with leading zeros (1234 == 001234)"""
    a, b = digits(a), digits(b)
    if not a or not b:
        return False
    n = max(len(a), len(b))
    return a.zfill(n) == b.zfill(n)


# ============================================================================ resampling
def lowpass_taps(fs, cutoff, n=127):
    m = np.arange(n) - (n - 1) / 2
    h = np.sinc(2 * cutoff / fs * m) * np.blackman(n)
    return h / h.sum()


class Downsampler:
    """Stream fs_in -> 8000 Hz: 3.4 kHz low-pass + fractional decimation."""

    def __init__(self, fs_in):
        self.fs_in = float(fs_in)
        self.ratio = self.fs_in / RX_FS
        self.taps = lowpass_taps(self.fs_in, 3400.0) if self.ratio > 1.001 else None
        self.hist = np.zeros(0 if self.taps is None else len(self.taps) - 1)
        self.pos = 0.0          # position of the next output sample in the input stream
        self.consumed = 0       # input samples already filtered

    def push(self, x):
        x = np.asarray(x, dtype=np.float64)
        if self.taps is None:
            return x.astype(np.float32)
        z = np.concatenate((self.hist, x))
        y = np.convolve(z, self.taps, mode="valid")          # len(y) == len(x)
        self.hist = z[-(len(self.taps) - 1):]
        start = self.consumed
        self.consumed += len(y)
        idx = np.arange(self.pos, self.consumed - 1, self.ratio)
        if len(idx) == 0:
            return np.zeros(0, dtype=np.float32)
        self.pos = idx[-1] + self.ratio
        out = np.interp(idx - start, np.arange(len(y)), y)
        return out.astype(np.float32)


# ============================================================================ receiver
class SelcallEngine:
    """Streaming Selcall receiver.  on_call(call_dict, unix_time) runs in the worker thread;
    on_event(kind, info) gets ('centers', [Hz...]) and ('error', {'text': ...})."""

    PERIOD = 1.0            # decoder runs once a second over a 25 s sliding window

    def __init__(self, fs_in, on_call, on_event=None, afc=True, fixed_center=S.F_CENTER):
        self.fs_in = fs_in
        self.on_call = on_call
        self.on_event = on_event or (lambda kind, info: None)
        self.afc = afc
        self.fixed_center = float(fixed_center)
        self.down = Downsampler(fs_in)
        self.rx = S.StreamReceiver(RX_FS)
        self.audio_q = queue.Queue()
        self._muted = False
        self._mute_until = 0.0
        self._stop = False
        self._thread = None
        self.t0 = time.time()

    def start(self):
        self._stop = False
        self.rx.reset()
        self.t0 = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop = True

    def mute(self, on, hold=0.5):
        """silence the input during own transmission (and `hold` seconds after it)"""
        self._muted = bool(on)
        if not on:
            self._mute_until = time.time() + hold

    def feed(self, x):
        """called from the audio callback; must be cheap"""
        y = self.down.push(x)
        if self._muted or time.time() < self._mute_until:
            y = np.zeros_like(y)
        self.audio_q.put_nowait(y)

    def process_now(self, flush=False):
        """move queued audio into the decoder and run it once (also used by tests)"""
        while True:
            try:
                self.rx.append(self.audio_q.get_nowait())
            except queue.Empty:
                break
        self.rx.fixed_center = None if self.afc else self.fixed_center
        calls = self.rx.process(flush=flush)
        self.on_event('centers', list(self.rx.last_centers))
        for c in calls:
            self.on_call(c, self.t0 + c["time"])
        return calls

    def _loop(self):
        while not self._stop:
            time.sleep(self.PERIOD)
            if self._stop:
                break
            try:
                self.process_now()
            except Exception as ex:
                self.on_event('error', {'text': 'Ошибка декодера Selcall: %s' % ex})


# ============================================================================ transmitter
def prepare_text(message, use_translit=True):
    if not message:
        return None
    text = translit(message) if use_translit else message
    return text[:MAX_MSG]


def build_audio(to_id, my_id, message, fs, dot_seconds=6.0, level=0.5, lead=0.5, tail=0.3,
                use_translit=True, center=S.F_CENTER):
    """returns (text actually sent, float32 audio with leading/trailing silence)"""
    text = prepare_text(message, use_translit)
    stream = S.build_call(digits(to_id), digits(my_id), text)
    y = S.modulate(stream, fs, float(dot_seconds), float(center), float(level))
    pre = np.zeros(int(max(0.0, lead) * fs), dtype=np.float32)
    post = np.zeros(int(max(0.0, tail) * fs), dtype=np.float32)
    return text or "", np.concatenate((pre, y, post)).astype(np.float32)


def check_ids(my_id, to_id):
    """returns error text or None"""
    me, to = digits(my_id), digits(to_id)
    if not me or not to:
        return "Укажите цифровые Selcall ID: свой и получателя (4 или 6 цифр)."
    if len(me) > 10 or len(to) > 10:
        return "Selcall ID: не больше 10 цифр (обычно 4 или 6)."
    return None


def air_time(dot_seconds, my_id, to_id, message, use_translit=True):
    """seconds on air (dot preamble + frame), without PTT delay"""
    text = prepare_text(message, use_translit)
    stream = S.build_call(digits(to_id) or "0", digits(my_id) or "0", text)
    ndots = int(float(dot_seconds) * S.BAUD) // 2 * 2
    return (ndots + 10 * len(stream)) / S.BAUD


def decode_file(path, afc=True, fixed_center=S.F_CENTER):
    x, fs = S.read_wav(path)
    if fs != RX_FS:
        x = Downsampler(fs).push(x)
    return S.decode(x, RX_FS, None if afc else float(fixed_center))


# ============================================================================ ring
def ring_pattern(style, fs, volume):
    out = []

    def tone(f, sec):
        n = int(sec * fs)
        t = np.arange(n) / fs
        w = np.ones(n)
        r = max(1, int(0.004 * fs))
        w[:r] = np.linspace(0, 1, r)
        w[-r:] = np.linspace(1, 0, r)
        out.append(volume * w * np.sin(2 * np.pi * f * t))

    def silence(sec):
        out.append(np.zeros(int(sec * fs)))

    if style == "vertex":
        for _ in range(2):
            for _ in range(10):
                tone(1500, 0.025)
                tone(2000, 0.025)
            silence(0.2)
        silence(1.4)
    elif style == "beep":
        for _ in range(3):
            tone(1200, 0.15)
            silence(0.1)
        silence(1.0)
    else:
        for _ in range(5):
            tone(1000, 0.08)
            tone(1300, 0.08)
        silence(1.0)
    return np.concatenate(out).astype(np.float32)


class Ringer:
    """Plays the ring pattern in a loop on its own OutputStream (does not touch sd.play(), which the
    transmitter uses).  Stops by itself after `seconds`."""

    def __init__(self, sd_module):
        self.sd = sd_module
        self.stream = None
        self.timer = None
        self.lock = threading.Lock()

    def start(self, device, style, volume, seconds):
        """returns error text or None"""
        self.stop()
        if self.sd is None:
            return 'звуковая библиотека недоступна'
        try:
            fs = int(self.sd.query_devices(device, 'output')['default_samplerate'])
        except Exception:
            fs = 48000
        pat = ring_pattern(style, fs, float(volume))
        pos = [0]

        def cb(outdata, frames, t, status):
            n = len(outdata)
            idx = (np.arange(n) + pos[0]) % len(pat)
            outdata[:, 0] = pat[idx]
            pos[0] = (pos[0] + n) % len(pat)
        try:
            with self.lock:
                self.stream = self.sd.OutputStream(samplerate=fs, device=device, channels=1, dtype='float32',
                                                   callback=cb)
                self.stream.start()
        except Exception as ex:
            self.stream = None
            return str(ex)
        self.timer = threading.Timer(float(seconds), self.stop)
        self.timer.daemon = True
        self.timer.start()
        return None

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        with self.lock:
            st, self.stream = self.stream, None
        if st is not None:
            try:
                st.abort()
                st.close()
            except Exception:
                pass

    @property
    def active(self):
        return self.stream is not None
