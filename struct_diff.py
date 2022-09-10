#!/usr/bin/env python3
"""
Structural comparison of two objects.

Copyright (c) 2011 Red Hat Corp. (Matěj Cepl)
Copyright (c) 2022 Mario Hros (K3A.me)

License: MIT
"""

import sys
from optparse import OptionParser
# Don't do anything silly ... this should be compatible with python 2.4!
try:
    import json
except ImportError:
    import simplejson as json
# try yaml but don't make it a hard requirement
try:
    import yaml
except:
    pass
__version__ = "2.0.0"

KEY_TYPE        = '__type'
KEY_REMOVE      = '__remove'
KEY_APPEND      = '__append'
KEY_UPDATE      = '__update'
KEY_ORIGINAL    = '__original'
KEY_LENGTH      = '__length'
TYPE_OBJECT = 'object'
TYPE_ARRAY = 'array'

def is_scalar(value):
    """
    Primitive version, relying on the fact that JSON cannot
    contain any more complicated data structures.
    """
    return not isinstance(value, (list, tuple, dict))

class BadJSONError(ValueError):
    """Module should use its own exceptions."""
    pass


def prefix_lines(s: str, prefix: str, prefix_first_line=True) -> str:
    """
    Prefixes lines in a string str with a string prefix.
    The first line will not be prefixed if prefix_first_line is False.
    """
    if prefix == '':
        return s
    lines = s.splitlines()
    for n in range(len(lines)):
        if n != 0 or prefix_first_line:
            lines[n] = prefix + lines[n]
    return '\n'.join(lines)

def is_changedict(d: dict) -> bool:
    """
    Returns True if d is a dict containing _remove, _append or _update keys
    """
    return isinstance(d, dict) and (KEY_REMOVE in d or KEY_APPEND in d or KEY_UPDATE in d or KEY_ORIGINAL in d)

def is_changedict_for_list(inp_dict: dict) -> bool:
    """
    Returns True if inp_dict is a changedict for a list (array) and contains only numeric keys.
    """
    if not is_changedict(inp_dict):
        return False
    # keys must be convertible to int
    def check_keys(d, key):
        if d is None:
            return True
        if key not in d:
            return True
        d = d[key]
        for k in d:
            if not isinstance(k, int):
                return False
        return True
    return check_keys(inp_dict, KEY_REMOVE) and check_keys(inp_dict, KEY_APPEND) and check_keys(inp_dict, KEY_UPDATE)

def changedict_vals(chdict: dict) -> tuple[str, dict, dict, dict, dict]:
    """
    Extracts (type, remove, append, upgrade, original) parts from the changedict.
    """
    typ = ''
    rem = {}
    app = {}
    upd = {}
    orig = {}

    if KEY_TYPE in chdict:
        typ = chdict[KEY_TYPE]
    if KEY_REMOVE in chdict:
        rem = chdict[KEY_REMOVE]
    if KEY_APPEND in chdict:
        app = chdict[KEY_APPEND]
    if KEY_UPDATE in chdict:
        upd = chdict[KEY_UPDATE]
    if KEY_ORIGINAL in chdict:
        orig = chdict[KEY_ORIGINAL]

    return (typ, rem, app, upd, orig)

