---
date: '2025-09-17T08:20:01+08:00'
draft: true
title: '后端踩坑 - 怎样正确管理 SQLAlchemy Session'
comments: true
tags: ['后端', '后端踩坑', '数据库', 'Python', 'SQLAlchemy', 'FastAPI']
categories: 后端踩坑
links:
    - title: SQLAlchemy 2.0 Documentation
      description: Session Basics
      website: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
      image: https://www.sqlalchemy.org/favicon.ico
    - title: PostgreSQL Wiki
      description: Number of Database Connections
      website: https://wiki.postgresql.org/wiki/Number_Of_Database_Connections
      image: https://wiki.postgresql.org/favicon.ico
---

## 错误示例

在写一个 FastAPI + SQLAlchemy 的项目, 最开始不熟悉时写了一堆坏代码。现在总结一下。

为了管理数据库的 Session, 我封装了一个 DatabaseSessionManager 类. 下面给出一个概括版的实现示例.

```python
# session.py
import contextlib
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def close(self):
        # Existing codes


# repo.py
class UserRepository:
    def __init__(self, session_manager: DatabaseSessionManager):
        self.session_manager = session_manager

    async def create(self, user_in: UserCreate) -> User:
        """创建新用户"""
        async with self.session_manager.session() as session:
            # ... 创建逻辑 ...
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj


#deps.py

def get_user_repo() -> UserRepository:
    session_manager = DatabaseSessionManager(settings.database_url)
    return UserRepository(session_manager)

async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserManager:
    return UserService(repository)
```

---

## 问题产生

先讲讲这个代码会直接跑崩的原因。

看起来在每一次数据库操作中, session 都会通过 `async with` 正确地被管理, 无论怎样都会被关闭。

之前的并发需求并不高, 一直没有显露问题。然而做了几百组的并发测试, 却发现疯狂报 `TooManyConnectionsError`。

回头看一眼代码，其实很快能发现问题。

---

## 原因

我在依赖注入中重复创建了 `DatabaseSessionManager` 的实例.

SQLAlchemy 推荐的实践是, 整个进程公用一个 engine, 尽可能短暂的使用每一个 session, session 用完即弃.

因此, 内部管理了数据库引擎和连接池的 `DatabaseSessionManager` 必须是全局唯一的单例. 上面的错误代码实际上是乱用依赖注入, 破坏了这一单例模式.

在基本没有并发需求的时候, 请求密度很低, 问题没有显现的原因是 Python 的垃圾回收机制定时回收了不再使用的 engine, 同时 PostgreSQL 服务器的空闲连接超时也会断开连接. 但并发量大起来之后, 这两个机制就不可能跟的上连接创建的速度了。

---

## 正确实践

上面的错误代码基本完全背离最佳实践。最大的问题是两个:

1. session 的生命周期不应该在 repository 管理。
2. DatabaseSessionManager 在这种场景下应当是单例。

正确的实践是什么？以下是我个人认为比较好的做法。

### 全局单例

首先我们需要保证 DatabaseSessionManager 的全局单例，避免重复创建 Engine。参见[SQLAlchemy 2.0 Documentation - Session Basics - Using a sessionmaker](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker)

> When you write your application, the sessionmaker factory should be scoped the same as the Engine object created by `create_engine()`, which is typically at module-level or global scope. As these objects are both factories, they can be used by any number of functions and threads simultaneously.

有一个比较常见的实现方法是用 `@lru_cache(max_size=1)`。

用 `@lru_cache(maxsize=1)` 装饰一个不带参数的函数时，这个函数第一次运行后，返回的对象就被存在缓存里，后面无论再调用多少次，都会直接返回同一个实例，不会再次创建。

需要注意的是这种做法一般只在单进程的情况下使用，使用多 worker 之类的多进程情况需要注意，因为本质上并没有复用连接。`pool_size * worker_count < max_connections`。如果是高并发大集群，需要用 pgbouncer 或者 pgpool II 之类的做连接复用

