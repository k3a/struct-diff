import json
from typing import Any

from ..comparator import OP
from .base import BaseFormatter, Part

class YAMLFormatter(BaseFormatter):
    def __init__(self, diff = None, opts = None):
        super().__init__(diff, opts)

    def _output(self, context: dict, op: str, part: str, key: str, value: Any, depth: int):
        indent = '  '*depth
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
                    indent += '  '
            # object key
            if len(stack) > 0 and stack[-1] == 'object' and key != '':
                key_in_current_stack_object += 1

            #print(f"op {op} part {part} key {key} value {value} depth {depth}")
            output(op, indent + prefix + json.dumps(value))

        context['stack'] = stack
        context['key_in_current_stack_object'] = key_in_current_stack_object