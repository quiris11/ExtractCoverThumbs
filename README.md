ExtractCoverThumbs [![Release](https://img.shields.io/github/release/quiris11/extractcoverthumbs.svg)](https://github.com/quiris11/extractcoverthumbs/releases/latest)
==================

Tool for recovering missing thumbnails in Cover View on Kindle e-ink devices. 
The tool **does not work** on Kindle with firmware **5.8.5 and newer** for ebooks **downloaded from Kindle Personal Documents Service**.

```
usage: ExtractCoverThumbs [-h] [-V] [-s] [--overwrite-pdoc-thumbs]
                          [--overwrite-amzn-thumbs] [-o] [--skip-apnx] [-f]
                          [-z] [-d [DAYS]] [-l] [--mark-real-pages] [-e]
                          kindle_directory

positional arguments:
  kindle_directory      directory where is a Kindle Paperwhite mounted

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -s, --silent          print less informations
  --overwrite-pdoc-thumbs
                        overwrite personal documents (PDOC) cover thumbnails
  --overwrite-amzn-thumbs
                        overwrite amzn ebook (EBOK) and book sample (EBSP)
                        cover thumbnails
  -o, --overwrite-apnx  overwrite APNX files
  --skip-apnx           skip generating APNX files
  -f, --fix-thumb       fix thumbnails for PERSONAL badge
  -z, --azw             process also AZW files
  -d [DAYS], --days [DAYS]
                        only "younger" ebooks than specified DAYS will be
                        processed (default: 7 days).
  -l, --lubimy-czytac   download real pages from lubimyczytac.pl (time-
                        consuming process!) (only with -d)
  --mark-real-pages     mark computed pages as real pages (only with -l and
                        -d)
  -e, --eject           eject Kindle after completing process
```

#### Additional requirements:
* python -m pip install pillow
* python -m pip install pyinstaller (for compilation only)

#### Compilation tips for creating standalone applications with Pyinstaller tool:
* build on Mac (with Python 2.7.x from Homebrew):
```
pyinstaller -Fn ExtractCoverThumbs_con ~/github/ExtractCoverThumbs/__main__.py
pyinstaller -Fn ExtractCoverThumbs_app  --windowed ~/github/ExtractCoverThumbs/gui.pyw
```
* build on Windows (with Python 2.7.x):
```
C:\Python27\Scripts\pyinstaller.exe -Fn ExtractCoverThumbs_con .\ExtractCoverThumbs\__main__.py
C:\Python27\Scripts\pyinstaller.exe -Fn ExtractCoverThumbs_win --windowed .\ExtractCoverThumbs\gui.pyw
```
