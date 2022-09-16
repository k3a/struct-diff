import difflib
import re
from typing import Any

from ..comparator import OP
from .base import BaseFormatter, Part

class YAMLFormatter(BaseFormatter):
    def __init__(self, diff = None, opts = None):
        # https://yaml.org/spec/1.2.2/#plain-style
        self.re_unsafe_str = re.compile(r'^([,\[\]{}#&*!|>\'"%@`\s]|[-?:]\s)')
        super().__init__(diff, opts)

    def _text_diff(self, prev_val: str, cur_val: str, indent_str: str, depth: int) -> list[str]:
        """Creates a simplified unified diff and returns its string representation"""
        prev_lines = (prev_val+'\n').splitlines(keepends=True)
        cur_lines = (cur_val+'\n').splitlines(keepends=True)
        d = list(difflib.unified_diff(prev_lines, cur_lines, n=1))
        if len(d) > 3:
            # strip header
            d = d[3:]
        if depth>0:
            # append depth
            for n in range(len(d)):
                l = d[n]
                if len(l) > 0:
                    d[n] = l[0] + indent_str*depth + l[1:]
        return d[:-1]

    def _format_scalar(self, val: Any) -> str:
        if isinstance(val, int):
            return str(val)
        elif isinstance(val, float):
            prec = self._get_opt('precision', None)
            return str(round(val, prec)) if prec is not None else str(val)
        else:
            s = str(val)
            if self.re_unsafe_str.match(s):
                s = "'" + s + "'"
            return s

    def _output(self, context: dict, op: str, part: str, key: str, value: Any, depth: int):
        if op == OP.MODIFY:
            old = value['__old']
            new = value['__new']
            # split non-multiline modify into two outputs for removal and add
            if not (isinstance(old, str) and isinstance(new, str) and '\n' in new.rstrip()):
                self._output(context, OP.REMOVE, part, key, value['__old'], depth)
                self._output(context, OP.ADD, part, key, value['__new'], depth)
                return

        indent_str = ' '*self._get_opt('indent_width', 1)
        indent = indent_str*depth
        prefix = f'{key}: ' if key else ''

        stack = context.get('stack', [])
        key_in_current_stack_object = context.get('key_in_current_stack_object', 0)
        output = context['output']
        
        if part == Part.OBJECT_BEGIN:
            stack.append('object')
            key_in_current_stack_object = 0
            if key != '':
                output(op, indent + prefix)
        elif part == Part.OBJECT_END:
            stack.pop()
        elif part == Part.ARRAY_BEGIN:
            stack.append('array')
            if key != '':
                output(op, indent + prefix)
        elif part == Part.ARRAY_END:
            stack.pop()
        elif part == Part.ELISION:
            output(op, indent + value)
        else:
            # array element
            if len(stack) > 0 and stack[-1] == 'array':
                prefix += '- '
            if len(stack) > 1 and stack[-1] == 'object' and stack[-2] == 'array':
                indent = indent[0:-2]
                if key_in_current_stack_object == 0:
                    prefix = f'- {key}: '
                else:
                    indent += indent_str
            # object key
            if len(stack) > 0 and stack[-1] == 'object' and key != '':
                key_in_current_stack_object += 1

            if op == OP.MODIFY:
                # the second check for OP_MODIFY, now it is surely multi-line
                diff_lines = self._text_diff(old, new, indent_str, depth+1)
                if depth > 0:
                    # print YAML multiline string header
                    output(OP.NONE, indent + prefix + '|-')
                for dl in diff_lines:
                    op = OP.NONE
                    if dl[0] == '+':
                        op = OP.ADD
                    elif dl[0] == '-':
                        op = OP.REMOVE
                    output(op, dl[1:-1])
                return

            #print(f"op {op} part {part} key {key} value {value} depth {depth}")
            output(op, indent + prefix + self._format_scalar(value))

        context['stack'] = stack
        context['key_in_current_stack_object'] = key_in_current_stack_object