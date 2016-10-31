import ast
import inspect
import os


if __name__ == '__main__':

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")
    django.setup()

if True:
    from scripts.lista_urls import lista_urls


def get_decorators(cls):
    target = cls
    decorators = {}

    def visit_FunctionDef(node):
        decorators[node.name] = []
        for n in node.decorator_list:
            name = ''
            if isinstance(n, ast.Call):
                name = n.func.attr if isinstance(
                    n.func, ast.Attribute) else n.func.id
            else:
                name = n.attr if isinstance(n, ast.Attribute) else n.id

            decorators[node.name].append(name)

    node_iter = ast.NodeVisitor()
    node_iter.visit_FunctionDef = visit_FunctionDef
    node_iter.visit(ast.parse(inspect.getsource(target)))
    return decorators


def get_permission_requireds(cls):
    target = cls
    decorators = []

    def get_permission_required(arg):

        for perm in arg.args:

            if isinstance(perm, ast.Str):
                decorators.append(getattr(perm, perm._fields[0]))
                continue

            if isinstance(perm, (ast.Tuple, ast.List)):
                if 'elts' not in perm._fields:
                    continue

                for elt in perm.elts:

                    if isinstance(elt, ast.Str):
                        decorators.append(getattr(elt, elt._fields[0]))

    def get_method_decorator(n):
        for arg in n.args:

            if not isinstance(arg, ast.Call):
                continue

            """
            Espera-se que:
            - o decorator seja uma função
            - esta função tenha o meta atributo 'id'
            - id = 'permission_required'
            - esta função tenha argumento args
            """
            if ('func' not in arg._fields or
                    'id' not in arg.func._fields or
                    arg.func.id != 'permission_required' or
                    'args' not in arg._fields):
                continue

            get_permission_required(arg)

    def visit_FunctionDef(node):
        for n in node.decorator_list:
            if not isinstance(n, ast.Call):
                continue

            """
            Espera-se que:
            - o decorator seja uma função
            - esta função tenha o meta atributo 'id'
            - id = 'method_decorator'
            - esta função tenha argumento args
            """
            if ('func' not in n._fields or
                    'id' not in n.func._fields or
                    n.func.id != 'method_decorator' or
                    'args' not in n._fields):
                get_permission_required(n)
            else:
                get_method_decorator(n)

    node_iter = ast.NodeVisitor()
    node_iter.visit_FunctionDef = visit_FunctionDef
    node_iter.visit(ast.parse(inspect.getsource(target)))
    return decorators


class ListaPermissionInDecorators():
    decorators = []

    def lista_permissions_in_decorators(self):
        urls = lista_urls()

        for url_item in urls:
            key, url, var, app_name = url_item
            if hasattr(key, 'view_class'):
                view = key.view_class
            elif hasattr(key, 'cls'):
                view = key.cls
            else:
                view = key

            if not view.__module__.startswith('sapl.'):
                continue

            try:
                decorators = list(map(lambda x: (x, view),
                                      get_permission_requireds(view)
                                      ))
                self.decorators += decorators
            except:
                pass
        return self.decorators

    def __call__(self):
        return self.lista_permissions_in_decorators()


lista_permissions_in_decorators = ListaPermissionInDecorators()

if __name__ == '__main__':
    _lista_permissions_in_decorators = lista_permissions_in_decorators()
    print(_lista_permissions_in_decorators)
