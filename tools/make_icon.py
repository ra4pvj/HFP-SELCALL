"""Draws the program icon (no image libraries needed): icon.png 256x256 and icon.ico (PNG inside ICO).

    python tools/make_icon.py
"""
import os
import struct
import zlib

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def png_bytes(rgba):
    h, w, _ = rgba.shape
    raw = b''.join(b'\x00' + rgba[y].tobytes() for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def draw(n=256, ss=4):
    """supersampled drawing -> antialiased RGBA"""
    N = n * ss
    y, x = np.mgrid[0:N, 0:N].astype(np.float32) / ss
    img = np.zeros((N, N, 4), np.float32)

    def put(mask, rgb, a=1.0):
        for i in range(3):
            img[..., i] = np.where(mask, rgb[i] * a + img[..., i] * (1 - a), img[..., i])
        img[..., 3] = np.where(mask, np.maximum(img[..., 3], a), img[..., 3])

    # rounded square, dark gradient
    r, m = 44, 8
    cx = np.clip(x, m + r, n - m - r)
    cy = np.clip(y, m + r, n - m - r)
    body = (x - cx) ** 2 + (y - cy) ** 2 <= r * r
    g = 0.10 + 0.10 * (1 - y / n)
    for i, k in enumerate((0.55, 0.75, 1.0)):
        img[..., i] = np.where(body, g * k, 0)
    img[..., 3] = body.astype(np.float32)
    # radio waves from the antenna tip
    ax, ay = n * 0.5, n * 0.36
    d = np.hypot(x - ax, y - ay)
    ang = np.degrees(np.arctan2(y - ay, x - ax))
    side = (np.abs(ang) < 50) | (np.abs(ang) > 130)
    for rad, w in ((30, 7), (56, 7), (82, 7)):
        put(body & side & (np.abs(d - rad) < w / 2), (0.22, 1.0, 0.22))
    # mast and base (tower)
    put(body & (np.abs(x - ax) < 5) & (y > ay) & (y < n * 0.82), (0.85, 0.95, 0.85))
    t = (y - ay) / (n * 0.82 - ay)
    legs = (y > ay) & (y < n * 0.82) & (np.abs(np.abs(x - ax) - t * n * 0.17) < 3.5)
    put(body & legs, (0.85, 0.95, 0.85))
    put(body & (np.hypot(x - ax, y - ay) < 11), (1.0, 0.25, 0.2))
    # "segment" bar at the bottom (the clock / level look)
    for i, col in enumerate(((0.18, 0.8, 0.25), (0.18, 0.8, 0.25), (0.18, 0.8, 0.25), (0.95, 0.77, 0.06),
                             (0.9, 0.3, 0.24))):
        x0 = n * 0.24 + i * n * 0.105
        put(body & (x > x0) & (x < x0 + n * 0.085) & (y > n * 0.86) & (y < n * 0.9), col)
    small = img.reshape(n, ss, n, ss, 4).mean(axis=(1, 3))
    return (np.clip(small, 0, 1) * 255).astype(np.uint8)


def main():
    big = draw(256)
    png = png_bytes(big)
    open(os.path.join(ROOT, 'icon.png'), 'wb').write(png)
    # ICO with PNG images (Windows Vista+): 256, 48, 32, 16
    imgs = [png] + [png_bytes(draw(s, ss=8)) for s in (48, 32, 16)]
    sizes = [256, 48, 32, 16]
    head = struct.pack('<HHH', 0, 1, len(imgs))
    off = 6 + 16 * len(imgs)
    ents = b''
    for s, data in zip(sizes, imgs):
        ents += struct.pack('<BBBBHHII', s % 256, s % 256, 0, 0, 1, 32, len(data), off)
        off += len(data)
    open(os.path.join(ROOT, 'icon.ico'), 'wb').write(head + ents + b''.join(imgs))
    print('icon.png, icon.ico')


if __name__ == '__main__':
    main()
