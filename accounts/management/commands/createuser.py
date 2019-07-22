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
    help = "一般ユーザーを作成する"

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')
        parser.add_argument('group_id')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        group_id = options['group_id']

        try:
            # システム管理者で操作したことにする
            Users.objects.create_user(username=username, password=password, group_id=group_id, created_user_id=1, updated_user_id=1)

        except Exception as e:
            logger.exception(e)
            print("%s" % e)
