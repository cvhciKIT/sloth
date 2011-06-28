def bind(fun, *args):
    return lambda: fun(*args)
