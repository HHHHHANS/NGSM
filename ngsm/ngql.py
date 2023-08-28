#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List
from typing import Tuple

from ngsm.model import VertexModel
from ngsm.model import EdgeModel
from ngsm.model import PropertySchemaModel
from ngsm.model import SchemaModel
from ngsm.model import TagSchemaModel
from ngsm.model import EdgeSchemaModel
from ngsm.model import NDataTypes
from ngsm.convertor import StmtFormatter
from ngsm.convertor import ValueFormatter


class Insert:

    @classmethod
    def split_into_couple_stmts(cls, fix_part: str, multi_part: list, multi_part_splitter: str):
        parts_should_split = StmtFormatter.parts_should_split_of_stmt(fix_part, multi_part)

        if parts_should_split == 1:
            return ''.join([fix_part, multi_part_splitter.join(multi_part), ';'])
        else:
            parts = StmtFormatter.split_into_parts(multi_parts=multi_part, parts_num=parts_should_split)
            return [''.join([fix_part, multi_part_splitter.join(p), ';']) for p in parts]

    @classmethod
    def edge(cls, schema: SchemaModel, edges: List[EdgeModel], if_not_exists: bool):
        if not edges:
            return None
        fix_stmt = 'Insert Edge{0}{1}({2}) VALUES '.format(
            ' IF NOT EXISTS ' if if_not_exists else ' ',
            schema.name,
            ','.join(schema.property_names()),
        )
        multi_parts = [Insert._edge(schema=schema, edge=edge) for edge in edges]
        return cls.split_into_couple_stmts(fix_part=fix_stmt, multi_part=multi_parts, multi_part_splitter=', ')

    @classmethod
    def _edge(cls, schema: SchemaModel, edge: EdgeModel):
        return '\"{0}\"->\"{1}\"{2}:({3})'.format(
            edge.src_vid,
            edge.dst_vid,
            '' if not edge.rank else '@{}'.format(edge.rank),
            Insert.properties(schema.properties, edge)
        )

    @classmethod
    def vertex(cls, schema: SchemaModel, vertexes: List[VertexModel], if_not_exists: bool):
        if not vertexes:
            return None
        fix_stmt = 'Insert VERTEX{0}{1}({2}) VALUES '.format(
            ' IF NOT EXISTS ' if if_not_exists else ' ',
            schema.name,
            ', '.join(schema.property_names()),
        )
        multi_parts = [Insert._vertex(schema=schema, vertex=vertex) for vertex in vertexes]
        return cls.split_into_couple_stmts(fix_part=fix_stmt, multi_part=multi_parts, multi_part_splitter=', ')

    @classmethod
    def _vertex(cls, schema: SchemaModel, vertex: VertexModel):
        return '\"{}\":({})'.format(vertex.vid, Insert.properties(schema.properties, vertex))

    @classmethod
    def properties(cls, properties: List[PropertySchemaModel], instance: (VertexModel, EdgeModel)):
        return ', '.join([cls._property_(property_.type,
                                         instance.property_value(property_.name))
                          for property_ in properties])

    @classmethod
    def _property_(cls, property_type, value):
        if value is None:
            return 'NULL'
        return ValueFormatter.encode(property_type, value)


