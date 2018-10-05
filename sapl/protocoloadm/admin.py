from sapl.utils import register_all_models_in_admin

register_all_models_in_admin(__name__, exclude_list=['timestamp',
                                                     'data',
                                                     'hora',
                                                     'timestamp_anulacao'])
