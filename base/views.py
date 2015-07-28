from django.views.generic.base import TemplateView


class HelpView(TemplateView):
    # XXX treat non existing template as a 404!!!!

    def get_template_names(self):
        print(self.kwargs['topic'])
        return ['ajuda/%s.html' % self.kwargs['topic']]
