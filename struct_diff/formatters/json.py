import json
from typing import Any

from ..comparator import OP
from .base import BaseFormatter, Part

class JSONFormatter(BaseFormatter):
    def __init__(self, diff = None, opts = None):
        super().__init__(diff, opts)

    def _output(self, context: Any, op: str, part: str, key: str, value: Any, depth: int):
        if op == OP.MODIFY:
            # split modify into two outputs for removal and add
            self._output(context, OP.REMOVE, part, key, value['__old'], depth)
            self._output(context, OP.ADD, part, key, value['__new'], depth)
            return

        indent_str = ' '*self._get_opt('indent_width', 2)
        indent = indent_str*depth
        prefix = f'{key}: ' if key else ''

        output = context['output']

        if part == Part.OBJECT_BEGIN:
            output(op, indent + prefix + '{')
        elif part == Part.OBJECT_END:
            output(op, indent + '}')
        elif part == Part.ARRAY_BEGIN:
            output(op, indent + prefix + '[')
        elif part == Part.ARRAY_END:
            output(op, indent + ']')
        elif part == Part.ELISION:
            output(op, indent + value)
        else:
            #print(f"op {op} part {part} key {key} value {value} depth {depth}")
            output(op, indent + prefix + json.dumps(value))
