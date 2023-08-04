#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum
import math


class EnumBase(Enum):
    @classmethod
    def values(cls):
        return tuple(e.value for e in cls)


def upper_division(a, b):
    """向上取整数除法"""
    return math.ceil(a / b)


def uniform_distribute(objs, parts):
    """对列表中元素进行均匀分配"""
    if not isinstance(objs, list):
        raise TypeError('objs require list type, got {} instead'.format(type(objs)))
    if not isinstance(parts, int) or parts < 1:
        raise ValueError('parts require integer > 0, got {} instead'.format(parts))
    distribution = [[] for _ in range(parts)]
    for i, _ in enumerate(objs):
        dis_index = i % parts
        distribution[dis_index].append(objs[i])

    return distribution
