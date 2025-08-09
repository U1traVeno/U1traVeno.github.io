---
date: '2025-07-20T00:21:21+08:00'
draft: false
title: '[HDU-CS-Wiki 后端教程] 大纲'
tags: ['HDU-CS-Wiki', '后端']
comments: true
---

## Before Beginning

- 前置知识需求: CS61A, 或掌握至少一门编程语言（如Python）的扎实基础，理解函数、类、简单数据结构（列表、字典、集合等）、递归等核心编程概念, 畅通的网络环境, 了解Python的基础写法, 基本的英语阅读能力, 提问的艺术, 基础CLI操作

## 第一部分： 后端基础 (Python + FastAPI + SQLModel)

### 教学目标(一)

- 快速上手: 让学生在几小时内，从零开始搭建起一个功能完整的 CRUD (增删改查) API。
- 建立自信: 通过 FastAPI 强大的自动文档和 SQLModel 的易用性，让学生感受到现代工具带来的便捷，消除对后端的畏难心理。
- 文档阅读: FastAPI 有着非常用户友好的文档, 利用它来培养阅读文档的习惯. 这也是本教程选择SQLModel而不是SQLAlchemy的原因之一
- 正确使用AI: 不要让Copilot变成Copybot
- 整个教程的每个模块会维护和精进同一个项目(不与 Project 1 相同, 教程项目更倾向于教学示范)
- 理解或掌握以下知识：

1. 路由函数 (Routing) 与 HTTP 方法 (GET, POST, PUT, DELETE)。
2. SQL, ORM 与数据库操作 (CRUD)。
3. API-服务-数据 的基本三层架构模式。
4. 中间件 (Middleware) 的作用。
5. 基本的安全思想.
6. 基本的单元测试和集成测试概念和写法
7. 配置管理: 学会分离开发, 测试, 生产环境
8. 学会现代部署: 掌握使用 Docker 和 Docker Compose 对应用进行容器化部署的基本技能。
9. 学会阅读框架文档
10. 基本的 Git 团队协作能力

### 课程大纲(一)

#### Lab 0

