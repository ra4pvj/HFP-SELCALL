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

RING_STYLES = [("codan", "Двухтональный"), ("vertex", "Трель"),
               ("beep", "Короткие гудки"), ("kalinka", "Мелодия «Калинка»")]
ANSWER_SECONDS = 2.5        # ответ в эфир тонами: 2,5 с (мелодия звучит целиком один раз)

# Начало припева «Калинки» (И. Ларионов, 1860; общественное достояние) по нотам, на октаву выше записи:
# E5 | D5 B4 C5 | D5 B4 C5 | D5 C5 B4 | A4 (частота, Гц; длительность в четвертях). 16 четвертей ≈ 2,9 с.
_E5, _D5, _C5, _B4, _A4 = 659.26, 587.33, 523.25, 493.88, 440.0
KALINKA_QUARTER = 0.18
KALINKA = [(_E5, 2),
           (_D5, 2), (_B4, 1), (_C5, 1),
           (_D5, 2), (_B4, 1), (_C5, 1),
           (_D5, 2), (_C5, 1), (_B4, 1),
           (_A4, 2)]


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

    if style == "kalinka":
        for f, n in KALINKA:
            dur = n * KALINKA_QUARTER
            m = int((dur - 0.015) * fs)
            t = np.arange(m) / fs
            env = (np.minimum(1, t / 0.006) * np.exp(-1.2 * t / dur) *
                   np.minimum(1, (m - 1 - np.arange(m)) / (0.006 * fs)))
            out.append(volume * env * (0.85 * np.sin(2 * np.pi * f * t) + 0.15 * np.sin(4 * np.pi * f * t)))
            silence(0.015)
        silence(0.8)
    elif style == "vertex":
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


def answer_pattern(style, fs, volume):
    """Сигнал ответа в эфир: мелодия — один раз без паузы; тоны — 2,5 с, конец плавно гасится."""
    x = ring_pattern(style, fs, volume)
    if style == "kalinka":
        return x[:max(0, len(x) - int(0.8 * fs))]
    n = int(ANSWER_SECONDS * fs)
    y = np.tile(x, n // len(x) + 1)[:n].copy()
    f = min(n, int(0.02 * fs))
    if f:
        y[-f:] *= np.linspace(1, 0, f)
    return y.astype(np.float32)


class Ringer:
    """Plays the ring pattern in a loop on its own OutputStream (does not touch sd.play(), which the
    transmitter uses).  Stops by itself after `seconds`."""

    def __init__(self, sd_module):
        self.sd = sd_module
        self.stream = None
        self.timer = None
        self.lock = threading.Lock()

    def start(self, device, style, volume, seconds, answer=False):
        """returns error text or None.  answer=True: play the answer signal once (preview, not on air)"""
        self.stop()
        if self.sd is None:
            return 'звуковая библиотека недоступна'
        try:
            fs = int(self.sd.query_devices(device, 'output')['default_samplerate'])
        except Exception:
            fs = 48000
        if answer:
            pat = np.concatenate((answer_pattern(style, fs, float(volume)), np.zeros(int(0.2 * fs), np.float32)))
            seconds = len(pat) / fs
        else:
            pat = ring_pattern(style, fs, float(volume))
        pos = [0]

        def cb(outdata, frames, t, status):
            n = len(outdata)
            if answer:
                chunk = pat[pos[0]:pos[0] + n]
                outdata[:, 0] = 0
                outdata[:len(chunk), 0] = chunk
                pos[0] += n
                return
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


# ============================================================================ listening to the air
class Listener:
    """Input audio to a loudspeaker for a while (to hear a voice message after a Selcall, or the
    station's reply after our own call).  feed() is called from the input callback."""

    def __init__(self, sd_module):
        self.sd = sd_module
        self.stream = None
        self.buf = queue.Queue(maxsize=50)
        self.fs_in = 48000
        self.fs_out = 48000
        self.level = 1.0
        self.lock = threading.Lock()
        self._rest = np.zeros(0, np.float32)

    @property
    def active(self):
        return self.stream is not None

    def start(self, device, fs_in, level=1.0):
        """returns error text or None"""
        self.stop()
        if self.sd is None:
            return 'звуковая библиотека недоступна'
        self.fs_in, self.level = int(fs_in), float(level)
        self._rest = np.zeros(0, np.float32)
        last = None
        for fs in (self.fs_in, 48000, 44100):
            try:
                st = self.sd.OutputStream(samplerate=fs, device=device, channels=1, dtype='float32',
                                          callback=self._cb)
                self.fs_out = fs
                st.start()
                with self.lock:
                    self.stream = st
                return None
            except Exception as ex:
                last = ex
        return str(last)

    def feed(self, x):
        if self.stream is None:
            return
        y = np.asarray(x, np.float32) * self.level
        if self.fs_out != self.fs_in:
            n = int(len(y) * self.fs_out / self.fs_in)
            y = np.interp(np.arange(n, dtype=np.float64) * self.fs_in / self.fs_out,
                          np.arange(len(y), dtype=np.float64), y).astype(np.float32)
        try:
            self.buf.put_nowait(y)
        except queue.Full:
            pass

    def _cb(self, outdata, frames, t, status):
        out = self._rest
        while len(out) < frames:
            try:
                out = np.concatenate((out, self.buf.get_nowait()))
            except queue.Empty:
                break
        n = min(frames, len(out))
        outdata[:, 0] = 0
        outdata[:n, 0] = out[:n]
        self._rest = out[n:][-int(self.fs_out):]          # never more than 1 s behind

    def stop(self):
        with self.lock:
            st, self.stream = self.stream, None
        if st is not None:
            try:
                st.abort()
                st.close()
            except Exception:
                pass
        while True:
            try:
                self.buf.get_nowait()
            except queue.Empty:
                break


# ============================================================================ external device
EXT_LINES = ["RTS", "DTR", "RTS+DTR"]


class ExtControl:
    """External device (siren, lamp, relay): "1" on RTS/DTR of a separate COM port."""

    def __init__(self, serial_module):
        self.serial = serial_module
        self.ser = None
        self.port = ""
        self.on = False
        self.lock = threading.Lock()

    def _open(self, port, line, invert):
        if self.ser is not None and self.port == port:
            return
        self._close_locked(line, invert)
        if self.serial is None:
            raise RuntimeError("pyserial недоступен")
        if not port:
            raise RuntimeError("не выбран COM-порт внешнего устройства")
        s = self.serial.Serial()
        s.port = port
        s.baudrate = 9600
        s.rts = bool(invert) if line in ("RTS", "RTS+DTR") else False   # level before open()
        s.dtr = bool(invert) if line in ("DTR", "RTS+DTR") else False
        s.open()
        self.ser, self.port = s, port

    def set(self, on, port, line, invert):
        """returns error text or None"""
        with self.lock:
            try:
                self._open(port, line, invert)
                level = bool(on) != bool(invert)
                if line in ("RTS", "RTS+DTR"):
                    self.ser.rts = level
                if line in ("DTR", "RTS+DTR"):
                    self.ser.dtr = level
                self.on = bool(on)
                return None
            except Exception as ex:
                self.on = False
                return "Внешнее устройство: %s" % ex

    def _close_locked(self, line, invert):
        if self.ser is not None:
            try:
                if line in ("RTS", "RTS+DTR"):
                    self.ser.rts = bool(invert)
                if line in ("DTR", "RTS+DTR"):
                    self.ser.dtr = bool(invert)
                self.ser.close()
            except Exception:
                pass
        self.ser, self.port, self.on = None, "", False

    def close(self, line="RTS+DTR", invert=False):
        with self.lock:
            self._close_locked(line, invert)
