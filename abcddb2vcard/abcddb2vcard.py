#!/usr/bin/env python3
'''
Extract data from AddressBook database (.abcddb) to Contacts VCards file (.vcf)
'''
import os
import sys
from io import TextIOWrapper
from pathlib import Path
from argparse import ArgumentParser
try:
    from .ABCDDB import ABCDDB, Record
except ImportError:  # fallback if not run as module
    from ABCDDB import ABCDDB, Record  # type: ignore[import, no-redef]

DB_FILE = str(Path.home().joinpath(
    'Library', 'Application Support', 'AddressBook', 'AddressBook-v22.abcddb'))


def main() -> None:
    cli = ArgumentParser(description=__doc__)
    cli.add_argument('output', type=str, metavar='outfile.vcf',
                     help='VCard output file.')
    cli.add_argument('-f', '--force', action='store_true',
                     help='Overwrite existing output file.')
    cli.add_argument('--dry-run', action='store_true',
                     help='Do not write file(s), just print filenames.')
    cli.add_argument('-i', '--input', type=str, metavar='AddressBook.abcddb',
                     default=DB_FILE, help='Specify another abcddb input file.'
                     ' Default: ' + DB_FILE)
    cli.add_argument('-s', '--split', type=str, metavar='FORMAT', help='''
        Output into several vcf files instead of a single file.
        File format can use any field of type Record.
        E.g. "%%{id}_%%{fullname}.vcf".
    ''')
    args = cli.parse_args()

    # check input args
    if not os.path.isfile(args.input):
        print('AddressBook "{}" does not exist.'.format(args.input),
              file=sys.stderr)
        exit(1)
    elif not os.path.isdir(os.path.dirname(args.output) or os.curdir):
        print('Output parent directory does not exist.', file=sys.stderr)
        exit(1)
    elif os.path.exists(args.output) and not args.force:
        print('Output file already exist. Use -f to force overwrite.',
              file=sys.stderr)
        exit(1)

    # perform export
    contacts = ABCDDB.load(args.input)
    export_count = 0

    # reused for appending to an open file
    def writeRec(f: TextIOWrapper, rec: Record):
        nonlocal export_count
        try:
            f.write(rec.makeVCard())
            export_count += 1
        except Exception as e:
            print(f'Error processing contact {rec.id} {rec.fullname}: {e}',
                    file=sys.stderr)

    # choose which export mode to use
    if args.split:  # multi-file mode
        outDir = Path(args.output)
        prevFilenames = set()
        for rec in contacts:
            filename = outDir / Path(rec.formatFilename(args.split))
            if filename in prevFilenames:
                print(f'WARN: overwriting "{filename}"', file=sys.stderr)
            prevFilenames.add(filename)

            os.makedirs(filename.parent, exist_ok=True)
            if args.dry_run:
                print(filename)
            else:
                with open(filename, 'w') as f:
                    writeRec(f, rec)
    else:  # single-file mode
        if args.dry_run:
            print(args.output)
        else:
            with open(args.output, 'w') as f:
                for rec in contacts:
                    writeRec(f, rec)
    print(f'{export_count}/{len(contacts)} contacts.')


if __name__ == '__main__':
    main()
