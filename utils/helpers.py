def first(gen, default_value=None):
    try:
        return next(gen)
    except StopIteration:
        return default_value
