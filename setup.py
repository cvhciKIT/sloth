#!/usr/bin/env python
import sys, os
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

# the following installation setup is based on django's setup.py
def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
sloth_dir = 'sloth'

for dirpath, dirnames, filenames in os.walk(sloth_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
        if 'labeltool.ui' in filenames:
            data_files.append([dirpath, [os.path.join(dirpath, 'labeltool.ui')]])
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(name='sloth',
      version='0.1',
      description='The Sloth Labeling Tool',
      author='CV:HCI Research Group',
      url='http://cvhci.anthropomatik.kit.edu',
      requires=['importlib', 'okapy'],
      packages=packages,
      data_files=data_files,
      scripts=['sloth/bin/sloth']
)
