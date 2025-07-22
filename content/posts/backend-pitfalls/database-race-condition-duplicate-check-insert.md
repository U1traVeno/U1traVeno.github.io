---
date: '2025-07-22T11:07:23+08:00'
draft: true
title: '后端踩坑 - 竞态条件导致的重复插入, 数据库操作原子化'
tags: ['后端', '后端踩坑', '数据库', 'Python', 'SQLAlchemy']
comments: true
---

有时需要避免让某一个Column出现重复的条目. 首先我们定义相关的模型:

```python
# models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MyModel(Base):
    __tablename__ = 'my_table'
    
    id = Column(Integer, primary_key=True)
    hash = Column(String(64), unique=True, nullable=False)
    foo = Column(String(100), nullable=False)
    bar = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# schemas.py
from pydantic import BaseModel
from datetime import datetime

class MyModelCreate(BaseModel):
    hash: str
    foo: str
    bar: str

class MyModelResponse(BaseModel):
    id: int
    hash: str
    foo: str
    bar: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# repository.py
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

class MyRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_record(self, model_data: MyModelCreate) -> Optional[MyModel]:
        try:
            new_record = MyModel(
                hash=model_data.hash,
                foo=model_data.foo,
                bar=model_data.bar
            )
            self.db.add(new_record)
            self.db.commit()
            return new_record
        except Exception:
            self.db.rollback()
            return None
    
    def get_by_hash(self, hash_value: str) -> Optional[MyModel]:
        return self.db.query(MyModel).filter(MyModel.hash == hash_value).first()


# services.py
import hashlib
from typing import Optional

class MyService:
    def __init__(self, repository: MyRepository):
        self.repository = repository
    
    @staticmethod
    def calculate_hash(foo: str, bar: str) -> str:
        content = f"{foo}:{bar}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def create_record(self, foo: str, bar: str) -> Optional[MyModelResponse]:
        hash_value = self.calculate_hash(foo, bar)
        model_data = MyModelCreate(hash=hash_value, foo=foo, bar=bar)
        
        result = self.repository.create_record(model_data)
        if not result:
            return None
        return MyModelResponse.from_orm(result)
```

在串行状态时, 这样是没有什么问题的. 但很多时候我们是并行异步处理. 这时就产生了竞态条件. 

假设我们有一个API-A和API-B同时接受到了两个一样的请求, 使用了这个方法: 

A 和 B 计算出hash, 查询发现数据库并没有这个hash, 于是都准备进行插入. 

## 竞态条件时间线分析

| 时间点 | 进程A | 进程B | 数据库状态 | 说明 |
|--------|-------|-------|------------|------|
| T1 | 执行 `db.commit()` | 准备执行 `db.commit()` | 等待处理A的请求 | A先发起提交请求 |
| T2 | 等待数据库响应 | 执行 `db.commit()` | 同时收到两个INSERT请求 | B几乎同时发起提交 |
| T3 | INSERT 成功，事务提交 | 等待数据库响应 | 处理A的请求，加锁后释放 | A的数据成功写入 |
| T4 | 返回成功结果 | 收到 `IntegrityError` 异常 | 处理B的请求，发现唯一键冲突 | B的INSERT失败 |
| T5 | 完成 | 执行 `db.rollback()`，返回 None | 回滚B的事务 | B处理失败，返回空值 |

实际上这里的代码是破坏了数据库操作原子化的原则. 有几种修改方案:

## 1. **捕获异常, 处理重复创建请求**

这个方案确实要好一点, 因为至少它拿到了记录. 

```python
# repository.py
from sqlalchemy.exc import IntegrityError
def create_record(self, model_data: MyModelCreate) -> Optional[MyModel]:
    """
    创建记录，返回(记录, 是否新创建)
    """
    try:
        new_record = MyModel(
            hash=model_data.hash,
            foo=model_data.foo,
            bar=model_data.bar
        )
        self.db.add(new_record)
        self.db.commit()
        return new_record
    except IntegrityError as e:
        self.db.rollback()
        raise e
    except Exception:
        return None

# services.py
def create_record(self, foo: str, bar: str) -> Tuple[MyModelResponse, bool]:
    """
    创建或获取记录，返回(记录, 是否新创建)
    """
    hash_value = self.calculate_hash(foo, bar)
    model_data = MyModelCreate(hash=hash_value, foo=foo, bar=bar)
    
    try:
        result = self.repository.create_record(model_data)
        is_new = True
    except IntegrityError:
        result = self.repository.get_by_hash(hash_value)
        is_new = False
    if not result:
        raise HTTPExceptions(status_code=500)

    return MyModelResponse.from_orm(result), is_new
```
这种应用层逻辑是一种比较初级的解决方案, 很直观, 符合人的线性思维, 但没有充分利用数据库的能力, 也未能处理并发环境下的复杂性. 

它仍然不是原子的. 数据库操作需要讨论的"原子性", 是指"**检查是否存在, 如果不存在则创建**"的整个流程必须是原子的. 因此, 这种解决方案存在一个更微妙的风险: 

