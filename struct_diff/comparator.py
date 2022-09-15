from difflib import SequenceMatcher
import json
from enum import Enum

from .util import _extend_typeof, _round_obj, _get_opt

class OP:
    NONE = ' '
    ADD = '+'
    REMOVE = '-'
    MODIFY = '~'

class ParserError(ValueError):
    pass

class Comparator(object):
    def __init__(self, opts=None):
        self.opts = opts

    def _get_opt(self, key, default=False):
        return _get_opt(self.opts, key, default)

    def __is_scalar(self, obj):
        return not isinstance(obj, (list, dict)) or obj is None

    def object_diff(self, obj1, obj2):
        """ Compare two dicts and return {score, equal, result} dict """
        result = {}
        score = 0
        equal = True

        for key, value in obj1.items():
            if not self._get_opt('output_new_only'):
                postfix = '__deleted'
            
                if key not in obj2:
                    result[f'{key}{postfix}'] = value
                    score -= 30
                    equal = False

        for key, value in obj2.items():
            postfix = '__added' if not self._get_opt('output_new_only') else ''

            if key not in obj1:
                result[f'{key}{postfix}'] = value
                score -= 30
                equal = False

        scalars_changed = False
        for key, value1 in obj1.items():
            if key in obj2:
                score += 20
                value2 = obj2[key]
                change = self.diff(value1, value2)
                if not change['equal']:
                    result[key] = change['result']
                    equal = False
                    if self.__is_scalar(value2):
                        scalars_changed = True
                elif self._get_opt('full') or key in self._get_opt('output_keys', []):
                    result[key] = value1
                    score += min(20, max(-10, change['score'] / 5)) # BATMAN!

        # include sigling keys of an object with diffs
        if scalars_changed and self._get_opt('object_context'):
            for key, value1 in obj1.items():
                if key not in result:
                    result[key] = value1
                    score += min(20, max(-10, change['score'] / 5)) # DOUBLE BATMAN!

        if equal:
            score = 100 * max(len(obj1), 0.5)
            if not self._get_opt('full'):
                result = None
        else:
            score = max(0, score)   
        return { 'score': score, 'result': result, 'equal': equal }

    def _find_matching_object(self, item, index, fuzzy_originals):
        best_match = None

        for key, it in fuzzy_originals.items():
            if key != '__next':
                candidate = it['item']
                match_index = it['index']
                index_distance = abs(match_index - index)
                if _extend_typeof(item) == _extend_typeof(candidate):
                    score = self.diff(item, candidate)['score']
                    if not best_match or \
                        score > best_match['score'] or \
                        (score == best_match['score'] and
                        index_distance < best_match['index_distance']):
                            best_match = { 'score': score, 'key': key, 'index_distance': index_distance }

        return best_match

    def _scalarize(self, array, originals, fuzzy_originals=False):
        fuzzy_matches = {}
        if fuzzy_originals:
            # Find best fuzzy match for each object in the array
            key_scores = {}
            for index in range(0, len(array)):
                item = array[index]
                if self.__is_scalar(item):
                    continue
                best_match = self._find_matching_object(item, index, fuzzy_originals)
                best_match_key = best_match['key'] if best_match else None
                if best_match and (best_match_key not in key_scores or best_match['score'] > key_scores[best_match_key]['score']):
                    key_scores[best_match_key] = { 'score': best_match['score'], 'index': index }
            for key, match in key_scores.items():
                fuzzy_matches[match['index']] = key
    
        result = []
        for index in range(0, len(array)):
            item = array[index]
            if self.__is_scalar(item):
                result.append(item)
            else:
                def incr_return_old(d, key):
                    old = d[key]
                    d[key] = old+1
                    return old
                key = index in fuzzy_matches and fuzzy_matches[index] or '__$!SCALAR' + str(incr_return_old(originals, '__next'))
                originals[key] = { 'item': item, 'index': index }
                result.append(key)
        return result

    def _is_scalarized (self, item, originals):
        return isinstance(item, str) and item in originals

    def _descalarize(self, item, originals):
        if self._is_scalarized(item, originals):
            return originals[item]['item']
        else:
            return item

    def array_diff(self, obj1, obj2):
        """ Compare two arrays and return {score, equal, result} dict """
        originals1 = { '__next': 1 }
        seq1 = self._scalarize(obj1, originals1)
        originals2 = { '__next': originals1['__next'] }
        seq2 = self._scalarize(obj2, originals2, originals1)
    
        if self._get_opt('sort'):
            def mixd(num):
                try:
                    el = int(num)
                    return (0, el)
                except:
                    return (1, num)
            # json_diff in JS sorts alphanumerically (key=str)
            # it should probably use a mixed method (key=mixd) instead
            seq1.sort(key=mixd)
            seq2.sort(key=mixd)

        opcodes = SequenceMatcher(None, seq1, seq2).get_opcodes()
    
        result = []
        score = 0
        equal = True
    
        for op, i1, i2, j1, j2 in opcodes:
            i, j = (0, 0)
            asc, end = (0, 0)
            asc1, end1 = (0, 0)
            asc2, end2 = (0, 0)
            if not (op == 'equal' or (self._get_opt('keys_only') and op == 'replace')):
                equal = False
        
            if op == 'equal':
                end = i2
                asc = i1 <= end
                for i in range(i1, end, 1 if asc else -1):
                    item = seq1[i]
                    if self._is_scalarized(item, originals1):
                        if not self._is_scalarized(item, originals2):
                            raise ParserError(f'internal bug: is_scalarized(item, originals1) != is_scalarized(item, originals2) for item {json.dumps(item, indent=2)}')
                        item1 = self._descalarize(item, originals1)
                        item2 = self._descalarize(item, originals2)
                        change = self.diff(item1, item2)
                        if not change['equal']:
                            result.append([OP.MODIFY, change['result']])
                            equal = False
                        else:
                            if self._get_opt('full') or self._get_opt('keep_unchanged_values'):
                                result.append([OP.NONE, item1])
                            else:
                                result.append([OP.NONE])
                    else:
                        if self._get_opt('full') or self._get_opt('keep_unchanged_values'):
                            result.append([OP.NONE, item])
                        else:
                            result.append([OP.NONE])
                    score += 10
            elif op == 'delete':
                end1 = i2
                asc1 = i1 <= end1
                for i in range(i1, end1, 1 if asc1 else -1):
                    result.append([OP.REMOVE, self._descalarize(seq1[i], originals1)])
                    score -= 5
            elif op == 'insert':
                end2 = j2
                asc2 = j1 <= end2
                for j in range(j1, end2, 1 if asc2 else -1):
                    result.append([OP.ADD, self._descalarize(seq2[j], originals2)])
                    score -= 5
            elif op == 'replace':
                if not self._get_opt('keys_only'):
                    asc3, end3 = (0, 0)
                    asc4, end4 = (0, 0)
                    end3 = i2
                    asc3 = i1 <= end3
                    for i in range(i1, end3, 1 if asc3 else -1):
                        result.append([OP.REMOVE, self._descalarize(seq1[i], originals1)])
                        score -= 5
                    end4 = j2
                    asc4 = j1 <= end4
                    for j in range(i1, end4, 1 if asc4 else -1):
                        result.append([OP.ADD, self._descalarize(seq2[j], originals2)])
                        score -= 5
                else:
                    asc5, end5 = (0, 0)
                    end5 = i2
                    asc5 = i1 <= end5
                    for i in range(i1, end5, 1 if asc5 else -1):
                        change = self.diff(
                            self._descalarize(seq1[i], originals1),
                            self._descalarize(seq2[i - i1 + j1], originals2)
                        )
                        if not change['equal']:
                            result.append([OP.MODIFY, change['result']])
                            equal = False
                        else:
                            result.append([OP.NONE])
        
        if equal or len(opcodes) == 0:
            if not self._get_opt('full'):
                result = None
            else:
                result = obj1
            score = 100
        else:
          score = max(0, score)
    
        return { 'score': score, 'result': result, 'equal': equal }

    def diff(self, obj1, obj2):
        """ Compare two objects of any type and return a dict with differences """
        type1 = _extend_typeof(obj1)
        type2 = _extend_typeof(obj2)
    
        if type1 == type2:
            if type1 == 'object':
                return self.object_diff(obj1, obj2)
            elif type1 == 'array':
                return self.array_diff(obj1, obj2)
    
        # Compare primitives or complex objects of different types
        score = 100
        result = obj1
        equal = False
        if not self._get_opt('keys_only', False):
            equal = obj1 == obj2
            if not equal:
                score = 0
        
                if self._get_opt('output_new_only', False):
                    result = obj2
                else:
                    result = { '__old': obj1, '__new': obj2 }
            elif not self._get_opt('full', False):
                result = None
        else:
            equal = True
            result = None
    
        return { 'score': score, 'result': result, 'equal': equal }

def diff(obj1, obj2, opts = None):
    """
    Compare two objects and return a dict with differences
    """
    p = _get_opt(opts, 'precision', None)
    if p is not None:
        obj1 = _round_obj(obj1, p)
        obj2 = _round_obj(obj2, p)
    return Comparator(opts).diff(obj1, obj2)['result']