class Comparator(object):
    """
    Main workhorse, the comparator producing changedicts
    """
    def __init__(self, obj1, obj2, opts=None):
        self.obj1 = obj1
        self.obj2 = obj2

        self.excluded_attributes = []
        self.included_attributes = []
        self.ignore_appended = False
        if opts:
            self.excluded_attributes = opts.exclude or []
            self.included_attributes = opts.include or []
            self.ignore_appended = opts.ignore_append or False

    def _is_incex_key(self, key, value):
        """Is this key excluded or not among included ones? If yes, it should
        be ignored."""
        key_out = ((self.included_attributes and
                   (key not in self.included_attributes)) or
                   (key in self.excluded_attributes))
        value_out = True
        if isinstance(value, dict):
            for change_key in value:
                if isinstance(value[change_key], dict):
                    for key in value[change_key]:
                        if ((self.included_attributes and
                             (key in self.included_attributes)) or
                           (key not in self.excluded_attributes)):
                                value_out = False
        return key_out and value_out

    def _filter_results(self, result):
        """Whole -i or -x functionality. Rather than complicate logic while
        going through the object’s tree we filter the result of plain
        comparison.

        Also clear out unused keys in result"""
        out_result = {}
        for change_type in result:
            if change_type == KEY_TYPE:
                # skip internal key
                continue
            temp_dict = {}
            for key in result[change_type]:
                if self.ignore_appended and (change_type == KEY_APPEND):
                    continue
                if not self._is_incex_key(key, result[change_type][key]):
                    temp_dict[key] = result[change_type][key]
            if len(temp_dict) > 0:
                out_result[change_type] = temp_dict
                # copy KEY_TYPE over
                out_result[KEY_TYPE] = result[KEY_TYPE]

        return out_result

    def _compare_elements(self, old, new):
        """Unify decision making on the leaf node level."""
        res = None
        # We want to go through the tree post-order
        if isinstance(old, dict):
            res_dict = self._compare_dicts(old, new)
            if (len(res_dict) > 0):
                res = res_dict
        # Now we are on the same level
        # different types, new value is new
        elif (type(old) != type(new)):
            res = new
        # recursive arrays
        # we can be sure now, that both new and old are
        # of the same type
        elif (isinstance(old, list)):
            res_arr = self._compare_arrays(old, new)
            if (len(res_arr) > 0):
                res = res_arr
        # the only thing remaining are scalars
        else:
            scalar_diff = self._compare_scalars_return_new(old, new)
            if scalar_diff is not None:
                res = scalar_diff

        return res

    def _compare_scalars_return_new(self, old, new):
        """
        Compare scalar values and return the new value if they differ.
        Returns None if old and new are the same.
        """
        if old != new:
            return new
        else:
            return None

    def _compare_arrays(self, old_arr, new_arr):
        """
        Produce changedict by comparing two list (array) objects
        """
        inters = min(len(old_arr), len(new_arr))  # this is the smaller length

        result = {
            KEY_TYPE: TYPE_ARRAY,
            KEY_APPEND: {},
            KEY_REMOVE: {},
            KEY_UPDATE: {},
            KEY_ORIGINAL: {}
        }
        for idx in range(inters):
            res = self._compare_elements(old_arr[idx], new_arr[idx])
            if res is not None:
                result[KEY_UPDATE][idx] = res
                result[KEY_ORIGINAL][idx] = old_arr[idx]

        # the rest of the larger array
        if (inters == len(old_arr)):
            for idx in range(inters, len(new_arr)):
                result[KEY_APPEND][idx] = new_arr[idx]
        else:
            for idx in range(inters, len(old_arr)):
                result[KEY_REMOVE][idx] = old_arr[idx]

        # Clear out unused keys in result
        out_result = {}
        for key in result:
            if len(result[key]) > 0:
                out_result[key] = result[key]

        if len(out_result) > 0:
            # copy length over
            if KEY_ORIGINAL not in out_result:
                out_result[KEY_ORIGINAL] = {}
            out_result[KEY_ORIGINAL][KEY_LENGTH] = len(old_arr)

        return self._filter_results(result)

    def _compare_dicts(self, old_obj=None, new_obj=None):
        """
        Produce changedict by comparing two dict objects
        """
        old_keys = set()
        new_keys = set()
        if old_obj and len(old_obj) > 0:
            old_keys = set(old_obj.keys())
        if new_obj and len(new_obj) > 0:
            new_keys = set(new_obj.keys())

        keys = old_keys | new_keys

        result = {
            KEY_TYPE: TYPE_OBJECT,
            KEY_APPEND: {},
            KEY_REMOVE: {},
            KEY_UPDATE: {},
            KEY_ORIGINAL: {},
        }
        for name in keys:
            # old_obj is missing
            if name not in old_obj:
                result[KEY_APPEND][name] = new_obj[name]
            # new_obj is missing
            elif name not in new_obj:
                result[KEY_REMOVE][name] = old_obj[name]
            else:
                res = self._compare_elements(old_obj[name], new_obj[name])
                if res is not None:
                    result[KEY_UPDATE][name] = res
                    result[KEY_ORIGINAL][name] = old_obj[name]

        return self._filter_results(result)

    def compare(self, old_obj=None, new_obj=None):
        """
        Produces changedoct by comparing two parameters old_obj and new_obj.
        Types of parameters may be different.
        If old_obj or new_obj is None, parameters taken from the constructor will be used.
        """
        if not old_obj and hasattr(self, "obj1"):
            old_obj = self.obj1
        if not new_obj and hasattr(self, "obj2"):
            new_obj = self.obj2

        same_type = type(old_obj) == type(new_obj)

        if same_type and isinstance(old_obj, dict):
            return self._compare_dicts(old_obj, new_obj)
        elif same_type and isinstance(old_obj, list):
            return self._compare_arrays(old_obj, new_obj)
        elif old_obj != new_obj:
            # different types betwen old and new, a scalar or unusual type 
            # remove the old oone and add a new one
            return {KEY_REMOVE: {'': old_obj}, KEY_APPEND: {'': new_obj}}
        else:
            # mo change
            return '{}'

