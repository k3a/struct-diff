#!/usr/bin/env python3

import json
import sys
from argparse import ArgumentParser

from .comparator import diff
from .formatters import colorize, YAMLFormatter

def main(argv=None):
    parser = ArgumentParser(prog='struct_diff')
    parser.add_argument('old', help='original file')
    parser.add_argument('new', help='new file')
    parser.add_argument('-C', dest='color', default=None, action='store_true', help='force colorize the output')
    parser.add_argument('--no-color', action='store_true', help='do not colorize the output')
    parser.add_argument('-j', '--raw-json', action='store_true', help='display raw JSON encoding of the diff')
    parser.add_argument('-Y', '--yaml', action='store_true', help='output diff as YAML')
    parser.add_argument('-f', '--full', action='store_true', help='include the equal sections of the document, not just the deltas')
    parser.add_argument('--max-elisions', type=int, help='max number of ...\'s to show in a row in "deltas" mode (before collapsing them) #var(maxElisions)')
    parser.add_argument('-o', '--output-keys', metavar='KEY', nargs='+', help='always print this comma separated keys, with their value, if they are part of an object with any diff')
    parser.add_argument('-n', '--output-new-only', action='store_true', help='output only the updated and new key/value pairs (without marking them as such). If you need only the diffs from the old file, just exchange the first and second json')
    parser.add_argument('-s', '--sort', action='store_true', help='sort primitive values in arrays before comparing')
    parser.add_argument('-c', '--object-context', action='store_true', help='if a scalar value of an object key is changed, also include other (unchanged) values of that object')
    parser.add_argument('-k', '--keys-only', action='store_true', help='compare only the keys, ignore the differences in values')
    parser.add_argument('-K', '--keep-unchanged-values', action='store_true', help='instead of omitting values that are equal, output them as they are')
    parser.add_argument('-p', '--precision', metavar='DECIMALS', type=int, help='round all floating point numbers to this number of decimal places prior to comparison')
    parser.add_argument('-w', '--indent-width', default=None, type=int, help='number of spaces for indendation')

    sys_args = argv if argv is not None else sys.argv[:]
    args = parser.parse_args()

    if args.no_color:
        args.color = False
    else:
        if args.color is None:
            args.color = sys.stdout.isatty()

    with open(args.old) as old_file, open(args.new) as new_file:
        try:
            obj1 = json.load(old_file)
        except Exception as e:
            print(f"error parsing file {args.old} as JSON: {e}", file=sys.stderr)
            old_file.seek(0, 0)
            obj1 = old_file.read()
        
        try:
            obj2 = json.load(new_file)
        except Exception as e:
            print(f"error parsing file {args.old} as JSON: {e}", file=sys.stderr)
            new_file.seek(0, 0)
            obj2 = new_file.read()

        diff_res = diff(obj1, obj2, args)

        if args.yaml:
            outs = str(YAMLFormatter(diff_res, args))
        elif args.raw_json:
            outs = json.dumps(diff_res, indent=2, ensure_ascii=False)
        else:
            outs = str(colorize(diff_res, args))

        print(outs, end=None if len(outs)>0 else '')

    # return 1 if there were differences
    if diff_res is not None and len(diff_res) > 0:
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
