import fnmatch
import os
from distutils.core import setup
from distutils.extension import Extension

import numpy
from Cython.Build import cythonize

matches = []
for root, dirnames, filenames in os.walk('friendlyfit'):
    for filename in fnmatch.filter(filenames, '*.pyx'):
        matches.append(os.path.join(root, filename))
print(matches)

extensions = [Extension(
    x.split('.')[0], [x], include_dirs=[numpy.get_include()],
    extra_compile_args=['-Wno-unused-function', '-Wno-unreachable-code'])
              for x in matches]

setup(ext_modules=cythonize(extensions))
