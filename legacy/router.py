class LegacyRouter(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'legacy':
            return 'legacy'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'legacy':
            return 'legacy'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'legacy' \
                and obj2._meta.app_label == 'legacy':
            return True
        return None

    def allow_migrate(self, db, model):
        if model._meta.app_label == 'legacy':
            return False
        return None
