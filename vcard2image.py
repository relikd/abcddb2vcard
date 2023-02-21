#!/usr/bin/env python3
import os
import sys
from base64 import b64decode
from pathlib import Path

if len(sys.argv) != 3:
    print('  Usage:', Path(__file__).name, 'infile.vcf', 'outdir/')
    exit(0)

infile = Path(sys.argv[1])
outdir = Path(sys.argv[2])
if not infile.exists():
    print('Does not exist: ', infile, file=sys.stderr)
    exit(1)
elif not outdir.exists():
    if not outdir.parent.exists():
        print('Output directory does not exist.', file=sys.stderr)
        exit(1)
    else:
        os.mkdir(outdir)

with open(infile, 'r') as f:
    c1 = 0
    c2 = 0
    name = ''
    img = ''
    collect = False
    for line in f.readlines():
        line = line.rstrip()
        if line == 'BEGIN:VCARD':
            c1 += 1
            name = ''
            img = ''
            collect = False
        elif line.startswith('FN:'):
            name = line.split(':', 1)[1]
        elif line.startswith('PHOTO;'):
            img = line.split(':', 1)[1]
            collect = True
        elif collect:
            if line[0] == ' ':
                img += line[1:]
            else:
                collect = False
        if line == 'END:VCARD' and img:
            c2 += 1
            name = name.replace('\\,', ',').replace('\\;', ';').replace(
                '/', '-')
            with open(outdir.joinpath(name + '.jpg'), 'wb') as fw:
                fw.write(b64decode(img))

    print(c1, 'contacts.', c2, 'images.')