class YAMLFormatter(object):
    """
    Formats changedict as YAML
    """

    def __init__(self, chdict):
        self.chdict = chdict

    def __str__(self):
        return self._string_from_chdict(self.chdict)

    def _string_value(self, val, prefix='', prefix_first_line=False, newline_if_nonscalar=False) -> str:
        """
        String representation a value with optional prefix.
        The will not be added on the first line if prefix_first_line is False.
        If newline_if_nonscalar is True, a new line is prefixed to the string value and in such
        case prefix_first_line parameter is ignored.
        """
        if is_scalar(val):
            return (prefix if prefix_first_line else '') + str(val)
        else:
            out = '\n' if newline_if_nonscalar else ''
            out += prefix_lines(yaml.safe_dump(val), prefix, prefix_first_line=prefix_first_line or newline_if_nonscalar)
            return out

    def _string_dict(self, chdict: dict, depth: int) -> str:
        """
        String representation of changes in a dict
        """

        out = ''
        (typ, rem, app, upd, orig) = changedict_vals(chdict)

        def format_key_line(op, key, val=None):
            if val is not None:
                val = self._string_value(val, prefix=op + ' '*(depth+1), newline_if_nonscalar=True)
            return op + ' '*depth + str(key) + (': '+val if val else ':')+'\n'

        for key in sorted(rem.keys()):
            out += format_key_line('-', key, rem[key])
        for key in sorted(app.keys()):
            out += format_key_line('+', key, app[key])
        for key in sorted(upd.keys()):
            val = upd[key]
            if is_changedict(val):
                # there is another changedict under the key
                out += format_key_line(' ', key)
                out += self._string_from_chdict(upd[key], depth+1)
            else:
                # this is an actual change of a value set to the key
                out += format_key_line('-', key, orig[key])
                out += format_key_line('+', key, upd[key])

        return out

    def _string_list(self, chdict: dict, depth: int) -> str:
        """
        String representation of changes in a list (array)
        """

        out = ''
        last_printed_idx = 0
        (typ, rem, app, upd, orig) = changedict_vals(chdict)

        ellipsis = lambda: ' ' + ' '*depth + '...\n'

        for n in sorted(upd, key=int):
            if n > last_printed_idx:
                out += ellipsis()
            # remove old
            out += '-' + ' '*depth + '- ' + self._string_value(orig[n], prefix='-' + ' '*(depth+2)) + '\n'
            # add new
            out += '+' + ' '*depth + '- ' +  self._string_value(orig[n], prefix='+' + ' '*(depth+2)) + '\n'
            last_printed_idx = n

        for n in sorted(rem, key=int):
            if n > last_printed_idx:
                out += ellipsis()
            out += '-' + ' '*depth + '- ' + self._string_value(rem[n], prefix='-' + ' '*(depth+2)) + '\n'
            last_printed_idx = n

        if len(app) > 0:
            if last_printed_idx < orig[KEY_LENGTH]-1:
                out += ellipsis()
            for n in sorted(app, key=int):
                out += '+' + ' '*depth + '- ' + self._string_value(app[n], prefix='+' + ' '*depth) + '\n'
                last_printed_idx = n

        return out

    def _string_from_chdict(self, chdict: dict, depth=0) -> str:
        """
        String representation of changes described by diff changedict made on the original object obj
        """
        out = ''

        (typ, rem, app, upd, orig) = changedict_vals(chdict)

        if len(rem) > 0 or len(app) > 0 or len(upd) > 0:
            if typ == TYPE_OBJECT:
                out += self._string_dict(chdict, depth)
            elif typ == TYPE_ARRAY or is_changedict_for_list(chdict):
                out += self._string_list(chdict, depth)
            else:
                out = ''
                for k in rem:
                    out += self._string_value(rem[k], prefix='-' + ' '*depth, prefix_first_line=True) + '\n'
                for k in app:
                    out += self._string_value(app[k], prefix='+' + ' '*depth, prefix_first_line=True) + '\n'
                if len(upd) > 0:
                    raise BadJSONError('unexpected _update ' + str(upd))

        return out if depth > 0 else out.rstrip()

def main(argv=None):
    """Main function, to process command line arguments etc."""
    sys_args = argv if argv is not None else sys.argv[:]
    usage = "usage: %prog [options] old.json new.json"
    parser = OptionParser(usage=usage)
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
        parser.error("Script requires two positional arguments, " +
                     "names for old and new JSON file.")

    with open(args[0]) as old_file, open(args[1]) as new_file: 
        try:
            obj1 = json.load(old_file)
        except (TypeError, OverflowError, ValueError) as exc:
            raise BadJSONError("Cannot decode object from JSON\n%s" %
                                str(exc))
        try:
            obj2 = json.load(new_file)
        except (TypeError, OverflowError, ValueError) as exc:
            raise BadJSONError("Cannot decode object from JSON\n%s" %
                                str(exc))

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
