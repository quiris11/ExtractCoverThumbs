from distutils.core import setup
import py2exe
import sys

sys.argv.append('py2exe')
setup(
    options={
        'py2exe': {
            'compressed': 1,
            'optimize': 2,
            'bundle_files': 1,
            'dist_dir': 'dist',
            'xref': False,
            'skip_archive': False,
            'ascii': False,
            'dll_excludes': ['w9xpopen.exe'],
        }
    },
    zipfile=None,
    console=[{'script': '__main__.py', 'dest_base': 'ExtractCoverThumbs'}],
)

# build on Mac:
# pyinstaller -Fn ExtractCoverThumbs ~/github/ExtractCoverThumbs/__main__.py
