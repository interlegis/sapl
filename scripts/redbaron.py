import os
import re

from redbaron import RedBaron

root = '/home/mazza/work/sapl'


def ignorado(path, name):
    for pattern in [
        'legacy.*',
        'relatorios/templates.*',
        '.*/migrations',
    ]:
        if re.match(os.path.join(root, pattern), path):
            return True
    return name.startswith('ipython_log.py') or name == 'manage.py'


filenames = [os.path.join(path, name)
             for path, subdirs, files in os.walk(root)
             for name in files
             if name.endswith('.py') and not ignorado(path, name)]


def build_red(filename):
    with open(filename, "r") as source_code:
        red = RedBaron(source_code.read())
        if red.data:
            red.__filename__ = filename
            return red

# reds = [build_red(f) for f in filenames]
# reds_without_tests = [r for r in reds
#                       if not re.match('.*/test_.*\.py', r.__filename__)]


def write(node):
    red = node.root
    with open(red.__filename__, "w") as source_code:
        source_code.write(red.dumps())


##############################################################################
# verificacoes ad-hoc

def flat(ll):
    return [i for l in ll for i in l]


def inter(n):
    'Se a string n esta dentro de uma chamada de traducao'
    try:
        assert not n.next or n.next.type == 'string'
        assert n.parent_find('call').parent.value[0].value == '_'
        return True
    except:
        return False


def frase(n):
    return ' ' in n.value


def mark(n):
    mark.ok |= {n.value}
mark.ok = set()


def get(r):
    return [s for s in r('string')
            if not inter(s) and s.value not in mark.ok]
    # and frase(s)


def fix(n):
    n.value = '_(%s)' % n.value
    write(n)


def local(node):
    res = '%s:%s' % (node.root.__filename__,
                     node.absolute_bounding_box.top_left.line)
    os.system("echo '%s' | xclip -selection c" % res)
    return res
