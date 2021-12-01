from  setuptools import setup, find_packages
from pathlib import Path
here = Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='py-gurklang',
    version='0.0.1',
    description='a python runtime for gurklang',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/gurkult/py-gurklang',
    python_requires='>=3.8, <4',
    packages=['gurklang', 'gurklang.stdlib_modules', 'gurklang.plugins']
)