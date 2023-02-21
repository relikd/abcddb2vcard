#!/usr/bin/env python3
'''
Extract data from AddressBook database (.abcddb) to Contacts VCards file (.vcf)
'''
import os
import sys
from ABCDDB import ABCDDB
from pathlib import Path
from argparse import ArgumentParser


DB_FILE = str(Path.home().joinpath(
    'Library', 'Application Support', 'AddressBook', 'AddressBook-v22.abcddb'))

cli = ArgumentParser(description=__doc__)
cli.add_argument('output', type=str, metavar='outfile.vcf',
                 help='VCard output file.')
cli.add_argument('-f', '--force', action='store_true',
                 help='Overwrite existing output file.')
cli.add_argument('-i', '--input', type=str, metavar='AddressBook.abcddb',
                 default=DB_FILE, help='Specify another abcddb input file.'
                 ' Default: ' + DB_FILE)
args = cli.parse_args()

# check input args
if not os.path.isfile(args.input):
    print('AddressBook "{}" does not exist.'.format(args.input),
          file=sys.stderr)
    exit(1)
elif not os.path.isdir(os.path.dirname(args.output) or os.curdir):
    print('Output parent directory does not exist.', file=sys.stderr)
    exit(1)
elif os.path.isfile(args.output) and not args.force:
    print('Output file already exist. Use -f to force overwrite.',
          file=sys.stderr)
    exit(1)

# perform export
contacts = ABCDDB.load(args.input)
with open(args.output, 'w') as f:
    for rec in contacts:
        f.write(rec.makeVCard())
    print(len(contacts), 'contacts.')
