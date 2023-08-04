#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import OrderedDict

from nebula3.data.DataObject import ValueWrapper

from ngsm.base import Setting
from ngsm.model import SchemaModel
from ngsm.model import NDataTypes
from ngsm.tool import upper_division
from ngsm.tool import uniform_distribute


class ValueFormatter:

    ValueWrapper2Parser = {
        NDataTypes.INT.value: ValueWrapper.as_int,
        NDataTypes.INT8.value: ValueWrapper.as_int,
        NDataTypes.INT16.value: ValueWrapper.as_int,
        NDataTypes.INT32.value: ValueWrapper.as_int,
        NDataTypes.INT64.value: ValueWrapper.as_int,
        NDataTypes.STRING.value: ValueWrapper.as_string,
        NDataTypes.BOOL.value: ValueWrapper.as_bool,
        NDataTypes.FLOAT.value: ValueWrapper.as_double,
        NDataTypes.DOUBLE.value: ValueWrapper.as_double,
        NDataTypes.TIMESTAMP.value: ValueWrapper.as_int  # todo: use ValueWrapper.as_time
    }

    Value2Formatter = {
        NDataTypes.INT.value: str,
        NDataTypes.INT8.value: str,
        NDataTypes.INT16.value: str,
        NDataTypes.INT32.value: str,
        NDataTypes.INT64.value: str,
        NDataTypes.STRING.value: lambda x: '\"{}\"'.format(str(x)),
        NDataTypes.BOOL.value: lambda x: 'true' if x else 'false',
        NDataTypes.FLOAT.value: str,
        NDataTypes.DOUBLE.value: str,
        NDataTypes.TIMESTAMP.value: str
    }

    @classmethod
    def _parse_value_wrapper(cls, v: ValueWrapper, dt, support_null: bool = True):
        if support_null:
            if v.is_null():
                return None
        if dt not in cls.ValueWrapper2Parser.keys():
            raise ValueError('not support parse {} yet'.format(dt))

        return cls.ValueWrapper2Parser[dt](v)

    @classmethod
    def is_null(cls, g_value: ValueWrapper):
        return g_value.is_null()

    @classmethod
    def parse(cls, d_t, g_value: ValueWrapper, support_null: bool = True):
        # 从图数据库中获取的ValueWrapper转py数据类型
        return cls._parse_value_wrapper(dt=d_t, v=g_value, support_null=support_null)

    @classmethod
    def parse_from_string(cls, g_value: ValueWrapper, support_null: bool = True):
        """常用解码函数"""
        return cls._parse_value_wrapper(dt=NDataTypes.STRING.value, v=g_value, support_null=support_null)

    @classmethod
    def parse_from_int(cls, g_value: ValueWrapper, support_null: bool = True):
        """常用解码函数"""
        return cls._parse_value_wrapper(dt=NDataTypes.INT.value, v=g_value, support_null=support_null)

    @classmethod
    def encode(cls, d_t, py_value):
        # 从py数据类型转化为输入到图数据库中nGQL语句的形式
        if d_t not in cls.Value2Formatter.keys():
            raise ValueError('{} is not support to encode yet'.format(d_t))
        return cls.Value2Formatter[d_t](py_value)

    @classmethod
    def encode_into_string(cls, py_value):
        """常用编码函数"""
        return cls.encode(d_t=NDataTypes.STRING.value, py_value=py_value)

    @classmethod
    def encode_into_int(cls, py_value):
        """常用编码函数"""
        return cls.encode(d_t=NDataTypes.INT.value, py_value=py_value)

    @classmethod
    def parse_vid(cls, g_vid: ValueWrapper, vid_type_is_fixed_string: bool = True):
        if vid_type_is_fixed_string:
            return g_vid.as_string()
        else:
            return g_vid.as_int()

    @classmethod
    def encode_vid(cls, py_vid, vid_type_is_fixed_string: bool = True):
        if vid_type_is_fixed_string:
            return '\"{}\"'.format(str(py_vid))
        else:
            return str(py_vid)

    @classmethod
    def encode_uuid(cls, value):
        return cls.encode(d_t=NDataTypes.STRING.value, py_value=value)

    @classmethod
    def parse_uuid(cls, value):
        return cls.parse(d_t=NDataTypes.STRING.value, g_value=value, support_null=False)

    @classmethod
    def edge(cls, edge_info: (tuple, list)):
        """
        :param edge_info: (v1.vid, edge_type, v2.vid)/[v1.vid, edge_type, v2.vid]
        """
        return '{} -> {}@{}'.format(cls.encode_vid(edge_info[0]),
                                    cls.encode_vid(edge_info[2]),
                                    edge_info[1]) if len(edge_info) == 3 else ''

    @classmethod
    def encode_property(cls, prop_name, value, schema: SchemaModel):
        return cls.encode(d_t=schema.property_type(prop_name), py_value=value)

    @classmethod
    def parse_property(cls, prop_name, value, schema: SchemaModel):
        return cls.parse(d_t=schema.property_type(prop_name), g_value=value)

    @classmethod
    def encode_properties(cls, prop: dict, schema: SchemaModel):
        return {k: cls.encode(d_t=schema.property_type(k), py_value=v) for k, v in prop.items()}

    @classmethod
    def parse_properties(cls, prop: dict, schema: SchemaModel, for_display=True, with_order=True):
        """转化节点或边属性"""
        result = dict() if not with_order else OrderedDict()
        for k, v in prop.items():
            new_k = schema.property_display(k) if for_display else k
            if new_k is None and for_display:
                # 面向用户不展示id、uuid等信息
                continue
            v = cls.parse(d_t=schema.property_type(k), g_value=v, support_null=schema.property_support_null(k))
            if v is None and for_display:
                v = '-'
            result.update({new_k: ' {}'.format(v) if for_display else v})
        return result


class StmtFormatter:

    @classmethod
    def parts_should_split_of_stmt(cls, fix_part: str, multi_part: list):
        """返回应该将过长的语句均分的份数"""
        return upper_division(len(fix_part) + sum([len(part) for part in multi_part]),
                              Setting.max_stmt_length)

    @classmethod
    def split_into_parts(cls, multi_parts, parts_num):
        return uniform_distribute(objs=multi_parts, parts=parts_num)
