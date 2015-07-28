from django.views.generic.base import TemplateView


class HelpView(TemplateView):

    def get_template_names(self):
        print(self.kwargs['topic'])
        return ['ajuda/%s.html' % self.kwargs['topic']]
