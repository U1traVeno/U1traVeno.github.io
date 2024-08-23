---
layout:     post
title:      我的 Vidar-hgame-mini 解题过程
subtitle:   信息安全领域的第一次接触
author:     U1traVeno
date:       2024-08-23
img:        img/tag-bg.jpg
tags:
    - Web
    - CTF
    - Vidar
--- 

> 将在hgame-mini结束之前长期更新

这篇文章将记录自己解题的心路历程。写的可能比较杂，按照自己做题顺序。不定期更新。

各个领域的start题目看完，发现自己大概还是对web更感兴趣一点。所以大概率这里大多数都是web的题(甚至全是

-----

*2024-08-23*

## Do you know http (100pt)

了解了一下http请求是怎么构成的。

[http消息结构 (runoob)](https://www.runoob.com/http/http-messages.html)

打开F12, 刷新靶机网站，定睛一看，响应头里有个Hint

![Hint](https://github.com/U1traVeno/U1traVeno.github.io/blob/main/img/in-post/2024-08-23-1.png)

Please use the HTTP header field that identifies the address of the web page, from which the resource has been requested.

这是啥意思。它还说要从vidar.club来到这个页面。

在 [Web安全学习笔记](https://websec.readthedocs.io/zh/latest/) 里面找到了这个

![Referer请求头](https://github.com/U1traVeno/U1traVeno.github.io/blob/main/img/in-post/2024-08-23-2.png)

于是我试着把刚刚接收到的http请求加上这个字段重发一下

![加上字段](https://github.com/U1traVeno/U1traVeno.github.io/blob/main/img/in-post/2024-08-23-3.png)

但是不行。响应头除了时间是一样的。

这里还有一个不知道为啥的问题，有时候像上面这样加了一个字段之后，点击不了下面的发送。不知道怎么回事。于是准备先睡觉了，此时是8.23的两点钟了。