from django.apps import apps

from sapl.legacy.migracao import legacy_app

for model in apps.get_app_config('legacy').get_models():
    if 'ind_excluido' in [f.name for f in model._meta.fields]:
        print(model, model.objects.values_list(
            'ind_excluido', flat=True).distinct())

legacy_models_without_ind_excluido = [
    m for m in legacy_app.models.values()
    if not any(f.name == 'ind_excluido' for f in m._meta.fields)]
