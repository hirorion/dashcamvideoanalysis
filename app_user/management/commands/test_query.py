# -*- coding: utf-8 -*-
"""
    deployment.management.commands

    @author: $Author$
    @version: $Id$

"""
import logging

from django.core.management.base import BaseCommand
from app_admin.models.movie_models import UserMovie

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "userのパスワードをリセットする"

    def handle(self, *args, **options):

        movie_query = UserMovie.objects
        movie_data = movie_query.filter(id=20)
        if movie_data.count() != 1:
            print("movie not exists")
        else:
            print(movie_data[0].status)

        try:
            #movie_data = movie_query.get(id=21)
            raise FileExistsError("aaa")

        except UserMovie.DoesNotExist as e:
            print("movie not exists")
            exit(1)
        except Exception as e:
            print("Exception")
            exit(1)

        print(movie_data.status)


