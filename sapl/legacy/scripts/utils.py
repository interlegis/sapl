import inspect


def getsourcelines(model):
    return [line.rstrip('\n').decode('utf-8')
            for line in inspect.getsourcelines(model)[0]]
