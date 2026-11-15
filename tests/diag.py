import sys, numpy as np
sys.path.insert(0, '.')
import selcall as S, selcall_engine as SE
print('numpy', np.__version__, 'LUT', S.SYM_LUT.dtype)
x, fs = S.read_wav('testdata/SELCALL_from_1111_to_1234.wav')
x48 = np.interp(np.arange(int(len(x) * 48000 / fs)) * fs / 48000, np.arange(len(x)), x).astype(np.float32)
for name, d8 in (('44k', SE.Downsampler(fs).push(x)), ('48k', SE.Downsampler(48000).push(x48)),
                 ('48k64', SE.Downsampler(48000).push(x48.astype(np.float64)))):
    d = np.asarray(d8, np.float64)
    print(name, d8.dtype, len(d), 'rms %.5f' % np.sqrt(np.mean(d * d)), 'sum %.6f' % d.sum(), 'first', d[1000:1003])
    print('  centers', S.estimate_centers(d, 8000))
    td = S.tone_diff(d, 8000, 1785.0)
    print('  td', td.dtype, '%.6f %.6f' % (td.mean(), np.abs(td).mean()))
    for ph in np.arange(0, 80, 10.0):
        idx = (ph + np.arange(int((len(td) - ph) / 80)) * 80).astype(int)
        bits = (td[idx] > 0).astype(np.uint8)
        print('   ph', ph, len(idx), int(bits.sum()), len(S._find_calls_in_bits(bits)))
    print('  decode', [S.fmt_call(c) for c in S.decode(d, 8000)])
