import sqlite3
from typing import Any, Dict, List, Type

class Column:
    def __init__(self, column_type: Any, primary_key: bool = False, unique: bool = False, nullable: bool = True):
        self.type = column_type
        self.primary_key = primary_key
        self.unique = unique
        self.nullable = nullable

class Integer:
    pass

class String:
    pass

class Engine:
    def __init__(self, url: str):
        if url == 'sqlite:///:memory:':
            path = ':memory:'
        elif url.startswith('sqlite:///'):
            path = url.replace('sqlite:///', '', 1)
        else:
            path = url
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.data: Dict[str, List[Dict[str, Any]]] = {}

    def execute(self, *args, **kwargs):
        return self.conn.execute(*args, **kwargs)

class MetaData:
    def __init__(self):
        self.tables: List[str] = []

    def create_all(self, engine: Engine):
        for table in self.tables:
            engine.data.setdefault(table, [])

def create_engine(url: str, echo: bool = False, future: bool = True) -> Engine:
    return Engine(url)

def declarative_base():
    class Base:
        metadata = MetaData()

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls._columns = [name for name, val in cls.__dict__.items() if isinstance(val, Column)]
            if not hasattr(cls, '__tablename__'):
                cls.__tablename__ = cls.__name__.lower()
            Base.metadata.tables.append(cls.__tablename__)

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    return Base

class Session:
    def __init__(self, bind: Engine):
        self.bind = bind

    def add(self, obj: Any):
        table = obj.__class__.__tablename__
        cols = obj.__class__._columns
        row = {c: getattr(obj, c) for c in cols}
        # auto id
        pk = None
        for c in cols:
            col_desc = getattr(obj.__class__, c)
            if isinstance(col_desc, Column) and col_desc.primary_key:
                pk = c
                break
        if pk and getattr(obj, pk, None) is None:
            row[pk] = len(self.bind.data.setdefault(table, [])) + 1
            setattr(obj, pk, row[pk])
        self.bind.data.setdefault(table, []).append(row)

    def commit(self):
        pass

    def query(self, model: Type[Any]):
        return Query(self.bind.data.get(model.__tablename__, []), model)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

class Query:
    def __init__(self, data: List[Dict[str, Any]], model: Type[Any]):
        self.data = data
        self.model = model

    def filter_by(self, **kwargs: Any):
        filtered = []
        for row in self.data:
            ok = True
            for key, val in kwargs.items():
                if row.get(key) != val:
                    ok = False
                    break
            if ok:
                filtered.append(row)
        self.data = filtered
        return self

    def first(self):
        if not self.data:
            return None
        row = self.data[0]
        obj = self.model()
        for k, v in row.items():
            setattr(obj, k, v)
        return obj

    def count(self):
        return len(self.data)


def sessionmaker(bind: Engine):
    def maker():
        return Session(bind)
    return maker
