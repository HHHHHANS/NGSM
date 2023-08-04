#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from types import FunctionType
from types import MethodType
from typing import List

import attr
from attr import validators

from ngsm.base import NDataTypes
from ngsm.base import NType2Validator
from ngsm.base import Setting
from ngsm.base import Const


def build_id(schema_name: str, _str_things: (List[str], str)):
    _s = [schema_name]
    _s.extend([_str_things] if isinstance(_str_things, str) else _str_things)
    return Const.vid_joiner.join(_s)


def build_index_name(schema_name: str, schema_type: str, properties: list = None):
    return 'i_{}{}'.format('{}_{}'.format(schema_type[0], schema_name),
                           '' if properties is None else '_P_{}'.format('_'.join([p.name for p in properties])))


@attr.s(eq=False, hash=False)
class PropertySchemaModel:
    """
    定义属性
    https://docs.nebula-graph.com.cn/3.2.0/3.ngql-guide/10.tag-statements/1.create-tag/
    """
    # 属性名称
    name = attr.ib(type=str, converter=lambda x: Setting.is_retain_keyword(x),
                   validator=validators.instance_of(str))
    # 属性类型
    type = attr.ib(type=str, validator=validators.in_(NDataTypes.values()))
    # 属性是否支持空值
    support_null = attr.ib(type=bool, default=True)
    # 是否设置默认值，默认不设置
    set_default = attr.ib(type=bool, default=False)
    # 默认值，默认为空
    default = attr.ib(type=(str, int, float, None), default=None)
    # 是否建立原生索引
    index = attr.ib(type=bool, default=False)
    # 属性展示时的key
    display = attr.ib(type=(str, None), validator=validators.instance_of((str, Const.TypeOfNone)), default='')
    # 属性备注信息
    comment = attr.ib(type=str, validator=validators.instance_of(str), default='')

    def __attrs_post_init__(self):
        if self.display == '':
            self.display = self.name
        if not self.support_null and self.set_default and self.default is None:
            # 属性值不能为空值，但默认值没有设置
            raise ValueError('property: \'{}\' does not support None value '
                             'but got None as default value'.format(self.name))
        if self.default is not None:
            checker = NType2Validator.get(self.type)
            if not checker:
                raise ValueError('{} has not checker yet'.format(self.type))
            checker(None, self, self.default)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if other.__class__ == self.__class__:
            if other.name == self.name:
                return True
        return False

    def __hash__(self):
        return self.name.__hash__()

    @classmethod
    def property_for_schema_validator(cls, instance, attribute, value):
        if value.__class__ != cls:
            raise TypeError('require {} type, got {} instead, '
                            'detail: {} of {}'.format(cls, type(value), attribute, instance))
        if value.type not in NDataTypes.values():
            raise ValueError('{} is not a acceptable type for schema, '
                             'detail: {} of {}'.format(value, attribute, instance))


