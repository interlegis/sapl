
import traceback

from django import apps
from django.conf import settings
from django.template.base import TOKEN_TEXT
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as django_ugettext_lazy


ExpressaoTextual = None


class ExpressaoTextualManage(object):
    __catalog = {'preprocess': [], 'indice': {}}

    def swap_translate(self, node):
        literal = node.filter_expression.var.literal
        swap = self._swap(literal)
        node.filter_expression.token = swap
        node.filter_expression.var.var = swap
        node.filter_expression.var.literal = swap
        return node

    def swap_block_translate(self, node):
        for item in node.singular + node.plural:
            if item.token_type != TOKEN_TEXT:
                continue
            item.contents = self._swap(item.contents)

        return node

    def swap_ugettext_lazy(self, proxy):
        return self._swap(proxy)

    def _swap(self, swap_value):

        msg = self._catalog(swap_value)

        """count = 0
        for key, expressao in indice.items():
            count += len(expressao['proxy'])
        print(count)"""
        return msg['custom'] if msg and msg['custom'] else swap_value

    def _catalog(self, item):
        global ExpressaoTextual
        if not ExpressaoTextual and apps.apps.models_ready:
            ExpressaoTextual = apps.apps.get_app_config(
                'base').get_model('ExpressaoTextual')

            exprs = ExpressaoTextual.objects.values_list('value', 'custom')
            try:
                expr = list(exprs)
            except:
                ExpressaoTextual = None
                self.__catalog['preprocess'].append(item)
                return None

            for value, custom in exprs:
                if value not in self.__catalog['indice']:
                    self.__catalog['indice'][value] = {
                        'proxy': [],
                        'value': value,
                        'custom': custom}

            for value in self.__catalog['preprocess']:
                text = force_text(value).strip()
                if not text:
                    continue
                if text in self.__catalog['indice']:
                    self.__catalog['indice'][text]['proxy'].append(value)
                else:
                    self.__catalog['indice'][text] = {
                        'proxy': [value, ],
                        'value': text,
                        'custom': None}
                    et = ExpressaoTextual(value=text, bind=True)
                    et.save()

            self.__catalog['preprocess'] = []

        elif not ExpressaoTextual:
            self.__catalog['preprocess'].append(item)
            return None

        indice = self.__catalog['indice']
        text = force_text(item).strip()
        if not text:
            return None
        msg = indice.get(text, None)
        if not msg:
            msg = indice[text] = {
                'proxy': [item, ],
                'value': text,
                'custom': None}
            et = ExpressaoTextual(value=text, bind=True)
            et.save()

        else:
            try:
                p = item._proxy____args
                trace = traceback.extract_stack()
                trace.reverse()
                while len(trace) > 0 and trace[0].filename != __file__:
                    trace.pop(0)

                while len(trace) > 0 and trace[0].filename == __file__:
                    trace.pop(0)

                if trace:
                    if trace[0].name == '<module>':
                        msg['proxy'].append(item)
            except:
                pass
        return msg

    def rebuild_expressao(self, et):
        catalog = self.__catalog
        value_catalog = catalog['indice'][et.value]
        value_catalog['custom'] = et.custom
        for p in catalog['indice'][et.value]['proxy']:
            try:
                p._proxy____args = (et.custom,)
            except:
                pass

    def rebuild(self):
        global ExpressaoTextual
        ExpressaoTextual.objects.update(bind=False)

        catalog = self.__catalog

        while catalog['preprocess']:
            proxy = catalog['preprocess'].pop(0)
            value = force_text(proxy).strip()
            if not value:
                continue

            if value in catalog['indice']:
                catalog['indice'][value]['proxy'].append(proxy)
            else:
                catalog['indice'][value] = {
                    'proxy': [proxy, ],
                    'value': value,
                    'custom': None}

        for key, exp in catalog['indice'].items():
            try:
                ex = ExpressaoTextual.objects.get(value=exp['value'])
            except:
                value = exp['value'].strip()
                if not value:
                    continue
                ex = ExpressaoTextual(value=exp['value'], custom='')
            ex.bind = True
            ex.save()

            if ex.custom:
                catalog['indice'][exp['value']]['custom'] = ex.custom
                for p in catalog['indice'][exp['value']]['proxy']:
                    try:
                        p._proxy____args = (ex.custom,)
                        print(p._proxy____args)
                    except:
                        print('text')

        ExpressaoTextual.objects.filter(bind=False).delete()


"""
        if sys.argv[1] == 'makemigrations':
            return
        # apps.apps.get_app_config('base').ready()
        ExpressaoTextual = apps.apps.get_app_config(
            'base').get_model('ExpressaoTextual')

        try:
            # modelo não existe no momento do migrate
            ExpressaoTextual.objects.update(bind=False)
        except:
            return

        expressoes = ExpressaoTextual.objects.all()

        for app in apps.apps.get_app_configs():
            if app.name not in settings.SAPL_APPS or app == self:
                continue

            for m in app.get_models():
                try:
                    exp = expressoes.get(value=m._meta.verbose_name)
                except:
                    exp = ExpressaoTextual(
                        value=m._meta.verbose_name, custom='')
                exp.bind = True
                exp.save()
                if exp.custom:
                    m._meta.verbose_name = exp.custom

                try:
                    exp = expressoes.get(value=m._meta.verbose_name_plural)
                except:
                    exp = ExpressaoTextual(
                        value=m._meta.verbose_name_plural, custom='')
                exp.bind = True
                exp.save()
                if exp.custom:
                    m._meta.verbose_name_plural = exp.custom

                for f in m._meta.fields:
                    try:
                        exp = expressoes.get(value=f.verbose_name)
                    except:
                        exp = ExpressaoTextual(
                            value=f.verbose_name, custom='')
                    exp.bind = True
                    exp.save()
                    if exp.custom:
                        f.verbose_name = exp.custom

        ExpressaoTextual.objects.filter(bind=False).delete()
"""

sapl_expressions = ExpressaoTextualManage()


def ugettext_lazy(message):
    proxy = django_ugettext_lazy(message)
    return sapl_expressions.swap_ugettext_lazy(proxy)
