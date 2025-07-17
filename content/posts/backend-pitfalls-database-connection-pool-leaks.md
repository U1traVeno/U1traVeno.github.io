---
date: '2025-07-17T19:20:01+08:00'
draft: false
title: '后端踩坑-数据库连接池泄漏, 单例模式和依赖注入'
comments: true
tags: ['后端', '数据库', 'Python', '设计模式']
---

在写一个 FastAPI + SQLAlchemy 的项目, 写出来个有点蠢的bug, 记一下. 

为了优雅的管理数据库的 Session, 我封装了一个DatabaseSessionManager类. 下面给出一个概括版的实现示例.

```python

import contextlib
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

class DatabaseSessionManager:
    """
    一个用于管理数据库引擎和会话的类。
    """
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
        if self._engine is None:
            logger.debug("DatabaseSessionManager already closed or not initialized")
            return
        try:
            await self._engine.dispose()
            logger.debug("数据库引擎已关闭")
        except Exception as e:
            logger.error(f"关闭数据库引擎时出错: {e}")
        finally:
            self._engine = None
            self._sessionmaker = None

```

然后在Repository中这样使用:

```python

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

```

这样, 看起来在每一次数据库操作中, session 都会通过 `async with` 正确地被管理, 无论怎样都会被关闭. 

之前的并发需求并不高, 一直没有显露问题. 然而做了几百组的并发测试, 却发现疯狂报 TooManyConnectionsError. 

最后意识到是因为我在依赖注入中重复创建了 DatabaseSessionManager 的实例. 

```python

def get_user_repo() -> UserRepository:
    # 致命错误：每次调用都创建一个新的DatabaseSessionManager实例！
    # 这意味着每次都创建了一个全新的数据库引擎和连接池！
    # 而且没有人调用这个session_manager的close方法!
    session_manager = DatabaseSessionManager(settings.database_url)
    return UserRepository(session_manager)

async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserManager:
    return UserService(repository) # Boom

```

SQLAlchemy推荐的实践是, 整个进程公用一个engine, 尽可能短暂的使用每一个session, session 用完即弃. 

因此, 内部管理了数据库引擎和连接池的 DatabaseSessionManager 必须是全局唯一的单例. 上面的错误代码实际上是破坏了单例模式. 

在基本没有并发需求的时候, 请求密度很低, 问题没有显现的原因是 Python 的垃圾回收机制定时回收了不再使用的 engine, 同时 PostgreSQL 服务器的空闲连接超时也会断开连接. 但并发量大起来之后, 这两个机制就不可能跟的上连接创建的速度了. 

因此如何解决就很显然了, 保证全局单例即可.

我们可以在应用启动时显式初始化:

```python

# session.py
class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict = {}):
        pass
    @contextlib.asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        pass
    async def close(self):
        pass

sessionmanager: Optional[DatabaseSessionManager] = None

# main.py
import app.session as session_module

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 步骤 1: 确保配置已完全加载。
    from app.core.config import settings

    # 步骤 2: 使用最终的 settings 对象来创建 sessionmanager 实例。
    db_manager = DatabaseSessionManager(host=settings.database_url, ...)

    # 步骤 3: 将创建好的实例赋给 session 模块的全局变量。
    session_module.sessionmanager = db_manager

    # 现在，应用的任何其他部分都可以安全地使用 sessionmanager 了
    await db_manager.check_database_health()

    yield
    
    # ... 清理工作 ...

# deps.py
from app.session import sessionmanager
from repositories.user import UserRepository

# 可以将 repo 也提升为模块级实例，因为它现在是无状态的
user_repo = UserRepository(sessionmanager)

def get_user_repo() -> UserRepository:
    return user_repo

```

这样修复之后, 应用受到的高并发请求不会因为连接溢出而立刻崩溃, 而是让请求排队等待数据库响应. 


