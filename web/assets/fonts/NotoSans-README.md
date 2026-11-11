# Offline Noto interface fonts

- `NotoSans.ttf`: unchanged copy of the supplied `NotoSans/NotoSans-VariableFont_wdth,wght.ttf`. Variable weight 100–900, normal width 100; the interface requests Medium (500).
- `NotoSansCJKsc-Medium.otf`: unchanged official Noto Sans CJK SC Medium (weight 500), downloaded from https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Medium.otf on 2026-11-10.

The supplied Latin font has no Chinese glyphs. The companion provides Chinese (including the editor's Chinese captions) rather than letting the OS choose an unrelated font. Both are loaded locally; no installed fonts or runtime network requests are needed. The variable font also preserves stronger heading weights in the native interface. Hex/code displays retain their monospace Latin font, with the same CJK companion for Chinese.

Licenses: `NotoSans-OFL.txt` is copied from the supplied `NotoSans/OFL.txt`; `NotoSansCJK-OFL.txt` is copied from https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE. Copyright notices are also embedded in the unchanged font name tables.

Native registration is in `native_fonts.py`; browser faces and Medium defaults are in `web/styles.css`. `scripts/build_desktop.py` explicitly packages both fonts and their notices, without including browser icon/font assets. Do not subset these fonts to only current captions: names and bilingual user text also need coverage.

The native interface uses an 11pt Medium body. Heading and icon sizes are set independently of the typeface. Font loading never scales the body based on a previously opened window's application font.
