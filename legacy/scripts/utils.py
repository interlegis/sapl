import inspect


def listify(function):
    def f(*args, **kwargs):
        return list(function(*args, **kwargs))
    return f


def getsourcelines(model):
    return [line.rstrip('\n').decode('utf-8')
            for line in inspect.getsourcelines(model)[0]]