@attr.s(repr=False, eq=False, hash=False)
class SchemaModel:
    """
    https://docs.nebula-graph.com.cn/3.2.0/3.ngql-guide/10.tag-statements/1.create-tag/
    ** 暂不开放设置过期属性 **
    """
    # 名称
    name = attr.ib(type=str, converter=lambda x: Setting.is_retain_keyword(x),
                   validator=validators.instance_of(str))
    # 属性定义
    properties = attr.ib(type=List[PropertySchemaModel],
                         converter=lambda x: list(set(x)),
                         validator=validators.deep_iterable(
                             PropertySchemaModel.property_for_schema_validator,
                             validators.instance_of(list)),
                         default=list())
    # 可以指定统一要添加的属性
    unified_properties = attr.ib(type=List[PropertySchemaModel],
                                 converter=lambda x: list(set(x)),
                                 validator=validators.deep_iterable(
                                     PropertySchemaModel.property_for_schema_validator,
                                     validators.instance_of(list)),
                                 default=list())
    # 复合属性原生索引
    compound_property_indexes = attr.ib(type=List[List[PropertySchemaModel]],
                                        validator=validators.instance_of(list),
                                        default=list())
    comment = attr.ib(type=str, validator=validators.instance_of(str), default='')
    # 非负整数，默认为0，即永不过期
    ttl_duration = attr.ib(type=int, validator=(validators.ge(0), validators.instance_of(int)), default=0)
    ttl_col = attr.ib(type=str, validator=validators.instance_of((str, type(None))), default=None)
    index = attr.ib(type=bool, default=True)  # build index or not
    cn_name = attr.ib(type=str, validator=validators.instance_of(str), default='')

    # 实际设定index的名称会加上schema信息以及一些前缀用来唯一标识
    index_name_builder = attr.ib(type=(FunctionType, MethodType), default=build_index_name)

    _schema_type = attr.ib(init=False)
    _index_names = attr.ib(type=list, init=False)
    _index_name = attr.ib(type=str, init=False)
    _prop_index_names = attr.ib(type=list, init=False)
    _properties_map = attr.ib(type=dict, init=False)

    def __attrs_post_init__(self):
        # 默认添加额外的属性：用于形成一个单独的岛屿
        self.properties.extend(self.unified_properties)
        self._properties_map = {p.name: p for p in self.properties}
        for i, indexes in enumerate(self.compound_property_indexes):
            if not isinstance(indexes, list):
                raise TypeError('compound_indexes required list type, got {} instead'.format(type(indexes)))
            if len(indexes) < 2:
                raise ValueError('compound_indexes require length > 2, got {} instead'.format(len(indexes)))
            _props = list()
            for index in indexes:
                if index not in self.property_names():
                    raise ValueError('property: {} is not defined in {}'.format(index, self.name))
                _props.append(self._properties_map.get(index))
            self.compound_property_indexes[i] = _props
        self._index_names = []

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            if other.name == self.name:
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.name.__hash__()

    def __repr__(self):
        return 'Schema: {}'.format(self.name)

    def property_names(self):
        return [prop.name for prop in self.properties]

    def property_type(self, p_name):
        if p_name not in self._properties_map.keys():
            raise ValueError('property: {} is not defined in schema: {}'.format(p_name, self.name))
        return self._properties_map.get(p_name).type

    def property_display(self, p_name):
        if p_name not in self._properties_map.keys():
            raise ValueError('property: {} is not defined in schema: {}'.format(p_name, self.name))
        return self._properties_map.get(p_name).display

    def property_support_null(self, p_name):
        if p_name not in self._properties_map.keys():
            raise ValueError('property: {} is not defined in schema: {}'.format(p_name, self.name))
        return self._properties_map.get(p_name).support_null

    def index_names(self):
        return self._index_names

    def index_name(self):
        return self._index_name

    def prop_index_names(self):
        return self._prop_index_names

    def check_prop_instances(self, properties: dict):
        """检查属性是否满足预定义"""
        for p in self.properties:
            # 检查不支持None的属性是否都满足
            if not p.support_null and properties.get(p.name) is None:
                raise ValueError('{} of {} got None while defined as not support null'.format(p.name, self.name))
            try:
                NDataTypes.check_type(value=properties.get(p.name), type_=p.type, support_null=True)
            except TypeError as e:
                raise TypeError('{} of {}: {}'.format(p.name, self.name, e)) from e

    def build_id(self, _str_things: (List[str], str), builder: (FunctionType, MethodType)):
        return builder(schema_name=self.name, _str_things=_str_things) if self.index else None

    def build_property_index(self, property_: PropertySchemaModel):
        _index_name = self.index_name_builder(self.name, schema_type=self._schema_type, properties=[property_])
        self._index_names.append(_index_name)
        return _index_name

    def build_compound_property_index(self, properties: List[PropertySchemaModel]):
        _index_name = self.index_name_builder(self.name, schema_type=self._schema_type, properties=properties)
        self._index_names.append(_index_name)
        return _index_name

    def build_schema_index(self):
        _index_name = self.index_name_builder(self.name, schema_type=self._schema_type, properties=None)
        self._index_name = _index_name
        self._index_names.append(_index_name)
        return _index_name


@attr.s(repr=False, eq=False, hash=False)
class TagSchemaModel(SchemaModel):
    """定义节点类型"""
    _schema_type = Const.TAG

    def __repr__(self):
        return 'Tag-Schema: {} with properties: {}'.format(self.name, {p.name for p in self.properties})


@attr.s(repr=False, eq=False, hash=False)
class EdgeSchemaModel(SchemaModel):
    """定义边类型"""
    _schema_type = Const.EDGE
    # 是否为双向类型
    binary = attr.ib(type=bool, default=False)

    def __repr__(self):
        return 'Edge-Schema: {} with properties:{}'.format(self.name, {p.name for p in self.properties})


# @attr.s(hash=False)
# class RawVertexModel:
#     """
#     节点实例
#     https://docs.nebula-graph.com.cn/3.2.0/3.ngql-guide/12.vertex-statements/1.insert-vertex/
#     """
#     # 节点id，图空间内全局唯一，默认参数，最终 vid = tag名称+连接符+自定id
#     vid = attr.ib(type=(str, int), validator=validators.instance_of((str, int)))
#     # 节点所属schema，目前一个节点只能是一个TagSchema的实例 TODO Nebula支持同个节点是多个TagSchema的实例
#     schema = attr.ib(type=TagSchema, validator=validators.instance_of(TagSchema))
#     # 节点属性
#     properties = attr.ib(type=dict, default=dict())
#     # 是否自动编码图节点id
#     auto_encode_vid = attr.ib(type=bool, default=True)


