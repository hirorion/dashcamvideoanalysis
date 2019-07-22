# -*- coding: utf-8 -*-


class DbRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'app_admin' or model._meta.app_label == 'app_user':
            return 'default'
        if model._meta.app_label == 'app_ai':
            return 'ai'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'app_admin' or model._meta.app_label == 'app_user':
            return 'default'
        if model._meta.app_label == 'app_ai':
            return 'ai'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model=None, **hints):
        if app_label == 'auth' or app_label == 'auth' or app_label == 'contenttypes' or app_label == 'sessions' or app_label == 'update'  or app_label == 'accounts' or app_label == 'registration':
            return db == 'default'
        if app_label == 'app_admin' or app_label == 'app_user':
            return db == 'default'
        if app_label == 'app_ai':
            return db == 'ai'
        return None
