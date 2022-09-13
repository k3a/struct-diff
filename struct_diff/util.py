import math

def _is_scalar(value):
    """
    Primitive version, relying on the fact that JSON cannot
    contain any more complicated data structures.
    """
    return not isinstance(value, (list, tuple, dict))

def _prefix_lines(s: str, prefix: str, prefix_first_line=True) -> str:
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

def _extend_typeof(obj):
    if obj is None:
        return 'null'
    elif isinstance(obj, list):
        return 'array'
    elif isinstance(obj, dict):
        return 'object'
    else:
	    return type(obj).__name__

def _round_obj(data, precision):
    if isinstance(data, list):
        return [_round_obj(i, precision) for i in data]
    elif isinstance(data, dict):
        for k in data:
            data[k] = _round_obj(data[k], precision)
        return data
    elif isinstance(data, float) and math.isfinite(data):
        return round(data, precision)
    else:
        return data

def _get_opt(opts, key, default=False):
    if not opts:
        return default
    if isinstance(opts, dict):
        val = opts.get(key, default)
    else:
        val = getattr(opts, key, default)
    return val if val is not None else default

def _set_opt(opts, key, val):
    d = {}
    if not opts:
        return
    if isinstance(opts, dict):
        opts[key] = val
    else:
        setattr(opts, key, val)
