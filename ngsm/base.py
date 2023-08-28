#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from attr import validators

from ngsm.tool import EnumBase


class Setting:
    __NebulaVersion__ = '3.2.0'

    # 保留关键字
    RETAIN_KEYWORD = """\
    ACROSS
    ADD
    ALTER
    AND
    AS
    ASC
    ASCENDING
    BALANCE
    BOOL
    BY
    CASE
    CHANGE
    COMPACT
    CREATE
    DATE
    DATETIME
    DELETE
    DESC
    DESCENDING
    DESCRIBE
    DISTINCT
    DOUBLE
    DOWNLOAD
    DROP
    EDGE
    EDGES
    EXISTS
    EXPLAIN
    FETCH
    FIND
    FIXED_STRING
    FLOAT
    FLUSH
    FORMAT
    FROM
    GET
    GO
    GRANT
    IF
    IGNORE_EXISTED_INDEX
    IN
    INDEX
    INDEXES
    INGEST
    INSERT
    INT
    INT16
    INT32
    INT64
    INT8
    INTERSECT
    IS
    LIMIT
    LIST
    LOOKUP
    MAP
    MATCH
    MINUS
    NO
    NOT
    NOT_IN
    NULL
    OF
    OFFSET
    ON
    OR
    ORDER
    OVER
    OVERWRITE
    PROFILE
    PROP
    REBUILD
    RECOVER
    REMOVE
    RESTART
    RETURN
    REVERSELY
    REVOKE
    SET
    SHOW
    STEP
    STEPS
    STOP
    STRING
    SUBMIT
    TAG
    TAGS
    TIME
    TIMESTAMP
    TO
    UNION
    UPDATE
    UPSERT
    UPTO
    USE
    VERTEX
    VERTICES
    WHEN
    WHERE
    WITH
    XOR
    YIELD
    """
    RETAIN_KEYWORD = RETAIN_KEYWORD.splitlines()

    @classmethod
    def is_retain_keyword(cls, str_obj: str):
        if str_obj.upper() in cls.RETAIN_KEYWORD:
            raise ValueError('{} is a retain word or nebula'.format(str_obj))
        return str_obj

    # 非保留关键字
    NONE_RETAIN_KEYWORD = """\
    ACCOUNT
    ADMIN
    ALL
    ANY
    ATOMIC_EDGE
    AUTO
    BIDIRECT
    BOTH
    CHARSET
    CLIENTS
    COLLATE
    COLLATION
    COMMENT
    CONFIGS
    CONTAINS
    DATA
    DBA
    DEFAULT
    ELASTICSEARCH
    ELSE
    END
    ENDS
    ENDS_WITH
    FORCE
    FULLTEXT
    FUZZY
    GOD
    GRAPH
    GROUP
    GROUPS
    GUEST
    HDFS
    HOST
    HOSTS
    INTO
    IS_EMPTY
    IS_NOT_EMPTY
    IS_NOT_NULL
    IS_NULL
    JOB
    JOBS
    KILL
    LEADER
    LISTENER
    META
    NOLOOP
    NONE
    NOT_CONTAINS
    NOT_ENDS_WITH
    NOT_STARTS_WITH
    OPTIONAL
    OUT
    PART
    PARTITION_NUM
    PARTS
    PASSWORD
    PATH
    PLAN
    PREFIX
    QUERIES
    QUERY
    REDUCE
    REGEXP
    REPLICA_FACTOR
    RESET
    ROLE
    ROLES
    SAMPLE
    SEARCH
    SERVICE
    SESSION
    SESSIONS
    SHORTEST
    SIGN
    SINGLE
    SKIP
    SNAPSHOT
    SNAPSHOTS
    SPACE
    SPACES
    STARTS
    STARTS_WITH
    STATS
    STATUS
    STORAGE
    SUBGRAPH
    TEXT
    TEXT_SEARCH
    THEN
    TOP
    TTL_COL
    TTL_DURATION
    UNWIND
    USER
    USERS
    UUID
    VALUE
    VALUES
    VID_TYPE
    WILDCARD
    ZONE
    ZONES
    FALSE
    TRUE
    """

    # 单条语句最大长度
    max_stmt_length = 4194304 / 2


class NDataTypes(EnumBase):
    # 字符串
    STRING = 'STRING'

    # 布尔
    BOOL = 'BOOL'

    # 整型数值
    INT = 'INT'
    INT64 = 'INT64'
    INT8 = 'INT8'
    INT16 = 'INT16'
    INT32 = 'INT32'

    # 浮点数值
    FLOAT = 'FLOAT'
    DOUBLE = 'DOUBLE'

    # 时间日期
    DATE = 'DATE'
    TIME = 'TIME'
    DATETIME = 'DATETIME'
    TIMESTAMP = 'TIMESTAMP'
    DURATION = 'DURATION'

    @classmethod
    def integers(cls):
        return cls.INT.value, cls.INT8.value, cls.INT16.value, cls.INT32.value, cls.INT64.value

    @classmethod
    def check_type(cls, value, type_, support_null):
        if support_null:
            if type_ in NDataTypes.integers() and not isinstance(value, (int, type(None))):
                raise TypeError('required int but got {} instead'.format(type(value)))
        else:
            if type_ in NDataTypes.integers() and not isinstance(value, int):
                raise TypeError('required int but got {} instead'.format(type(value)))


# Define the validator when pre-defined Nebula-type meet py-type
NType2Validator = {
    NDataTypes.INT.value: validators.instance_of(int),
    NDataTypes.INT8.value: validators.instance_of(int),
    NDataTypes.INT16.value: validators.instance_of(int),
    NDataTypes.INT32.value: validators.instance_of(int),
    NDataTypes.INT64.value: validators.instance_of(int),
    NDataTypes.STRING.value: validators.instance_of(str),
    NDataTypes.BOOL.value: validators.instance_of(bool),
    NDataTypes.FLOAT.value: validators.instance_of(float),
    NDataTypes.DOUBLE.value: validators.instance_of(float),
    NDataTypes.TIMESTAMP.value: validators.instance_of(int)
}


class Const:
    TAG = 'TAG'
    EDGE = 'EDGE'
    PROPERTY = 'PROPERTY'

    TypeOfNone = type(None)

    vid_joiner = '__'
