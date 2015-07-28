import copy
import logging

from django.utils.log import DEFAULT_LOGGING

# hack to suppress many annoying warnings from crispy_forms
#   Do remove this file and corresponding import in settings
#   when crispy_forms is corrected !!!
SUPRESS_CRISPY_FORM_WARNINGS_LOGGING = copy.deepcopy(DEFAULT_LOGGING)
SUPRESS_CRISPY_FORM_WARNINGS_LOGGING['filters']['suppress_deprecated'] = {
    '()': 'sapl.temp_suppress_crispy_form_warnings.SuppressDeprecated'
}
SUPRESS_CRISPY_FORM_WARNINGS_LOGGING['handlers']['console']['filters'].append(
    'suppress_deprecated')


class SuppressDeprecated(logging.Filter):

    def filter(self, record):
        msg = record.getMessage()
        return not ('crispy_forms' in msg and
                    'RemovedInDjango19Warning' in msg)
