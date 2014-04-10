from distutils.core import setup
import py2exe
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

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
            'includes': ['lxml.etree', 'lxml._elementpath', 'gzip'],
        }
    },
    zipfile=None,
    console=['epubQTools.py'],
)
