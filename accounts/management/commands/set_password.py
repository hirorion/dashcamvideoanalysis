# -*- coding: utf-8 -*-
"""
    deployment.management.commands

    @author: $Author$
    @version: $Id$

"""
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Users

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "userのパスワードをリセットする"

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')

    @transaction.non_atomic_requests
    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        transaction.set_autocommit(False)
        try:
            user = Users.objects.filter(username=username).first()
            user.set_password(password)
            user.updated_user_id = 1  # システム管理者
            user.save()

        except Exception as e:
            transaction.rollback()
            logger.exception(e)
            print("%s" % e)

        finally:
            transaction.commit()
            transaction.set_autocommit(True)