| 时间点 | 进程A | 进程B | 进程C | 风险点 |
|--------|-------|-------|-------|--------|
| T1 | 调用 `create_record()` 成功提交 | 准备调用 `create_record()` | 不存在 | A成功创建记录 |
| T2 | 完成操作 | 调用 `create_record()`，抛出 `IntegrityError` | 不存在 | B遇到重复键冲突 |
| T3 | 完成操作 | 捕获异常，进入 except 块 | 不存在 | B准备查询已存在记录 |
| T4 | 完成操作 | 准备调用 `get_by_hash()` | **删除A创建的记录** | ⚠️ 关键风险窗口 |
| T5 | 完成操作 | 调用 `get_by_hash()`，返回 None | 完成删除操作 | B查询不到任何记录 |
| T6 | 完成操作 | 抛出 `HTTPException(500)` | 完成操作 | 用户收到意外的服务器错误 |



## 2. **在数据库层面处理(UPSERT)** 

UPSERT 是 UPDATE 和 SELECT 的组合词. 

如 PostgreSQL 和 sqlite 的 ON CONFLICT, MySQL的 ON DUPLICATE KEY UPDATE

这种方法将竞态条件的处理交给数据库层面，是在不引入redis等重量级部件的情况下可靠的解决方案. 应用层代码可以由此变为声明式的业务逻辑.

### 原生SQL实现

**PostgreSQL:**
```sql
INSERT INTO my_table (hash, foo, bar, created_at) 
VALUES ('hash_value', 'foo_value', 'bar_value', NOW())
ON CONFLICT (hash) 
DO UPDATE SET 
    foo = EXCLUDED.foo,
    bar = EXCLUDED.bar,
    created_at = NOW()
RETURNING *;
```

**SQLite:**
```sql
INSERT INTO my_table (hash, foo, bar, created_at) 
VALUES ('hash_value', 'foo_value', 'bar_value', datetime('now'))
ON CONFLICT (hash) 
DO UPDATE SET 
    foo = excluded.foo,
    bar = excluded.bar,
    created_at = datetime('now')
RETURNING *;
```

**MySQL:**
```sql
INSERT INTO my_table (hash, foo, bar, created_at)
VALUES ('hash_value', 'foo_value', 'bar_value', NOW())
ON DUPLICATE KEY UPDATE
  foo = VALUES(foo),
  bar = VALUES(bar),
  created_at = NOW();
```



### SQLAlchemy方言实现(PostgreSQL为例)

```python
# repository.py
from sqlalchemy.dialects.postgresql import insert
from typing import Tuple
from sqlalchemy.orm import Session

class MyRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_record(self, model_data: MyModelCreate) -> Tuple[MyModel, bool]:
        """
        原子化地获取或创建记录。
        返回 (记录实例, 是否是新创建的布尔值)。
        """
        # 1. 构建 INSERT 语句
        stmt = insert(MyModel).values(
            hash=model_data.hash,
            foo=model_data.foo,
            bar=model_data.bar
        )

        # 2. 定义冲突时的行为 (ON CONFLICT)
        # 我们利用 DO UPDATE 来确保总能返回记录。
        # set_={} 表示如果冲突了，什么字段都不实际更新，但这个子句是使用 RETURNING 的前提。
        # 我们可以通过比较 xmax 系统字段来判断是 INSERT 还是 UPDATE 发生的。
        # 在 PostgreSQL 中，新插入的行 xmax 值为 0。
        update_stmt = stmt.on_conflict_do_update(
            index_elements=['hash'],  # 指定唯一的索引列
            set_={'foo': stmt.excluded.foo}, # 即使值不变也要指定一个，以便触发update路径
            # where_=(MyModel.foo != stmt.excluded.foo) # 可以加一个判断条件，仅当内容变化时才更新
        ).returning(MyModel, MyModel.xmax) # RETURNING 子句返回完整的模型和xmax字段

        # 3. 执行并获取结果
        result_row = self.db.execute(update_stmt).first()
        self.db.commit()

        record = result_row[0]
        xmax_val = result_row[1]
        
        # 4. 判断记录是否为新创建
        # 如果 xmax 为 0，说明执行的是 INSERT
        is_created = (xmax_val == 0)

        return record, is_created


# services.py
import hashlib
from typing import Tuple
from fastapi import HTTPException

class MyService:
    def __init__(self, repository: MyRepository):
        self.repository = repository
    
    @staticmethod
    def calculate_hash(foo: str, bar: str) -> str:
        content = f"{foo}:{bar}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def create_or_get_record(self, foo: str, bar: str) -> Tuple[MyModelResponse, bool]:
        """
        创建或获取记录，使用UPSERT操作确保原子性
        返回: (记录对象, 是否为新创建)
        """
        try:
            hash_value = self.calculate_hash(foo, bar)
            model_data = MyModelCreate(hash=hash_value, foo=foo, bar=bar)
            
            record, is_new = self.repository.get_or_create_record(model_data)
            
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create or retrieve record")
            
            return MyModelResponse.from_orm(record), is_new
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")

```

