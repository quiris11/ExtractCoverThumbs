ExtractCoverThumbs
==================

Tool for recovering missing thumbnails in Cover View on Kindle e-ink devices

```
usage: ExtractCoverThumbs [-h] [-V] [-s] [--overwrite-pdoc-thumbs]
                          [--overwrite-amzn-thumbs] [--overwrite-apnx]
                          [--skip-apnx] [-f] [-z] [-d [DAYS]] [--dump-pages]
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
  --overwrite-apnx      overwrite APNX files
  --skip-apnx           skip generating APNX files
  -f, --fix-thumb       fix thumbnails for PERSONAL badge
  -z, --azw             also extract covers from AZW files
  -d [DAYS], --days [DAYS]
                        only "younger" ebooks than specified DAYS will be
                        processed (default: 7 days).
  --dump-pages          dump list of new books with a rough number of pages
                        from last dump
```
