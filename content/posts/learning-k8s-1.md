---
date: '2025-03-20T22:28:19+08:00'
draft: true
title: 'K8S学习笔记-1-总览k8s'
cover: 
    image: "images/1024px-kubernetes_logo.png"
tags: ['Kubernetes', 'docker']
---

之前只是粗略过了一遍k8s的文档，简单跑了一下minikube，又去油管看了看什么Kubernetes的入门教程。但不写博客总是会忘干净的，毕竟设立博客的一部分初衷就是作为学习笔记使用啊。

开这个坑准备记录自己作为一个完全的初学者对于k8s的理解。

## 什么是Kubernetes? 它解决了什么问题？

Kubernetes(简称k8s)是容器编排框架，能编排成百上千的容器，并且可以轻松让它们部署到实体机，虚拟机，或是云环境。

{{<collapse summary="官方文档对于k8s能做什么是这么说的(可以展开)">}}

### 服务发现和负载均衡

Kubernetes 可以使用 DNS 名称或自己的 IP 地址来暴露容器。 如果进入容器的流量很大， Kubernetes 可以负载均衡并分配网络流量，从而使部署稳定。

### 存储编排

Kubernetes 允许你自动挂载你选择的存储系统，例如本地存储、公共云提供商等。

### 自动部署和回滚

你可以使用 Kubernetes 描述已部署容器的所需状态， 它可以以受控的速率将实际状态更改为期望状态。 例如，你可以自动化 Kubernetes 来为你的部署创建新容器， 删除现有容器并将它们的所有资源用于新容器。

### 自动完成装箱计算

你为 Kubernetes 提供许多节点组成的集群，在这个集群上运行容器化的任务。 你告诉 Kubernetes 每个容器需要多少 CPU 和内存 (RAM)。 Kubernetes 可以将这些容器按实际情况调度到你的节点上，以最佳方式利用你的资源。

### 自我修复

Kubernetes 将重新启动失败的容器、替换容器、杀死不响应用户定义的运行状况检查的容器， 并且在准备好服务之前不将其通告给客户端。

### 密钥与配置管理

Kubernetes 允许你存储和管理敏感信息，例如密码、OAuth 令牌和 SSH 密钥。 你可以在不重建容器镜像的情况下部署和更新密钥和应用程序配置，也无需在堆栈配置中暴露密钥。

### 批处理执行 
除了服务外，Kubernetes 还可以管理你的批处理和 CI（持续集成）工作负载，如有需要，可以替换失败的容器。
水平扩缩 使用简单的命令、用户界面或根据 CPU 使用率自动对你的应用进行扩缩。
IPv4/IPv6 双栈 为 Pod（容器组）和 Service（服务）分配 IPv4 和 IPv6 地址。
为可扩展性设计 在不改变上游源代码的情况下为你的 Kubernetes 集群添加功能。

{{</collapse>}}

我觉得文档看着头昏，不如举个例子。

假设你写了个电商系统，整个系统使用微服务架构，用户服务，订单服务，支付服务，库存服务啥啥的。

现在你的每一个服务都跑在Docker里，在十台服务器上运行。

- 你得手动决定每个服务跑在哪个服务器上。用户服务放服务器 1 和 2，订单服务放 3 和 4。一旦有新服务器加入或老服务器宕机，你得重新手动分配，还要 SSH 登录每台机器拉镜像、跑容器。

- 双十一流量暴增，支付服务的一个容器挂了。你半夜被叫醒，登录服务器，查日志，重启容器。结果发现是内存不够，得再加一台机器，手动把容器迁移过去。

- 用户服务流量激增，两个容器不够用。你得自己搭个 Nginx，手动配置负载均衡规则，把流量分到不同容器，还要实时监控，流量大了再加容器，少了再减。

- 订单服务需要调用用户服务查用户信息，但用户服务的容器 IP 变了，你得手动更新订单服务的配置，或者自己写脚本维护一个服务发现机制。

- 你给库存服务发了个新版本，结果有 bug，库存显示全错。只能一台一台回滚，手动停掉新容器，跑回老版本的镜像，整个过程可能花好几个小时。

