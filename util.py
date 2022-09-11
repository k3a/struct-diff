def is_scalar(value):
    """
    Primitive version, relying on the fact that JSON cannot
    contain any more complicated data structures.
    """
    return not isinstance(value, (list, tuple, dict))

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