class Create:

    @classmethod
    def space(cls):
        pass

    @classmethod
    def _schema(cls, schema_type, schema: SchemaModel, if_not_exists: bool):
        return 'CREATE {0} {1}{2}({3}){4};'.format(
            schema_type,
            'IF NOT EXISTS ' if if_not_exists else '',
            schema.name,
            Create.properties(schema.properties),
            ' COMMENT=\"{}\"'.format(schema.comment) if schema.comment else ''
        )

    @classmethod
    def tag(cls, schema: SchemaModel, if_not_exists: bool):
        return cls._schema(schema_type='TAG', schema=schema, if_not_exists=if_not_exists)

    @classmethod
    def edge_type(cls, schema: SchemaModel, if_not_exists: bool):
        return cls._schema(schema_type='EDGE', schema=schema, if_not_exists=if_not_exists)

    @classmethod
    def properties(cls, properties: List[PropertySchemaModel]):
        return ', '.join([Create._property_(property_) for property_ in properties])

    @classmethod
    def _property_(cls, property_: PropertySchemaModel):
        return '{0} {1}{2}{3}{4}'.format(
            property_.name,
            property_.type,
            ' NOT NULL' if not property_.support_null else '',
            ' DEFAULT {}'.format(property_.default) if property_.default else '',
            ' COMMENT \"{}\"'.format(property_.comment) if property_.comment else ''
        )

    @classmethod
    def _schema_index(cls, schema_type, schema: SchemaModel, if_not_exists: bool):
        return 'CREATE {0} {1}INDEX {2} on {3}();'.format(
            schema_type,
            'IF NOT EXISTS ' if if_not_exists else '',
            schema.build_schema_index(),
            schema.name
        ) if schema.index else None

    @classmethod
    def _property_index(cls, schema_type, schema: SchemaModel,
                        property_: (List[PropertySchemaModel], PropertySchemaModel),
                        string_length: int, if_not_exists: bool):
        if not property_:
            return None

        if isinstance(property_, PropertySchemaModel):
            build_index_func = schema.build_property_index
            build_index_type_func = cls._property_index_type
        else:
            build_index_func = schema.build_compound_property_index
            build_index_type_func = cls._compound_property_index_type

        return 'CREATE {0} {1}INDEX {2} on {3}({4});'.format(
            schema_type,
            'IF NOT EXISTS ' if if_not_exists else '',
            build_index_func(property_),
            schema.name,
            build_index_type_func(property_, string_length=string_length)
        )

    @classmethod
    def _property_index_type(cls, property_: PropertySchemaModel, string_length: int):
        return property_.name if property_.type != NDataTypes.STRING.value \
            else '{}({})'.format(property_.name, string_length)

    @classmethod
    def _compound_property_index_type(cls, properties: List[PropertySchemaModel], string_length: int):
        return ', '.join([cls._property_index_type(property_=p, string_length=string_length) for p in properties])

    @classmethod
    def tag_index(cls, schema: TagSchemaModel, if_not_exists: bool):
        return cls._schema_index(schema_type='TAG', schema=schema, if_not_exists=if_not_exists)

    @classmethod
    def edge_type_index(cls, schema: EdgeSchemaModel, if_not_exists: bool):
        return cls._schema_index(schema_type='EDGE', schema=schema, if_not_exists=if_not_exists)

    @classmethod
    def property_index(cls, schema: [TagSchemaModel, EdgeSchemaModel],
                       property_: PropertySchemaModel, string_length: int, if_not_exists: bool):
        # 单属性索引
        if not property_.index:
            return None
        schema_type = 'TAG' if isinstance(schema, TagSchemaModel) else 'EDGE'
        return cls._property_index(schema_type=schema_type, schema=schema,
                                   property_=property_,
                                   if_not_exists=if_not_exists, string_length=string_length)

    @classmethod
    def compound_property_index(cls, schema: [TagSchemaModel, EdgeSchemaModel],
                                compound_properties: List[PropertySchemaModel], string_length: int,
                                if_not_exists: bool):
        # 复合属性索引
        schema_type = 'TAG' if isinstance(schema, TagSchemaModel) else 'EDGE'
        return cls._property_index(schema_type=schema_type, schema=schema,
                                   property_=compound_properties,
                                   if_not_exists=if_not_exists, string_length=string_length)


class Delete:

    @classmethod
    def vertex(cls, schema: SchemaModel):
        pass

    @classmethod
    def edge(cls, schema: SchemaModel, edge_pairs: (List[tuple], Tuple[tuple])):
        if not isinstance(edge_pairs, (list, tuple)):
            raise TypeError('required list or tuple type, got {}'.format(type(edge_pairs)))
        if not edge_pairs:
            return None
        fix_stmt = 'DELETE EDGE {} '.format(schema.name)
        multi_parts = [cls._edge(edge_pair) for edge_pair in edge_pairs]
        return Insert.split_into_couple_stmts(fix_part=fix_stmt, multi_part=multi_parts, multi_part_splitter=', ')

    @classmethod
    def _edge(cls, edge_info: tuple):
        return ValueFormatter.edge(edge_info=edge_info)


class Update:

    @classmethod
    def edge(cls, schema: SchemaModel, edge_pair: Tuple, new_properties: dict):
        # 目前仅支持单次更新一条边的属性
        return 'UPDATE EDGE ON {} {} SET {}' \
               ';'.format(schema.name,
                          ValueFormatter.edge(edge_info=edge_pair),
                          ', '.join(['{} = {}'.format(k, ValueFormatter.encode(schema.property_type(k), v))
                                     for k, v in new_properties.items()])
                          )