这还只是几个服务。但如果有上百个服务呢？

用k8s之后，部署只要写个yaml，`kubectl apply -f`。服务挂了会自动重启或者替换。同时k8s会自动负载均衡，流量大就加pod，流量小就减pod。容器的IP也不用操心，k8s抽象出了Service层来解决IP问题。版本更新和回滚也很方便，`kubectl rollout/rollback`。

## K8S 基本架构

![K8S架构图](https://kubernetes.io/images/docs/components-of-kubernetes.svg)

一个集群（Cluster）有至少一个控制平面（Control Plane）。控制平面上连着几个工作节点（Worker Node）。每一个工作节点上可能有几个容器。

每一个节点上都运行着一个kubelet，它可以保证各个节点间的通信，在Pod上运行一些东西。

### 控制平面(Control Plane)
[**控制平面**](https://kubernetes.io/zh-cn/docs/concepts/overview/components/#control-plane-components)只运行一些k8s所必要的进程，主要有四个：API Server，Controller Manager, Scheduler，etcd。控制平面一般会有多个节点来保证可用性，我们叫这些节点 Master Node。下面简略讲讲控制平面主要的四个组件。

**API Server**，它也是个容器，它公开了 Kubernetes API，可以理解为每个 cluster 的入口，负责接收处理请求。

**Controller Manager**，接收整个集群的运行信息，比如什么东西需要维修，或者什么容器挂了要重启之类的。

**Scheduler**，负责根据各个 Node 的工作负载，剩余资源，把新的Pod分配给不同的Node。

**etcd**，一致且高可用的键值存储，用作 Kubernetes 所有集群数据的后台数据库，里面存着各种配置文件数据、每个节点各个时间的状态数据，这就相当于存了很多快照，k8s的回滚就是依赖于它。etcd 这个名字听着很抽象。etcd 发音为/ˈɛtsiːdiː/，意思是“distributed `etc` directory”，分布式配置文件目录。我们知道linux中`/etc`目录一般存一些系统和应用程序的配置文件，etcd就是分布式的`/etc`。

### Node and Pod

k8s中的工作机器称为节点(node)。Pod 是集群上一组运行的容器，是 k8s 最小的抽象单元。

我们不能简单的把它们理解为 Pod 构成了 Node, Node 中包含 Pod 。准确来说它们的关系是运行与承载。Node 是硬件或资源的实体，Pod 是运行在这个实体上的工作负载。换句话说，Node 承载了 Pod，而不是 Pod 组成了 Node。

Pod 中可以运行多个容器。但最佳实践一般是每一个 pod 只跑一个容器。如果多容器，也应该是：一个主要应用容器，还有一些辅助容器，或者什么必须得跑在那个 pod 里的服务。

### Service and Ingress

每个 Pod 都有一个内部IP地址。那么如果Pod挂了重启，我们怎么保证其他的 Pod 还能迅速获取到新的IP呢？ 

K8s引入了 [**Service**](https://kubernetes.io/zh-cn/docs/concepts/services-networking/service/#services-in-kubernetes) 的抽象层，这就可以为Pod提供了稳定的访问入口。可以简单的理解为，Service给一组Pod提供了一个稳定的虚拟IP(ClusterIP)，它只在集群内部使用的地址可以分配给每一个Pod。比如说Service和Pod的生命周期不同步。也就是说，即使Pod死了，下一个Pod仍然可以从同一个Service获取同样的地址。

Service是一个集群内部的IP地址。而[**Ingress**](https://kubernetes.io/zh-cn/docs/concepts/services-networking/ingress/)所做的事情是为Service提供可以从集群外部访问的路由规则和入口（域名，路径，HTTP）。它通过 [**Ingress Controller**](https://kubernetes.io/zh-cn/docs/concepts/services-networking/ingress-controllers/) 实现。

准确的说，Service并不是不能提供外部访问。可以开一个固定的NodePort。但显然这样不灵活。

### ConfigMap and Secret

