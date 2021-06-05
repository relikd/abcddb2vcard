#!/usr/bin/env python3
import sys
from ABCDDB import ABCDDB
from pathlib import Path

if len(sys.argv) != 2:
    print('  Usage:', Path(__file__).name, 'outfile.vcf')
    exit(0)

outfile = Path(sys.argv[1])
if not outfile.parent.exists():
    print('Output directory does not exist.', file=sys.stderr)
    exit(1)

contacts = ABCDDB.load(Path.home().joinpath(
    'Library/Application Support/AddressBook/AddressBook-v22.abcddb'))
# contacts = [list(contacts)[-1]]  # test on last imported contact
with open(outfile, 'w') as f:
    for rec in contacts:
        f.write(rec.makeVCard())
    print(len(contacts), 'contacts.')
