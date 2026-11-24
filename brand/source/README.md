# Brand kit generator

`gen.py` makes every file in `brand/logo/`, `brand/favicon/` and `brand/social/` from Roboto Mono, with the text
turned into outlines so the SVGs don't depend on any installed font. It isn't part of the site and is only run by
hand when the brand changes, so neither its dependencies nor the font are in the repository.

## What it needs

- **The font:** Roboto Mono from [Fontsource](https://fontsource.org/fonts/roboto-mono), npm package
  `@fontsource/roboto-mono` 5.3.0 (SIL Open Font License 1.1). The script reads
  `package/files/roboto-mono-latin-500-normal.woff2` and `…-700-normal.woff2` from this folder, where the package's
  tarball unpacks.
- **Python 3.12** with fonttools 4.67.0, brotli 1.2.0 (fonttools needs it to read WOFF2), CairoSVG 2.9.1 and
  Pillow 13.0.0.
- **Cairo**, the system library CairoSVG draws with: `brew install cairo` on macOS, `sudo apt install libcairo2`
  on Ubuntu. On Windows, through [MSYS2](https://www.msys2.org/): `winget install MSYS2.MSYS2`, then
  `pacman -S mingw-w64-ucrt-x86_64-cairo` in the "MSYS2 UCRT64" shell, which puts `libcairo-2.dll` in
  `C:\msys64\ucrt64\bin`.

## Running it

From the repository root:

```bash
curl -sL https://registry.npmjs.org/@fontsource/roboto-mono/-/roboto-mono-5.3.0.tgz | tar -xz -C brand/source
python3.12 -m venv brand/source/.venv
brand/source/.venv/bin/pip install fonttools==4.67.0 brotli==1.2.0 cairosvg==2.9.1 pillow==13.0.0
brand/source/.venv/bin/python brand/source/gen.py
```

On a Mac where CairoSVG can't find Homebrew's Cairo, put `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` in front of
the last command. If anything is missing, the script says what before generating anything.

On Windows, in Git Bash, the virtualenv's programs are in `Scripts/` rather than `bin/`, Python 3.12 is
`py -3.12`, and MSYS2's Cairo goes on the `PATH` for the last command only:

```bash
py -3.12 -m venv brand/source/.venv
brand/source/.venv/Scripts/pip install fonttools==4.67.0 brotli==1.2.0 cairosvg==2.9.1 pillow==13.0.0
PATH="/c/msys64/ucrt64/bin:$PATH" brand/source/.venv/Scripts/python brand/source/gen.py
```

It writes to `brand/source/out/`, laid out like `brand/`; copy over the files that changed. The font, the virtualenv
and `out/` are ignored by git. With these versions the output matches the committed files, except that the committed
SVGs also carry the C2PA provenance metadata that Claude Design added when exporting the kit.
