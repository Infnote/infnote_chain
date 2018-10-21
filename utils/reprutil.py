from functools import reduce


def flat_dict_for_repr(value: dict, initial='', indent=0) -> str:
    if not isinstance(value, dict):
        return f'{value}'

    def max_width_cal(r, x):
        return r if r > len(x) else len(x)

    max_width = reduce(max_width_cal, value, 0)
    result = initial
    for k, v in value.items():
        if isinstance(v, dict):
            v = flat_dict_for_repr(v, '\n', indent + 4)
        elif isinstance(v, list):
            tmp = ''
            for item in v:
                tmp += flat_dict_for_repr(item, '\n', indent + 4)
            v = tmp
        elif isinstance(v, str):
            if len(v) > 150:
                v = v[:150]
        result += f'{" " * indent}[{k}{" " * (max_width - len(k))}] {v}\n'
    return result
