KEY_TYPE        = '__type'
KEY_REMOVE      = '__remove'
KEY_APPEND      = '__append'
KEY_UPDATE      = '__update'
KEY_ORIGINAL    = '__original'
KEY_LENGTH      = '__length'
TYPE_OBJECT = 'object'
TYPE_ARRAY = 'array'

def is_changedict(d: dict) -> bool:
    """
    Returns True if d is a dict containing _remove, _append or _update keys
    """
    return isinstance(d, dict) and (KEY_REMOVE in d or KEY_APPEND in d or KEY_UPDATE in d or KEY_ORIGINAL in d)

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