- VSCode 配置, [环境变量, Python 虚拟环境, PEP规范和类型标注](https://fastapi.tiangolo.com/zh/python-types/)
- 前后端的基本概念, 后端是什么
- uv Python 环境管理
- Git基本配置, Github
- ...

#### 模块一: API 和 HTTP

- API 和 路由函数
- 路径参数和查询参数
- HTTP, GET 和 POST 方法
- 请求体和数据校验(pydantic)
- API 文档 (展示FastAPI的自动生成的 Swagger 文档)
- ...
- 作业:
  - 阅读文档, 找到如何使用 FastAPI 构造一个上传文件的接口.
  - 通过阅读文档, 发现并解决 FastAPI 中路由函数先后定义产生的问题.
- 拓展阅读:
  - HTTP MDN, 图解HTTP
  - RESTful API 和 WebSocket
  - API测试工具
  - ...

#### 模块二： 数据库

- SQL语句: 手动使用SQL来进行基础的查询和数据库操作
- ORM 与模型: ORM概念, 使用 SQLModel，定义第一个数据模型。
- 连接数据库: 使用 SQLite 作为入门数据库，配置数据库连接。
- 实现 CRUD: 编写完整的增、删、改、查四个 API 接口。
- 数据库事务的概念和重要性(ACID), SQLModel 的 session
- 索引设计
- 作业:
  - 提供一个复杂的数据库 ER 图, 要求编写几个不同复杂度的 SQL 查询语句, 覆盖连接 (JOIN), 分组 (GROUP BY), 子查询等。
  - 用ORM的关系预加载优化一个 N+1 查询问题.
- 拓展阅读:
  - SQL, NoSQL(MongoDB, Redis, Neo4j)
  - 索引, 外键, 多对多...
  - alembic 等数据库同步工具
  - ACID、CAP 和 BASE
  - 软删除
  - SQL 注入
  - ...

#### 模块三： 代码的规范化

- **问题引入**: 当业务逻辑变复杂时，所有代码都写在路由函数里的坏处。
- 重构代码: 引入三层架构思想, 把先前的代码清晰分为API层, 服务层, 路由层.
- 如何避免过度设计
- 拓展阅读:
  - IoC 和 依赖注入
  - [22种设计模式](https://refactoringguru.cn/design-patterns/catalog)
  - SOLID 原则
  - 领域驱动设计
  - ...

#### 模块四： 中间件

- 中间件基本概念
- 中间件一般应用场景
- 错误处理中间件(统一错误响应格式)
- CORS中间件
- 作业:
  - 编写一个简单的记录API日志的中间件, 统计请求处理时长.
  - 实现自定义异常处理中间件
- 拓展阅读:
  - ...

#### 模块五: 基本的安全思想

- JWT Token
- passwd_hashed
- CORS
- 环境变量管理敏感信息
- 永远不要相信用户的输入
- ...
- 作业:
  - 实现一个完整的注册登陆流程, 密码哈希存储
  - 利用中间件实现API的Token鉴权
  - ...
- 拓展阅读:
  - ...

#### 模块六：交付你的第一个后端服务 (容器化)

- Docker 入门: 讲解什么是 Docker, 它解决了什么问题.
- Dockerfile: 为 FastAPI 应用编写一个 Dockerfile
- Docker Compose
- 作业:
  - ...
- 拓展阅读:
  - 除了Docker以外的容器, Podman, container.d
  - CI/CD, Github Actions
  - ...

#### Project 1: 电子书商城

- 与前端组协调, 后端小组与前端小组共同完成电子书商城项目.
- 要求:
  - 强制使用 Feature Branch 工作流
  - 编写有意义的 Commit Message
  - 团队成员之间需要进行 Code Review

## 第二部分： 后端进阶 (Go + Gin)

### 教学目标(二)

- 深入原理: 通过 Go 的显式特性，让学生深刻理解路由、中间件、ORM 等概念的底层实现本质。
- 培养底层思维: 从一个“框架使用者”转变为一个能思考性能、并发、内存管理的“工程师”。
- 掌握 Go 后端开发: 熟练使用 Go 语言、Gin 框架和 GORM 来构建高性能的后端服务，并掌握 Go 的指针、错误处理等核心特性。
- 熟悉高级组件: 使用 Redis 缓存，使用消息队列。
- 衔接微服务架构: 理解从单体应用到微服务的演进过程，初步掌握 RPC (gRPC)、服务注册与发现、容器编排 (Kubernetes) 等核心概念。

### 课程大纲(二)

### Lab 0: Go语言基础

Go 语法, Go环境搭建, 工作区概念, Go Modules, Goroutine

### 模块一： 重新认识路由和框架

- 路由的本质: 先用 Go 标准库 net/http 手写一个简单的 Web 服务器，暴露路由函数。
- 引入 Gin: 讲解 Gin 如何用更优雅的方式解决了 net/http 的路由和分组问题。
- Gin 的 Context
- ...
- 作业:
  - 尝试使用 net/http 实现一个支持不同HTTP方法的路由分发器
- 拓展阅读:
  - gin-swagger
  - 大厂基于Gin的框架
  - GORM

### 模块二： 再论架构与中间件的本质

- 通过接口和构造函数手动注入依赖, 本质上为了解决相同的问题
- 中间件的本质: 手写一个最简单的 Gin 中间件, 本质是一个接收 *gin.Context 并调用 c.Next() 的函数. 责任链模式.
- ...
- 作业:
  - 替换Gin框架的默认Logger中间件
  - 实现一个 Panic 恢复中间件, 确保单个请求的崩溃不会导致整个服务宕机, 并能记录下崩溃的堆栈信息
- 拓展阅读:
  - Go的闭包
  - go 的反射机制和适用场景
  
### 模块三: 消息队列

- 问题引入: 当服务所需要的请求量越来越多
- RabbitMQ(AMQP 模型) 和 Kafka(流模型) 的区别和适用场景
- ACK, 持久化和重试
- 什么时候应当为系统引入消息队列才不会显得累赘
- ...
- 作业:
  - 实现一个异步任务, 通过API提交某个耗时请求之后, 服务将任务放入RabbitMQ后立即返回, 让一个Worker服务消费任务
- 拓展阅读:
  - 死信队列
  - Kafka核心概念: Topic, Partition, Offset, Consumer Group
  - RocketMQ
  
### 模块四: 缓存

- Redis
- 缓存的常见策略 (Cache-aside, Read-through, Write-through)
- 缓存穿透、缓存击穿、缓存雪崩的原因和解决方案
- Redis 常见数据结构的使用场景
- 什么时候应当引入缓存才不会显得累赘
- ...
- 作业:
  - 为某个高频读取的API增加Redis缓存(Cache-aside), 并进行压测, 对比QPS和响应时间。
- 拓展阅读:
  - 缓存与数据库一致性问题
  - 分布式锁的概念与基于Redis的实现

### 模块五：从单体到微服务

- 单体应用的痛点, 为什么业界会需要微服务架构
- RPC概念, 以及RPC的底层本质
- gRPC: Protobuf, 服务定义, 四种通信模式, 在Go中的实践
- 作业:
  - 创建两个微服务：user-service 和 order-service。order-service 在创建订单时，需要通过 gRPC 调用 user-service 来验证用户信息是否存在

### 模块六：Kubernetes

- 什么是容器编排? 为什么已经有compose了还需要k8s?
- k8s 架构和核心概念讲解
- kind
- 作业:
  - 为一个简单的微服务编写Kubernetes的Deployment和Service的YAML文件, 并使用kind在本地部署起来
  - 在kind集群中滚动更新 (Rolling Update) 和回滚 (Rollback) 一个服务
- 拓展阅读:
  - k8s 官方文档
  - ...

### Project 2 : 电商平台

参考2024年字节后端青训营项目. 要求使用gRPC的微服务架构, 使用k8s集群进行部署.

### 延伸

一起收集一下常见的各种典型后端项目的设计与实现方式.
