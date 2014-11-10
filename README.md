ExtractCoverThumbs
==================

Tool for recovering missing thumbnails in Cover View on Kindle e-ink devices

```
usage: ExtractCoverThumbs [-h] [-V] [-v] [-o] [-a] [-z] [-d [DAYS]]
                          kindle_directory

positional arguments:
  kindle_directory      directory where is a Kindle Paperwhite mounted

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -v, --verbose         print more informations
  -o, --overwrite       overwrite thumbnails
  -a, --apnx            also generate APNX files
  -z, --azw             also extract covers from AZW files
  -d [DAYS], --days [DAYS]
                        only "younger" ebooks than specified DAYS will be
                        processed (default: 7 days).
```
