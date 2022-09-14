import math
import re
import json
from abc import ABC, abstractmethod
from typing import Any

from ..util import _get_opt, _extend_typeof, _is_scalar
from ..comparator import OP

class FormatterError(ValueError):
    pass

class Part:
    BODY = 'b'
    ELISION = 'e'
    OBJECT_BEGIN = 'O'
    OBJECT_END = 'o'
    ARRAY_ELEMENT = '-'
    ARRAY_BEGIN = 'A'
    ARRAY_END = 'a'

_ansi = lambda code: '\x1b['+str(code)+'m'

Theme = {
    OP.NONE: lambda c: c,
    OP.ADD: lambda c: _ansi(32) + c +_ansi(0),
    OP.REMOVE: lambda c: _ansi(31) + c +_ansi(0),
}

class BaseFormatter(ABC):
    """Base class containing common formatter code to make writing formatters easier"""

    def __init__(self, diff = None, opts = None):
        self.diff = diff
        self.opts = opts

    def _get_opt(self, key, default=False):
        return _get_opt(self.opts, key, default)

    @abstractmethod
    def _output(self, context: Any, op: str, part: str, key: str, value: Any, depth: int):
        pass

    def _output_elisions(self, context: Any, n, depth: int):
        max_elisions = self._get_opt('max_elisions', math.inf)
        if n < max_elisions:
            for i in range(0, n):
                self._output(context, OP.NONE, Part.ELISION, '', '...', depth)
        else:
            self._output(context, OP.NONE, Part.ELISION, '', f'... ({n} entries)', depth)

    def _output_diff(self, context: Any, key: str, diff: Any, op = OP.NONE, depth = 0):
        subvalue = None
        subdepth = depth+1

        typ = _extend_typeof(diff)
        if typ == 'object':
            if ('__old' in diff) and ('__new' in diff) and (len(diff) == 2):
                if _is_scalar(diff['__old']) and _is_scalar(diff['__new']):
                    return self._output(context, OP.MODIFY, Part.BODY, key, diff, depth)
                else:
                    self._output_diff(context, key, diff['__old'], OP.REMOVE, depth)
                    return self._output_diff(context, key, diff['__new'], OP.ADD, depth)
            else:
                self._output(context, op, Part.OBJECT_BEGIN, key, None, depth)
                for subkey in diff:
                    m = None
                    subvalue = diff[subkey]
                    m = re.match(r'^(.*)__deleted$', subkey)
                    if m:
                        self._output_diff(context, m[1], subvalue, OP.REMOVE, subdepth)
                    else:
                        m = re.match(r'^(.*)__added$', subkey)
                        if m:
                            self._output_diff(context, m[1], subvalue, OP.ADD, subdepth)
                        else:
                            self._output_diff(context, subkey, subvalue, op, subdepth)
                return self._output(context, op, Part.OBJECT_END, key, None, depth)

        elif typ == 'array':
            self._output(context, op, Part.ARRAY_BEGIN, key, None, depth)
        
            looks_like_diff = True
            for item in diff:
                if (_extend_typeof(item) != 'array') or not ((len(item) == 2) or ((len(item) == 1) and (item[0] == ' '))) or not (isinstance(item[0], str)) or (len(item[0]) != 1) or item[0] not in [' ', '-', '+', '~']:
                    looks_like_diff = False
        
            if looks_like_diff:
                subop = OP.NONE
                elision_count = 0
                for it in diff:
                    subop = it[0]
                    subvalue = it[1] if len(it) > 1 else None
                    if subop == OP.NONE and subvalue is None:
                        elision_count+=1
                    else:
                        if elision_count > 0:
                            self._output_elisions(context, elision_count, subdepth)
                        elision_count = 0
            
                        if subop not in [OP.NONE, OP.MODIFY, OP.ADD, OP.REMOVE]:
                            raise FormatterError(f'Unexpected op \'{subop}\' in {json.dumps(diff, indent="  ")}')
                        
                        if subop == OP.MODIFY:
                            subop = OP.NONE

                        self._output_diff(context, '', subvalue, subop, subdepth)

                        if elision_count > 0:
                            self._output_elisions(context, elision_count, subdepth)
            else:
                for subvalue in diff:
                    self._output_diff(context, '', subvalue, op, subdepth)
        
            return self._output(context, op, Part.ARRAY_END, key, None, depth)
        else:
            if diff == 0 or diff is None or diff == False or diff == '' or diff:
                return self._output(context, op, Part.BODY, key, diff, depth)

    def stringify(self, diff = None, opts = None):
        """
        Produces a human-readable diff text lines from a dict of differences created by Comparator.
        """
        if diff is None:
            diff = self.diff
        if opts is None:
            opts = self.opts

        if diff is None:
            return ''

        output = []

        def output_cb(op, line):
            nonlocal output

            line = f'{op}{line}'
            if self._get_opt('color', False):
                theme = self._get_opt('theme', Theme)
                if op in theme:
                    line = theme[op](line)
            output.append(line)

        self._output_diff({'output': output_cb}, '', diff)

        return '\n'.join(output)

    def __str__(self):
        return self.stringify()
