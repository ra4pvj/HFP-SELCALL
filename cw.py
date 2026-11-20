"""Morse (CW) audio for the beacon: Latin, digits, punctuation and Russian letters (Russian Morse table).

    audio = cw_audio('RA4PVJ BCN', fs=48000, wpm=20, tone=800, level=0.5)
"""
import numpy as np

LATIN = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....', 'I': '..',
    'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6': '-....',
    '7': '--...', '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    '/': '-..-.', '=': '-...-', '-': '-....-', '+': '.-.-.', '@': '.--.-.', ':': '---...', '(': '-.--.',
    ')': '-.--.-', '!': '-.-.--', "'": '.----.', '"': '.-..-.',
}
# Russian Morse (the Latin equivalents where they exist)
RUSSIAN = {
    'А': '.-', 'Б': '-...', 'В': '.--', 'Г': '--.', 'Д': '-..', 'Е': '.', 'Ё': '.', 'Ж': '...-', 'З': '--..',
    'И': '..', 'Й': '.---', 'К': '-.-', 'Л': '.-..', 'М': '--', 'Н': '-.', 'О': '---', 'П': '.--.', 'Р': '.-.',
    'С': '...', 'Т': '-', 'У': '..-', 'Ф': '..-.', 'Х': '....', 'Ц': '-.-.', 'Ч': '---.', 'Ш': '----',
    'Щ': '--.-', 'Ъ': '--.--', 'Ы': '-.--', 'Ь': '-..-', 'Э': '..-..', 'Ю': '..--', 'Я': '.-.-',
}
TABLE = dict(LATIN, **RUSSIAN)


def morse(text):
    """'SOS' -> '... --- ...'; unknown characters are skipped; words separated by ' / '"""
    words = []
    for w in str(text).upper().split():
        codes = [TABLE[c] for c in w if c in TABLE]
        if codes:
            words.append(' '.join(codes))
    return ' / '.join(words)


def cw_audio(text, fs, wpm=20, tone=800.0, level=0.5, lead=0.0, tail=0.3):
    """keyed sine tone with 5 ms raised-cosine edges (no key clicks); PARIS timing: dot = 1.2 / wpm s"""
    dot = 1.2 / max(5.0, min(60.0, float(wpm)))
    n_dot = int(round(dot * fs))
    r = max(1, int(0.005 * fs))
    edge = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, r))

    def on(units):
        n = units * n_dot
        t = np.arange(n) / fs
        env = np.ones(n)
        env[:r] = edge[:n] if n < r else edge
        env[-r:] = np.minimum(env[-r:], edge[::-1][:len(env[-r:])])
        return (level * env * np.sin(2 * np.pi * float(tone) * t)).astype(np.float32)

    def off(units):
        return np.zeros(units * n_dot, np.float32)

    parts = [np.zeros(int(lead * fs), np.float32)]
    words = morse(text).split(' / ')
    for wi, w in enumerate(words):
        if not w:
            continue
        for ci, code in enumerate(w.split(' ')):
            for si, sym in enumerate(code):
                parts.append(on(1 if sym == '.' else 3))
                if si < len(code) - 1:
                    parts.append(off(1))
            if ci < len(w.split(' ')) - 1:
                parts.append(off(3))
        if wi < len(words) - 1:
            parts.append(off(7))
    parts.append(np.zeros(int(tail * fs), np.float32))
    return np.concatenate(parts)
