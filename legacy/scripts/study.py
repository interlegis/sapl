from django.apps import apps

for model in apps.get_app_config('legacy').get_models():
    if 'ind_excluido' in [f.name for f in model._meta.fields]:
        print model, model.objects.values_list('ind_excluido', flat=True).distinct()