@attr.s(eq=False, hash=False)
class VertexModel:
    """
    节点实例
    https://docs.nebula-graph.com.cn/3.2.0/3.ngql-guide/12.vertex-statements/1.insert-vertex/
    """
    # 节点id，图空间内全局唯一，默认参数，最终 vid = tag名称+连接符+自定id
    vid = attr.ib(type=(str, int), validator=validators.instance_of((str, int)))
    # 节点所属schema，目前一个节点只能是一个TagSchema的实例 TODO Nebula支持同个节点是多个TagSchema的实例
    schema = attr.ib(type=TagSchemaModel, validator=validators.instance_of(TagSchemaModel))
    # 节点属性
    properties = attr.ib(type=dict, default=dict())
    # # 是否自动编码图节点id
    # auto_encode_vid = attr.ib(type=bool, default=True)
    # 实际存入图数据库中的vid会加上schema名称作为前缀
    vid_builder = attr.ib(type=(FunctionType, MethodType), default=build_id)

    def __attrs_post_init__(self):
        # if self.auto_encode_vid:
        #     self.vid = self.schema.build_id(str(self.vid))
        self.vid = self.schema.build_id(str(self.vid), builder=self.vid_builder)
        try:
            self.schema.check_prop_instances(properties=self.properties)
        except Exception as e:
            raise e

    def __ne__(self, other):
        # vid 相同则相同
        return not self.__eq__(other)

    def __eq__(self, other):
        # vid 相同则相同
        if self.__class__ == other.__class__:
            if other.vid == self.vid:
                return True
        return False

    def __hash__(self):
        return self.vid.__hash__()

    def property_value(self, p_k):
        return self.properties.get(p_k, None)


@attr.s(eq=False, hash=False, repr=False)
class EdgeModel:
    """
    边实例
    https://docs.nebula-graph.com.cn/3.2.0/3.ngql-guide/13.edge-statements/1.insert-edge/
    """
    # 起始点vid
    src_vid = attr.ib(type=(str, int), validator=validators.instance_of((str, int)))
    # 终点vid
    dst_vid = attr.ib(type=(str, int), validator=validators.instance_of((str, int)))
    # 边所属schema
    schema = attr.ib(type=EdgeSchemaModel, validator=validators.instance_of(EdgeSchemaModel))
    # 边属性
    properties = attr.ib(type=dict, default=dict())
    rank = attr.ib(type=int, default=0, validator=validators.instance_of(int))

    def __ne__(self, other):
        # type、起点、终点、rank 都相同的边为相同边
        return not self.__eq__(other)

    def __eq__(self, other):
        # type、起点、终点、rank 都相同的边为相同边
        if self.__class__ == other.__class__:
            if other.src_vid == self.src_vid and \
                    other.dst_vid == self.dst_vid and \
                    other.schema == self.schema and \
                    other.rank == self.rank:
                return True
        return False

    def __hash__(self):
        return hash(''.join([str(self.src_vid),
                             str(self.dst_vid),
                             str(self.rank),
                             str(self.schema.name)
                             ]))

    def __repr__(self):
        return 'src_vid: {}, dst_vid: {}, schema: {}, ' \
               'rank: {}, properties: {}'.format(self.src_vid, self.dst_vid,
                                                 self.schema, self.rank,
                                                 self.properties)

    def property_value(self, p_k):
        return self.properties.get(p_k, None)


@attr.s
class SchemaInstancesModel:
    """某schema下实例集"""
    schema = attr.ib(type=(TagSchemaModel, EdgeSchemaModel), validator=validators.instance_of(SchemaModel))
    candidates = attr.ib(type=(List[VertexModel], List[EdgeModel]), init=False)
    schema_type = attr.ib(init=False)
    schema_type_class = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.candidates = []
        self.schema_type_class = VertexModel if self.schema_type == Const.TAG else EdgeModel

    def _check_member_schema(self, _member):
        """
        检查成员的schema类型和属性是否与预定义的一致
        """
        if not isinstance(_member, self.schema_type_class):
            raise TypeError('require {} got {} instead'.format(self.schema_type_class, type(_member)))

    def add(self, _member):
        self._check_member_schema(_member)
        self.candidates.append(_member)

    def union(self, instances):
        if instances.schema == self.schema and instances.schema_type == self.schema_type:
            self.candidates.extend(instances.candidates)


@attr.s
class VertexesModel(SchemaInstancesModel):
    """某Tag下节点实例集"""
    schema_type = Const.TAG


@attr.s
class EdgesModel(SchemaInstancesModel):
    """某EdgeType下边实例集"""
    schema_type = Const.EDGE
