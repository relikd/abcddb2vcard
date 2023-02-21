#!/usr/bin/env python3
from setuptools import setup
from abcddb2vcard import __doc__, __version__

with open('README.md') as fp:
    longdesc = fp.read()

setup(
    name='abcddb2vcard',
    description=__doc__.strip(),
    version=__version__,
    author='relikd',
    url='https://github.com/relikd/abcddb2vcard',
    license='MIT',
    packages=['abcddb2vcard'],
    entry_points={
        'console_scripts': [
            'abcddb2vcard=abcddb2vcard.abcddb2vcard:main',
            'vcard2img=abcddb2vcard.vcard2img:main',
        ]
    },
    long_description_content_type="text/markdown",
    long_description=longdesc,
    python_requires='>=3.5',
    keywords=[
        'abcddb',
        'abcd',
        'address book',
        'vcard',
        'contacts',
        'converter',
        'export',
        'backup',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: MacOS X',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: SQL',
        'Topic :: Communications :: Email :: Address Book',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: Utilities',
    ],
)
