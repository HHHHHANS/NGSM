#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ngsm.base import NDataTypes
from ngsm.model import TagSchemaModel
from ngsm.model import EdgeSchemaModel
from ngsm.model import PropertySchemaModel

TagA = TagSchemaModel(
    name='A',
    properties={
        PropertySchemaModel(name='p1-tag-a', type=NDataTypes.STRING.value, support_null=False, index=True,
                            comment='string type\'s property of Tag A'),
        PropertySchemaModel(name='p2-tag-a', type=NDataTypes.BOOL.value, index=True, default=True,
                            comment='bool type\'s property of Tag A')
    },
    comment='Definition of Tag Schema A'
)

TagB = TagSchemaModel(
    name='B',
    properties={
        PropertySchemaModel(name='p1-tag-b', type=NDataTypes.INT.value,
                            comment='string type\'s property of Tag B')
    },
    comment='Definition of Tag Schema B'
)

EdgeTypeA = EdgeSchemaModel(
    name='A',
    properties={
        PropertySchemaModel(name='p1-edge-A', type=NDataTypes.FLOAT.value,
                            comment='float type\'s property of Edge A')
    }
)

print(TagA)
print(TagB)
print(EdgeTypeA)
print(TagA == TagB)
