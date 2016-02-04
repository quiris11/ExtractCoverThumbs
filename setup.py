from distutils.core import setup
import py2exe  # noqa
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
    console=[{'script': '__main__.py', 'dest_base': 'ExtractCoverThumbs_con'}],
    windows=[{'script': 'gui.py', 'dest_base': 'ExtractCoverThumbs_win'}],
)

# build on Mac:
# pyinstaller -Fn ExtractCoverThumbs_con ~/github/ExtractCoverThumbs/__main__.py  # noqa
# pyinstaller -Fn ExtractCoverThumbs_app  --windowed ~/github/ExtractCoverThumbs/gui.py  # noqa

# build on Windows:
# 1) turn off antivirus
# 2) python setup.py py2exe
