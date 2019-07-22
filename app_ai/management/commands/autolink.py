# -*- coding: utf-8 -*-
"""
    app_ai.management.commands

    書き起こしで作成されたJSONをDBに登録するコマンド

"""
import logging
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from app_admin.models.movie_models import UserMovie
from app_ai.models import AiMovie

logger = logging.getLogger(__name__)


def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


def set_data():

    with transaction.atomic():
        try:
            mvs = UserMovie.objects.filter(is_delete=False)
            for mv in mvs:
                filename, ext = os.path.splitext(mv.filename)
                # 動画の情報を保存
                aimv = get_or_none(AiMovie, name__contains=filename)
                if aimv:
                    aimv.user_movie_id = mv.id
                    aimv.name = mv.filename
                    aimv.unique_name = mv.unique_filename
                    aimv.save(update_fields=['user_movie_id', 'name', 'unique_name'])

        except Exception as e:
            logger.exception(e)
            print("%s" % e)


class Command(BaseCommand):
    help = "AIからのJSONをDBにフレームごとに保存する"

    def handle(self, *args, **options):

        self.output_transaction = True

        set_data()
