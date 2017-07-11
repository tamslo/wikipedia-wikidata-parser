from collections import OrderedDict


def first(gen, default_value=None):
    try:
        return next(gen)
    except StopIteration:
        return default_value


def flatten(l, remove_duplicates=False):
    flat_list = [item for sublist in l for item in sublist]
    if remove_duplicates:
        flat_list = list(OrderedDict.fromkeys(flat_list))

    return flat_list
