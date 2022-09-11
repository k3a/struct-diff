# try yaml but don't make it a hard requirement
try:
    import yaml
except:
    pass

from util import is_scalar, prefix_lines
from comparator import changedict_vals, is_changedict, is_changedict_for_list, \
    TYPE_OBJECT, TYPE_ARRAY, KEY_LENGTH

class YAMLFormatterError(ValueError):
    """Module should use its own exceptions."""
    pass

class YAMLFormatter(object):
    """
    Formats changedict as YAML
    """

    def __init__(self, chdict):
        try: yaml
        except: raise YAMLFormatterError('pyyaml dependency is required for YAMLFormatter')
        self.chdict = chdict

    def __str__(self):
        return self._string_from_chdict(self.chdict)

    def _string_value(self, val, prefix='', prefix_first_line=False, newline_if_nonscalar=False) -> str:
        """
        String representation a leaf value with optional prefix.
        The value is encoded as-is, i.e. an object is dumped as the full yaml output.
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

    def _string_dict(self, chdict: dict, depth: int, prefix_first_line=True) -> str:
        """
        String representation of changes in a dict
        """

        out = ''
        (typ, rem, app, upd, orig) = changedict_vals(chdict)

        def prefix(op):
            nonlocal prefix_first_line
            if not prefix_first_line:
                prefix_first_line = True
                return ''
            else:
                return op + ' '*depth

        def format_key_line(op, key, val=None):
            if val is not None:
                val = self._string_value(val, prefix=op + ' '*(depth+1), newline_if_nonscalar=True)
            
            return prefix(op) + str(key) + (': '+val if val else ':')+'\n'

        for key in sorted(rem.keys()):
            out += format_key_line('-', key, rem[key])
        for key in sorted(app.keys()):
            out += format_key_line('+', key, app[key])
        for key in sorted(upd.keys()):
            val = upd[key]
            if is_changedict(val):
                # there is another changedict under the key
                out += format_key_line(' ', key)
                out += self._string_from_chdict(upd[key], depth+1, True)
            else:
                # this is an actual change of a value set to the key
                out += format_key_line('-', key, orig[key])
                out += format_key_line('+', key, upd[key])

        return out

    def _string_list(self, chdict: dict, depth: int, prefix_first_line=True) -> str:
        """
        String representation of changes in a list (array)
        """

        out = ''
        last_printed_idx = 0
        (typ, rem, app, upd, orig) = changedict_vals(chdict)

        ellipsis = lambda: ' ' + ' '*depth + '...\n'

        def prefix(op):
            nonlocal prefix_first_line
            if not prefix_first_line:
                prefix_first_line = True
                return ''
            else:
                return op + ' '*depth

        for n in sorted(upd, key=int):
            if n > last_printed_idx:
                out += ellipsis()
            
            # print prefix
            out += prefix('-')

            val = upd[n]
            if is_changedict(val):
                # there is another changedict
                out += '- ' + self._string_from_chdict(val, depth+2, prefix_first_line=False)
            else:
                # this is a single value change in an array element so remove the old value first
                out += '- ' + self._string_value(orig[n], prefix='-' + ' '*(depth+2)) + '\n'
                # and add a new value
                out += prefix('+')
                out += '- ' + self._string_value(val, prefix='+' + ' '*(depth+2)) + '\n'
    
            last_printed_idx = n

        for n in sorted(rem, key=int):
            if n > last_printed_idx:
                out += ellipsis()
            out += prefix('-') + '- ' + self._string_value(rem[n], prefix='-' + ' '*(depth+2)) + '\n'
            last_printed_idx = n

        if len(app) > 0:
            if last_printed_idx < orig[KEY_LENGTH]-1:
                out += ellipsis()
            for n in sorted(app, key=int):
                out += prefix('+') + '- ' + self._string_value(app[n], prefix='+' + ' '*depth) + '\n'
                last_printed_idx = n

        return out

    def _string_from_chdict(self, chdict: dict, depth=0, prefix_first_line=True) -> str:
        """
        String representation of changes described by diff changedict made on the original object obj
        """
        out = ''

        (typ, rem, app, upd, orig) = changedict_vals(chdict)

        if len(rem) > 0 or len(app) > 0 or len(upd) > 0:
            if typ == TYPE_OBJECT:
                out += self._string_dict(chdict, depth, prefix_first_line)
            elif typ == TYPE_ARRAY or is_changedict_for_list(chdict):
                out += self._string_list(chdict, depth, prefix_first_line)
            else:
                out = ''
                for k in rem:
                    out += self._string_value(rem[k], prefix='-' + ' '*depth, prefix_first_line=True) + '\n'
                for k in app:
                    out += self._string_value(app[k], prefix='+' + ' '*depth, prefix_first_line=True) + '\n'
                if len(upd) > 0:
                    raise YAMLFormatterError('unexpected _update ' + str(upd))

        return out if depth > 0 else out.rstrip()
