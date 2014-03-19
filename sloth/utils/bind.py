def bind(fun, *args):
    return lambda: fun(*args)


def compose_noargs(funs):
    def tmp():
        for f in funs:
            f()
    return tmp


def compose(funs):
    def tmp(*args, **kwargs):
        for f in funs:
            f(*args, **kwargs)
    return tmp