class RebuildIndex:

    @classmethod
    def _(cls, schema_type: str, index_names: (List[str], str) = None):
        if not index_names:
            index_names_str = ' '
        else:
            index_names_str = ' {0}'.format(','.join(index_names if isinstance(index_names, list) else [index_names]))
        return 'REBUILD {0} INDEX{1};'.format(schema_type, index_names_str)

    @classmethod
    def tag(cls, schema: SchemaModel, include_properties: bool):
        return cls._(schema_type='TAG',
                     index_names=schema.index_names() if include_properties else schema.index_name())

    @classmethod
    def edge_type(cls, schema: EdgeSchemaModel, include_properties: bool):
        return cls._(schema_type='EDGE',
                     index_names=schema.index_names() if include_properties else schema.index_name())

    @classmethod
    def properties(cls, schema: (TagSchemaModel, EdgeSchemaModel), index_names: (List[str], str) = None):
        schema_type = 'TAG' if isinstance(schema, TagSchemaModel) else 'EDGE'
        return cls._(schema_type=schema_type, index_names=index_names)


class Space:

    @classmethod
    def create(cls, space_name: str, partition_num: int, replica_factor: int,
               vid_type: str, if_not_exists: bool, comment: str = ''):
        """创建图空间"""
        return 'CREATE SPACE {}{}(partition_num={}, replica_factor={}, vid_type={}){};'.format(
            'IF NOT EXISTS ' if if_not_exists else '',
            space_name, partition_num, replica_factor, vid_type,
            ' COMMENT=\"{}\"'.format(comment) if comment else ''
        )

    @classmethod
    def show(cls):
        return 'SHOW SPACES;'

    @classmethod
    def clone(cls, new_space: str, old_space: str, if_not_exists: bool):
        return 'CREATE SPACE {0}{1} AS {2};'.format(
            'IF NOT EXISTS ' if if_not_exists else '',
            new_space, old_space
        )

    @classmethod
    def _drop(cls, space_name: str):
        """
        https://docs.nebula-graph.com.cn/3.2.0/3.ngql-guide/9.space-statements/5.drop-space/
        """
        return 'DROP SPACE IF EXISTS {}'.format(space_name)

    @classmethod
    def _clear(cls, space_name: str):
        """
        https://docs.nebula-graph.com.cn/3.2.0/3.ngql-guide/9.space-statements/6.clear-space/
        + 用于清空图空间中的点和边，但不会删除图空间本身、其中的Schema信息以及索引等元数据
        + 不是原子性操作。如果执行出错，请重新执行，避免残留数据
        """
        return 'CLEAR SPACE IF EXISTS {};'.format(space_name)

    @classmethod
    def use(cls, space_name: str):
        return 'USE {};'.format(space_name)

    @classmethod
    def describe(cls, space_name: str):
        return 'DESCRIBE SPACE {};'.format(space_name)


class Tag:

    @classmethod
    def create(cls, schema: SchemaModel, if_not_exists: bool):
        return Create.tag(schema=schema, if_not_exists=if_not_exists)


class EdgeType:
    @classmethod
    def create(cls, schema: SchemaModel, if_not_exists: bool):
        return Create.edge_type(schema=schema, if_not_exists=if_not_exists)


class Vertex:

    @classmethod
    def insert(cls, schema: SchemaModel, vertexes: List[VertexModel], if_not_exists: bool):
        return Insert.vertex(schema=schema, vertexes=vertexes, if_not_exists=if_not_exists)


class Edge:

    @classmethod
    def insert(cls, schema: SchemaModel, edges: List[EdgeModel], if_not_exists: bool):
        return Insert.edge(schema=schema, edges=edges, if_not_exists=if_not_exists)

    @classmethod
    def delete(cls, schema: SchemaModel, edge_pairs: (List[tuple], Tuple[tuple])):
        return Delete.edge(schema=schema, edge_pairs=edge_pairs)

    @classmethod
    def update(cls, schema: EdgeSchemaModel, edge_pair: tuple, new_properties: dict):
        # 目前仅支持单条更新
        return Update.edge(schema=schema, edge_pair=edge_pair, new_properties=new_properties)
