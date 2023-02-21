#!/usr/bin/env python3
'''
Extract all profile pictures from a Contacts VCards file (.vcf)
'''
import os
import sys
from base64 import b64decode
from argparse import ArgumentParser, FileType


def main() -> None:
    cli = ArgumentParser(description=__doc__)
    cli.add_argument('input', type=FileType('r'), metavar='infile.vcf',
                     help='VCard input file.')
    cli.add_argument('outdir', type=str, help='Output directory.')
    args = cli.parse_args()

    # check input args
    if not os.path.isdir(os.path.dirname(args.outdir) or os.curdir):
        print('Output parent directory does not exist.', file=sys.stderr)
        exit(1)

    os.makedirs(args.outdir, exist_ok=True)

    # perform export
    c1 = 0
    c2 = 0
    name = ''
    img = ''
    collect = False
    for line in args.input.readlines():
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
            with open(os.path.join(args.outdir, name + '.jpg'), 'wb') as fw:
                fw.write(b64decode(img))

    print(c1, 'contacts.', c2, 'images.')


if __name__ == '__main__':
    main()
