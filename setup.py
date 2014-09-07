#!/usr/bin/env python

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
from setuptools import setup, find_packages
import sys
from platform import system

py_version = sys.version_info[:2]
PY2 = py_version[0] == 2
ON_WINDOWS = system() == 'Windows'

if PY2:
    if py_version < (2, 7):
        raise RuntimeError(
            'On Python 2, Err requires Python 2.7 or later')

    deps = ['webtest',
            'setuptools',
            'yapsy',
            'bottle',
            'requests',
            'jinja2',
            'pyOpenSSL',
            'dnspython',  # dnspython for SRV records
            'config']
else:
    if py_version < (3, 3):
        raise RuntimeError(
            'On Python 3, Err requires Python 3.3 or later')

    deps = ['webtest',
            'setuptools',
            'yapsy',
            'bottle',
            'requests',
            'jinja2',
            'pyOpenSSL',
            'dnspython3']  # requests are for the unittests, dnspython for SRV records

if not ON_WINDOWS:
    deps += ['daemonize']

src_dirs = ("errbot", "scripts", "tests")


def convert_to_python2():
    try:
        from lib3to2 import main as three2two
    except ImportError:
        print("Installing Err under Python 2, which requires 3to2 to be installed, but it was not found")
        print("I will now attempt to install it automatically, but this requires at least pip 1.4 to be installed")
        print("If you get the error 'no such option: --no-clean', please `pip install 3to2` manually and "
              "then `pip install err` again.")
        from pip import main as mainpip

        mainpip(['install', '3to2', '--no-clean'])
        from lib3to2 import main as three2two
    import shutil
    import shlex

    for d in src_dirs:
        three2two.main("lib3to2.fixes", shlex.split("-n --no-diffs -w {0}".format(d)))


src_root = os.curdir
sys.path.insert(0, os.path.join(src_root, 'errbot'))  # hack to avoid loading err machinery from the errbot package


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


if __name__ == "__main__":
    from version import VERSION

    changes = read('CHANGES.rst')

    if changes.find(VERSION) == -1:
        raise Exception('You forgot to put a release note in CHANGES.rst ?!')

    if set(sys.argv) & set(('bdist',
                            'bdist_dumb',
                            'bdist_rpm',
                            'bdist_wininst',
                            'bdist_msi')):
        raise Exception("err doesn't support binary distributions")

    # under python2 if we want to make a source distribution,
    # don't pre-convert the sources, leave them as py3.
    if PY2 and 'install' in sys.argv or 'develop' in sys.argv:
        convert_to_python2()

    setup(
        name="err",
        version=VERSION,
        packages=find_packages(src_root),
        scripts=['scripts/err.py'],

        install_requires=deps,
        tests_require=['nose', 'webtest', 'requests'],
        package_data={
            '': ['*.txt', '*.rst', '*.plug', '*.html', '*.js', '*.css'],
        },

        author="Guillaume BINET",
        author_email="gbin@gootz.net",
        description="err is a plugin based team chatbot designed to be easily deployable, extensible and maintainable.",
        long_description=''.join([read('README.rst'), '\n\n', changes]),
        license="GPL",
        keywords="xmpp jabber chatbot bot plugin",
        url="http://errbot.net/",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Topic :: Communications :: Chat",
            "Topic :: Communications :: Chat :: Internet Relay Chat",
            "Topic :: Communications :: Conferencing",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.3",
        ],
        src_root=src_root,
        platforms='any',
    )

# restore the paths
sys.path.remove(os.path.join(src_root, 'errbot'))
