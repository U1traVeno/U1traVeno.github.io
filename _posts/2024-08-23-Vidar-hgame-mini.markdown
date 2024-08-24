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

![Hint](/img/in-post/2024-08-23-1.png)

Please use the HTTP header field that identifies the address of the web page, from which the resource has been requested.

这是啥意思。它还说要从vidar.club来到这个页面。

在 [Web安全学习笔记](https://websec.readthedocs.io/zh/latest/) 里面找到了这个

需要注意的是，Referer是错误的拼写，就像creat一样，把错误的一直沿用了下来。

![Referer请求头](/img/in-post/2024-08-23-2.png)

于是我试着把刚刚接收到的http请求加上这个字段重发一下

![加上字段](/img/in-post/2024-08-23-3.png)

但是不行。响应头除了时间是一样的。于是就在这里卡住了。

*2024-8-24-01:07*

---

卡住的原因和那个https输入不了的问题有关。问了l1nk, 他告诉我这里直接输入[vidar.club](vidar.club)就好，不用加上前面的`https://`。但是Firefox的开发者不加这个是没法发过去的呀！遂下了一个Hackbar插件在firefox上，叫做 [HackBar V2](https://addons.mozilla.org/zh-CN/firefox/addon/hackbar-free/) 。用它就可以随意的修改Referer了。

![24-8-24-1](/img/in-post/2024-08-24-1.png)

看到新提示，应该是user-agent。直接复制过来重新Excecute

![24-8-24-2](/img/in-post/2024-08-24-2.png)

现在提示说让请求从本地来到这个页面，一开始以为是`Referer: http://127.0.0.1/`。但是并不是这样。

加上了`Origin: http://127.0.0.1/`。

但并不行，又试了一下`X-Forwarded-For: 127.0.0.1`，可行。这两个有什么区别呢？

下一个提示是：
> Hello guest! only admin can get flag.
所以要伪装成管理员。

注意到Cookies中，有一个user=guest。改成user=admin。

下一个提示：
> You are admin! Flag is in this page
又一次卡住了。之前学到的在html里面找元素的方法失效了，没找到flag。

---

更新，找不到是因为其实响应头里面有一个Fl4g: 但是请看
![082403](/img/in-post/2024-08-24-3.png)

## How to use developer tools (100pt)

打开F12, 发现html里面给这些按钮加上了`onclick="return False"`。把这些改掉就可以跳转了。

![html](/img/in-post/2024-08-23-4.png)

根据提示来到182.xx.xx.xx:xxxxx/L00kAtME.php

![L00kAtME](/img/in-post/2024-08-23-5.png)

`disabled="disabled"`?? 删！

![删](/img/in-post/2024-08-23-6.png)

这里只拿到一部分flag。另一部分在f12网络模块GET到的一个包里面的消息头。

f12有用捏

## Get Post Universe (150pt)

根据名字，是要用到 GET 和 POST 两个方法吗？

并没有。GET请求里加上了Money: 10000没有效果。

在网址后面加上`/?money=10000`, 行了。
![082404](/img/in-post/2024-08-24-4.png)

第二个提示。POST card_id=xxx。

用之前的Hackbar去POST一个参数。记得点一下load URL，图片中忘记点了。之后便得到Flag
![082405](/img/in-post/2024-08-24-5.png)
![082406](/img/in-post/2024-08-24-6.png)




