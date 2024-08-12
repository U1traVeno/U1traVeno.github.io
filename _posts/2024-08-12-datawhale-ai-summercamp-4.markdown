---
layout:     post
title:      "Datawhale AI夏令营 第四期方向二笔记"
subtitle:   "与大项目的第一次接触"
date:       2024-08-12 17:19:00
author:     "U1traVeno"
header-img: "img/tag-bg.jpg"
tags:
    - Datawhale
    - AI
---

# Datawhale AI夏令营 第四期方向二笔记

**在夏令营结束前会持续更新**

----------------

## Task1

夏令营的第一个任务

### Task总结
本次task带着像我这种零基础小白一步步实现了在云端部署一个大语言模型，可以辅助我们编程。  
通过课后精读baseline代码，可以理解熟悉如何在代码中调用api，对我这样的只会基本语法的选手帮助甚多  

### 流程  

#### Step0 开通阿里云PAI-DSW试用  

跟着教程就好啦~

#### Step1 在魔搭创建PAI实例  

这里也是点点点就好了。终端似乎是类unix命令行，对我这种经常用linux的玩家很友好(

#### Step2 Demo搭建!  

有朋友碰到下载慢或者失败的问题，可以更换pip镜像源来解决  

这里也是跟着教程一路顺利走下来了~~虽然有点感觉懵懵的~~  

**不能忘记回魔搭关闭实例！！！**
**不能忘记回魔搭关闭实例！！！**
**不能忘记回魔搭关闭实例！！！**

#### Baseline精读  

之前的步骤都点点点就好了，没啥难度。我觉得真正吸引我的还是后面的baseline精读。    

在这贴一个baseline代码
```python

# 导入所需的库
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import streamlit as st

# 创建一个标题和一个副标题
st.title("💬 Yuan2.0 智能编程助手")

# 源大模型下载
from modelscope import snapshot_download
model_dir = snapshot_download('IEITYuan/Yuan2-2B-Mars-hf', cache_dir='./')
# model_dir = snapshot_download('IEITYuan/Yuan2-2B-July-hf', cache_dir='./')

# 定义模型路径
path = './IEITYuan/Yuan2-2B-Mars-hf'
# path = './IEITYuan/Yuan2-2B-July-hf'

# 定义模型数据类型
torch_dtype = torch.bfloat16 # A10
# torch_dtype = torch.float16 # P100

# 定义一个函数，用于获取模型和tokenizer
@st.cache_resource
def get_model():
    print("Creat tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(path, add_eos_token=False, add_bos_token=False, eos_token='<eod>')
    tokenizer.add_tokens(['<sep>', '<pad>', '<mask>', '<predict>', '<FIM_SUFFIX>', '<FIM_PREFIX>', '<FIM_MIDDLE>','<commit_before>','<commit_msg>','<commit_after>','<jupyter_start>','<jupyter_text>','<jupyter_code>','<jupyter_output>','<empty_output>'], special_tokens=True)

    print("Creat model...")
    model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch_dtype, trust_remote_code=True).cuda()

    print("Done.")
    return tokenizer, model

# 加载model和tokenizer
tokenizer, model = get_model()

# 初次运行时，session_state中没有"messages"，需要创建一个空列表
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 每次对话时，都需要遍历session_state中的所有消息，并显示在聊天界面上
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 如果用户在聊天输入框中输入了内容，则执行以下操作
if prompt := st.chat_input():
    # 将用户的输入添加到session_state中的messages列表中
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 在聊天界面上显示用户的输入
    st.chat_message("user").write(prompt)

    # 调用模型
    prompt = "<n>".join(msg["content"] for msg in st.session_state.messages) + "<sep>" # 拼接对话历史
    inputs = tokenizer(prompt, return_tensors="pt")["input_ids"].cuda()
    outputs = model.generate(inputs, do_sample=False, max_length=1024) # 设置解码方式和最大生成长度
    output = tokenizer.decode(outputs[0])
    response = output.split("<sep>")[-1].replace("<eod>", '')

    # 将模型的输出添加到session_state中的messages列表中
    st.session_state.messages.append({"role": "assistant", "content": response})

    # 在聊天界面上显示模型的输出
    st.chat_message("assistant").write(response)

```

对我这种刚学了cs61a的新人来说  
~~完全看不懂啊喂~~  
不过自己感觉还是被一大段代码吓到了。冷静下来自己读读还是能知道在做什么的  

------------
