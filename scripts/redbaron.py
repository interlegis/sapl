import os
import re
import subprocess

from redbaron import RedBaron
from redbaron.nodes import EndlNode, ReturnNode, StringNode

git_project_root = subprocess.Popen(
    ["git", "rev-parse", "--show-toplevel"],
     stdout=subprocess.PIPE
     ).communicate()[0].decode('utf-8').replace('\n', '')


def ignorado(path, name):
    for pattern in [
        'legacy.*',
        'relatorios/templates.*',
        '.*/migrations',
    ]:
        if re.match(os.path.join(git_project_root, pattern), path):
            return True
    return name.startswith('ipython_log.py') or name == 'manage.py'


filenames = [os.path.join(path, name)
             for path, subdirs, files in os.walk(git_project_root)
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
    red = node.git_project_root
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
    res = '%s:%s' % (node.git_project_root.__filename__,
                     node.absolute_bounding_box.top_left.line)
    os.system("echo '%s' | xclip -selection c" % res)
    return res


def acha_props_constantes(red):
    "Enumera nós property que apenas retornam uma constante"
    for fun in red('def'):
        if fun.decorators.dumps().strip() == '@property':
            nos = [n for n in fun.value if not isinstance(n, EndlNode)]
            if len(nos) == 1:
                [ret] = nos
                if (isinstance(ret, ReturnNode)
                        and isinstance(ret.value, StringNode)):
                    yield fun


def corrige_props_constantes(reds):
    "Troca nós property que apenas retornam uma constante por um assign"
    pp = [p for red in reds for p in acha_props_constantes(red)]
    for p in pp:
        p.parent.value[p.index_on_parent] = '{} = {}'.format(p.name, p('return')('string').dumps())
        write(p)
