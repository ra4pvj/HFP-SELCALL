# PyInstaller spec for a macOS .app bundle:  pyinstaller --noconfirm hfp_selcall_mac.spec
from PyInstaller.utils.hooks import collect_all
datas, binaries, hiddenimports = collect_all('sounddevice')
a = Analysis(['hfp_selcall_app.py'], pathex=['.'], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports + ['hfpager_modem', 'hfpager_rx', 'hfpager_ptt', 'hfpager_rig',
                                            'selcall', 'selcall_engine', 'serial', 'serial.tools.list_ports'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='HFPSelcallApp', console=False)
coll = COLLECT(exe, a.binaries, a.datas, name='HFPSelcallApp')
app = BUNDLE(coll, name='HFPSelcallApp.app', bundle_identifier='local.hfpselcall.app',
             info_plist={'NSMicrophoneUsageDescription':
                         'Приложение принимает сигналы HFPager и Selcall со звукового входа.',
                         'NSHighResolutionCapable': True})
