def listify(function):
    def f(*args, **kwargs):
        return list(function(*args, **kwargs))
    return f
