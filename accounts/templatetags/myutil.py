# -*- coding: utf-8 -*-
"""
@author: mitsui
"""
import logging
import os
from datetime import datetime
from subprocess import check_output

import pytz
from django import template

from config.settings import BASE_DIR, VERSION

logger = logging.getLogger(__name__)

register = template.Library()

@register.simple_tag
def version_date():
    try:
        timezone = pytz.timezone("Asia/Tokyo")
        dt = datetime.fromtimestamp(os.stat(os.path.abspath(os.path.join(BASE_DIR, '.git'))).st_mtime, tz=timezone)
        name = dt.strftime('%Y-%m-%d %H:%M %Z')

    except Exception as e:
        logging.exception(e)
        return VERSION

        # return "%s %s-%s" % (VERSION, name, result.decode('utf-8'))
    return "%s Last Update: %s" % (VERSION, name)

@register.filter
def array_reverse(array):
    return array.reverse()

@register.filter
def remove_p(html):
    return html.replace('<p>', '').replace('</p>', '')

@register.filter
def remove_strong(html):
    return html.replace('<strong>', '').replace('</strong>', '')

@register.filter
def get_form_fields(form, arg):
    return form.fields[arg]

@register.filter
def get_form_choices(form, arg):
    return form.fields[arg].choices


@register.filter
def get_form_errors(form, arg):
    return form[arg].errors

@register.filter
def get_lang(data, lang):
    # 言語切替のため
    if not lang in data:
        lang = 'en'
    return data[lang]


@register.filter(name='lookup')
def lookup(value, arg, default=""):
    '''
    クラスメソッドのルックアップ
    :param value:
    :param arg:
    :param default:
    :return:
    '''
    if hasattr(value, arg):
        return getattr(value, arg)
    else:
        return default

@register.filter(name='lookup_arr')
def lookup_arr(value, arg):
    '''
    配列のルックアップ
    :param value:
    :param arg:
    :return:
    '''
    return value[arg]

@register.filter(name='lookup_arr_str')
def lookup_arr(value, arg):
    '''
    配列のルックアップ
    :param value:
    :param arg:
    :return:
    '''
    return value[str(arg)]

@register.filter
def str_format_old(formatstr, value):
    '''
    指定文字列のフォーマット
    :param formatstr:
    :param value:
    :return:
    '''
    return formatstr.format(value)

@register.filter
def str_format(formatstr, value):
    '''
    指定文字列のフォーマット
    :param formatstr:
    :param value:
    :return:
    '''
    return formatstr % value

@register.filter
def truncate(value, arg):
    return value[:int(arg)]

@register.filter
def cut_middle_truncate(value, arg):
    length = len(value)
    str = value[:int(arg)]
    length2 = length - int(arg)
    str = str + "..." + value[length2:]
    return str

@register.filter(name='range')
def _range(_min, args=None):
    _max, _step = None, None
    if args:
        if not isinstance(args, int):
            _max, _step = map(int, args.split(','))
        else:
            _max = args
    args = filter(None, (_min, _max, _step))
    return range(*args)


@register.filter
def split1_space(value):
    s = value.split(" ")
    return s[0]


@register.filter
def split2_space(value):
    s = value.split(" ")
    if len(s) > 1:
        return s[1]
    else:
        return ""

@register.filter
def split_20(value):
    s = value.replace(" ", "")
    return s[:20]

@register.filter
def split_20over(value):
    s = value.replace(" ", "")
    if len(s) > 20:
        return s[20:]
    return ""

@register.filter
def int_val(value):
    s = int(value)
    return s