如何计算连接池应当是多大？又挖了一个坑。参见 [PostgreSQL Wiki - Number Of Database Connections](https://wiki.postgresql.org/wiki/Number_Of_Database_Connections)

> For optimal throughput the number of active connections should be somewhere near ((core_count * 2) + effective_spindle_count).

```python
@lru_cache(maxsize=1)
def get_sessionmanager() -> DatabaseSessionManager:
    settings = get_settings()
    return DatabaseSessionManager(settings.database.url)
```

### Session 生命周期

session 的生命周期应当由业务逻辑来决定。我们应当在 API 路由依赖注入获得 session, 在服务层进行 `session.commit()` 等操作。

[SQLAlchemy 2.0 Documentation - Session Basics - When do I construct a Session, when do I commit it, and when do I close it?](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it)
> Make sure you have a clear notion of where transactions begin and end, and keep transactions short, meaning, they end at the series of a sequence of operations, instead of being held open indefinitely.
>
> As a general rule, the application should manage the lifecycle of the session externally to functions that deal with specific data. This is a fundamental separation of concerns which keeps data-specific operations agnostic of the context in which they access and manipulate that data.

数据库操作的原子性不是说把每一个数据库操作单独放一个 session, 是保证每一系列相关的数据库操作整体，是原子性的。文档说要让事务简短，不是说在每一个 repo 方法都分一个 session。

**永远不要在 repository 中进行 `session.commit()`!**

正确的做法是在路由函数开始时，依赖注入一个 Session, 而不可能是注入一个 DatabaseSessionManager。

```python
@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    repository: UserRepository = Depends(get_user_repository),
) -> User:
```

## 完整代码 Demo

以下是可供直接运行的完整代码示例:

```python
# model.py
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
```

```python
# repository.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User


class UserRepository:
    async def create(self, session: AsyncSession, name: str, email: str, age: Optional[int] = None) -> User:
        user = User(name=name, email=email, age=age)
        session.add(user)
        await session.flush()  # 获取自动生成的 ID，但不提交事务
        return user
```

```python
# config.py

from typing import Any
from functools import lru_cache
from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    db_path: str = "./playground.db"
    
    @computed_field(repr=False)
    @property
    def url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"

    @computed_field
    @property
    def engine_kwargs(self) -> dict[str, Any]:
        return {
            "echo": False,  # 设置为 True 可以看到 SQL 语句
        }

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PLAYGROUND_",
        env_nested_delimiter="__",
    )

    debug: bool = False
    database: DatabaseConfig = DatabaseConfig()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

```python
# session.py
import contextlib
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncConnection,
)

from .config import get_settings, DatabaseConfig

from loguru import logger


class DatabaseSessionManager:
    def __init__(self, config: DatabaseConfig, debug: bool = False):

        self._engine = create_async_engine(config.url, **config.engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            self._engine,
            expire_on_commit=False,  # 关闭自动提交
            class_=AsyncSession,
        )

    async def close(self):
        if self._engine is None:
            logger.debug("DatabaseSessionManager already closed or not initialized")
            return

        try:
            await self._engine.dispose()
            logger.debug("Database engine closed")
        except Exception as e:
            logger.error(f"Error occurred while closing the database engine: {e}")
        finally:
            self._engine = None
            self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncGenerator[AsyncConnection, None]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception as e:
                await connection.rollback()
                logger.error(f"Error during connection context, rolling back: {e}")
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            try:
                await session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")


@lru_cache(maxsize=1)
def get_sessionmanager() -> DatabaseSessionManager:
    settings = get_settings()
    return DatabaseSessionManager(settings.database, debug=settings.debug)
```

```python
# deps.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from .session import get_sessionmanager
from .repository import UserRepository


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    sessionmanager = get_sessionmanager()
    async with sessionmanager.session() as session:
        yield session


def get_user_repository() -> UserRepository:
    return UserRepository()
```

```python
# api.py
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from .deps import get_db_session, get_user_repository
from .repository import UserRepository
from .models import User


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None
    
    class Config:
        from_attributes = True  # 允许从 ORM 模型创建


# 路由定义
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    repository: UserRepository = Depends(get_user_repository),
) -> User:

    user = await repository.create(
        session=session,
        name=user_data.name,
        email=user_data.email,
        age=user_data.age,
    )
    
    # 提交事务
    await session.commit()
    
    # 刷新对象以获取数据库生成的字段
    await session.refresh(user)
    
    return user
```

```python
# main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from .session import get_sessionmanager
from .models import Base
from .api import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    sessionmanager = get_sessionmanager()
    async with sessionmanager.connect() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield
    
    await sessionmanager.close()


app = FastAPI(
    lifespan=lifespan,
)

app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World!"}
```
