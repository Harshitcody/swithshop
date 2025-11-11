from setuptools import setup
from setuptools import Extension
from Cython.Build import cythonize

ext_modules = [
    Extension("rec_engine", ["rec_engine.pyx"], extra_compile_args=["-O3"]),
]

setup(
    name="rec_engine",
    ext_modules=cythonize(ext_modules, compiler_directives={'language_level': "3"}),
)
