# Patcher
Patcher for FUComplete.

Windows only for now (works with wine too), only works when built with [pyinstaller](https://github.com/pyinstaller/pyinstaller) due to paths, to build use:
```
pyinstaller.exe --upx-dir="c:\\upx" --clean --win-private-assemblies --onefile --add-binary "UMD-replace.exe;bin" --add-binary "xdelta3.exe;bin" patcher.py
```

Requirements:
- Python 3.6+
- [pycdlib](https://github.com/clalancette/pycdlib)
- This [mhef](https://github.com/IncognitoMan/mhef) fork
- [UMD-Replace](https://www.romhacking.net/utilities/891/)
- [xdelta3](https://github.com/jmacd/xdelta)
