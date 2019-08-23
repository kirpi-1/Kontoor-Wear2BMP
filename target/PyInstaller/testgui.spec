# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['E:\\Project\\Webapp\\src\\main\\python\\main.py'],
             pathex=['E:\\Project\\Webapp\\target\\PyInstaller'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['c:\\users\\darren\\.conda\\envs\\pytorch\\lib\\site-packages\\fbs\\freeze\\hooks'],
             runtime_hooks=['C:\\Users\\Darren\\AppData\\Local\\Temp\\tmpuvrr3aav\\fbs_pyinstaller_hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=True)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [('v', None, 'OPTION')],
          exclude_binaries=True,
          name='testgui',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True , icon='E:\\Project\\Webapp\\src\\main\\icons\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='testgui')
