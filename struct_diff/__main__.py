#!/usr/bin/env python3
"""
Structural comparison of two objects.

Copyright (c) 2011 Red Hat Corp. (Matěj Cepl)
Copyright (c) 2022 Mario Hros (K3A.me)

License: MIT
"""
try:
    import json
except ImportError:
    import simplejson as json
import sys
from optparse import OptionParser

from .comparator import Comparator
from .formatters import YAMLFormatter

def main(argv=None):
    """Main function, to process command line arguments etc."""
    sys_args = argv if argv is not None else sys.argv[:]
    usage = "usage: %prog [options] old.json new.json"
    parser = OptionParser(prog="struct_diff", usage=usage)
    parser.add_option("-x", "--exclude",
                      action="append", dest="exclude", metavar="ATTR",
                      default=[],
                      help="attributes which should be ignored when comparing")
    parser.add_option("-i", "--include",
                      action="append", dest="include", metavar="ATTR",
                      default=[],
                      help="attributes which should be exclusively " +
                      "used when comparing")
    parser.add_option("-o", "--output",
                      action="append", dest="output", metavar="FILE",
                      default=[],
                      help="name of the output file (default is stdout)")
    parser.add_option("-a", "--ignore-append",
                      action="store_true", dest="ignore_append",
                      metavar="BOOL", default=False,
                      help="ignore appended keys")
    parser.add_option("-Y", "--yaml",
                      action="store_true", dest="yaml",
                      metavar="BOOL", default=False,
                      help="output YAML diff")
    (options, args) = parser.parse_args(sys_args[1:])

    if options.output:
        outf = open(options.output[0], "w")
    else:
        outf = sys.stdout

    if len(args) != 2:
        parser.error("Two positional arguments, " +
                     "paths to the old and new JSON file are required")

    with open(args[0]) as old_file, open(args[1]) as new_file:
        try:
            obj1 = json.load(old_file)
        except Exception as e:
            print(f"error opening file {args[0]} as JSON: {e}", file=sys.stderr)
            old_file.seek(0, 0)
            obj1 = old_file.read()
        
        try:
            obj2 = json.load(new_file)
        except Exception as e:
            print(f"error opening file {args[1]} as JSON: {e}", file=sys.stderr)
            new_file.seek(0, 0)
            obj2 = new_file.read()

        diff = Comparator(obj1, obj2, options)
        diff_res = diff.compare()

        if options.yaml:
            outs = str(YAMLFormatter(diff_res))
        else:
            outs = json.dumps(diff_res, indent=4, ensure_ascii=False)

        print(outs, end=None if len(outs)>0 else '', file=outf)
        outf.close()

    if len(diff_res) > 0:
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
