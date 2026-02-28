---
title: "初试渗透测试，尝试构建 AI 渗透工作流"
description: 
date: 2026-02-25T17:53:41+08:00
image: 
math: 
license: 
hidden: false
comments: true
draft: false
---

其实是寒假作业，但是觉得做的东西还是很有意义的，需要好好记录。

作业要求 Code is cheap, show me the talk. 所以秉承这样的观点，并且尽量让工作流 AI 化。

本文中人类的 prompt 将用 Markdown 引用语法标注。

## fscan 二次开发

### 正则提取 poc 响应关键字

本节使用 Claude Sonnet 4.6

[fscan](https://fscan.club/#/) 默认的 yaml 语法是 xray 风格的，没有提取响应的功能。希望给 fscan 补充正则提取响应关键字段的功能。

fork 一下 fscan 的仓库，从 v1.8.4 release 开始开了个 `feat/show-output` 分支，因为听说后续的 main 分支使用体验并不很好。

claude code /init 一下。看了眼感觉不够满意，因为需要补充新增 WebScan 的扫描输出的功能，所以让它补充研究了一下 WebScan 的代码结构，记录在 CLAUDE.md。

> 1. 着重关注一下 WebScan 的代码结构，一并记录在 CLAUDE.md。
> 2.使用 web_search mcp 工具，查看 fscan 文档 <https://fscan.club/#/docs>, 在 CLAUDE.md 中记录 fscan 特有的构建约束的说明，记录常用的构建约束指令。注意遵循此次对 CLAUDE.md 的修改仍然遵循 /init 命令的原则：
>
> - "Focus on the big picture architecture"
> - "Avoid listing every component"
> - "Don't include generic development practices"

此处的 web_search mcp 来自 MiniMax，结果发现在有精确网址的情况下不太好用，claude 自己用 fetch 了。

然后开始 vibe coding。习惯使用 plan mode 先让它讲清楚计划，看了没有很离谱才让它继续写。

> 在 WebScan/ 中通过解析 poc 的响应内容，允许用户在 poc yaml 中使用正则表达式提取和编写 exp 相关的字段。下面给出样例：
>
> ```text
> [+] PocScan http://10.3.4.78:8848 poc-yaml-nacos-multi-check-auth-bypass
>    * accessToken: xxxxxxxxxx
>    * username: xxxxxxxxxx
>    * password: xxxxxxxxxx
> ```

{{< details summary="Plan: Display POC Search-Extracted Variables in Output" >}}

````markdown

Plan: Display POC Search-Extracted Variables in Output

Context

Currently, when a POC succeeds in normal mode (rules-based), named capture groups extracted from HTTP responses via the search regex field are stored in
variableMap for use in subsequent rules but are never displayed to the user. The user wants these extracted values (e.g., access tokens, credentials)
to appear in the scan output below the POC result line:

[+] PocScan http://10.3.4.78:8848 poc-yaml-nacos-multi-check-auth-bypass
 * accessToken: xxxxxxxxxx
 * username: xxxxxxxxxx
 * password: xxxxxxxxxx

Critical File

Only one file needs modification:
/Users/veno/Projects/fscan/WebScan/lib/check.go

Implementation

1. Add "sort" import

In the import block, add "sort" (alphabetically between "regexp" and "strings").

2. Modify executePoc signature

From:
func executePoc(oReq *http.Request, p *Poc) (bool, error, string)
To:
func executePoc(oReq *http.Request, p *Poc) (bool, error, string, map[string]string)

3. Declare searchVars after variableMap (line ~80)

variableMap := make(map[string]interface{})
defer func() { variableMap = nil }()
searchVars := make(map[string]string)  // ADD THIS
variableMap["request"] = req

4. Populate searchVars in DealWithRule closure

Change the search block inside DealWithRule from:
if rule.Search != "" {
 result := doSearch(rule.Search, GetHeader(resp.Headers)+string(resp.Body))
 if len(result) > 0 { // 正则匹配成功
     for k, v := range result {
         variableMap[k] = v
     }
 } else {
     return false, nil
 }
}
To:
if rule.Search != "" {
 result := doSearch(rule.Search, GetHeader(resp.Headers)+string(resp.Body))
 if len(result) > 0 { // 正则匹配成功
     for k, v := range result {
         variableMap[k] = v
         if k != "" { // only named groups; unnamed groups have empty-string key
             searchVars[k] = v
         }
     }
 } else {
     return false, nil
 }
}

5. Update all return statements in executePoc

┌──────┬────────────────────────────────────────┬───────────────────────────────────────┐
│ Line │                  From                  │                  To                   │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~72  │ return false, err, ""                  │ return false, err, "", nil            │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~77  │ return false, err, ""                  │ return false, err, "", nil            │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~86  │ return false, nil, ""                  │ return false, nil, "", nil            │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~100 │ return success, nil, "" (Sets/cluster) │ return success, nil, "", nil          │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~193 │ return success, nil, name (Groups)     │ return success, nil, name, searchVars │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~198 │ return success, nil, "" (Rules final)  │ return success, nil, "", searchVars   │
└──────┴────────────────────────────────────────┴───────────────────────────────────────┘

6. Update CheckMultiPoc to display extracted variables

From:
isVul, _, name := executePoc(task.Req, task.Poc)
if isVul {
 result := fmt.Sprintf("[+] PocScan %s %s %s", task.Req.URL, task.Poc.Name, name)
 common.LogSuccess(result)
}
To:
isVul, _, name, extractedVars := executePoc(task.Req, task.Poc)
if isVul {
 result := fmt.Sprintf("[+] PocScan %s %s %s", task.Req.URL, task.Poc.Name, name)
 if len(extractedVars) > 0 {
     keys := make([]string, 0, len(extractedVars))
     for k := range extractedVars {
         keys = append(keys, k)
     }
     sort.Strings(keys)
     for _, k := range keys {
         result += fmt.Sprintf("\n    * %s: %s", k, extractedVars[k])
     }
 }
 common.LogSuccess(result)
}

Design Decisions

- Sort keys alphabetically: Go map iteration is non-deterministic; sorting ensures consistent, reproducible output.
- Single LogSuccess call: Builds the full multi-line string before calling LogSuccess to prevent interleaving from concurrent goroutines.
fmt.Println/color.Red in SaveLog handle multi-line strings correctly. WriteFile also works with multi-line strings (plain text appends result + "\n";
JSON output: Go's json.Marshal escapes embedded newlines).
- Exclude unnamed groups (k != ""): doSearch can return "" as a key for unnamed capture groups; these are internal and should not appear in output.
- set variables not in searchVars: set variables are added to variableMap directly (not through doSearch), so they can never enter searchVars.
- brute-force path unchanged: clusterpoc already has its own output with credentials in tmpMap.
- Groups mode returns searchVars: For consistency, the groups path also returns searchVars (line 193) so POCs using groups format also display extracted
variables.

Verification

# Build to confirm compilation
go build -o fscan main.go

# Run against a target with a POC that uses search patterns (e.g., nacos auth bypass)
./fscan -h <target> -m webonly -poc poc-yaml-nacos-multi-check-auth-bypass

# Expected: output shows extracted variables indented below the POC result line
````

{{< /details >}}

此处有点问题因为我还没真的写这个模板。应该让它自己写简单的测试用 yaml 和简单的服务进行测试。

{{< details summary="Plan: Display POC Search-Extracted Variables in Output" >}}

````markdown
Plan: Display POC Search-Extracted Variables in Output

Context

Currently, when a POC succeeds in normal mode (rules-based), named capture groups extracted from HTTP responses via the search regex field are stored in
variableMap for use in subsequent rules but are never displayed to the user. The user wants these extracted values (e.g., access tokens, credentials)
to appear in the scan output below the POC result line:

[+] PocScan http://10.3.4.78:8848 poc-yaml-nacos-multi-check-auth-bypass
 * accessToken: xxxxxxxxxx
 * username: xxxxxxxxxx
 * password: xxxxxxxxxx

Critical File

Only one file needs modification:
/Users/veno/Projects/fscan/WebScan/lib/check.go

Implementation

1. Add "sort" import

In the import block, add "sort" (alphabetically between "regexp" and "strings").

2. Modify executePoc signature

From:
func executePoc(oReq *http.Request, p *Poc) (bool, error, string)
To:
func executePoc(oReq *http.Request, p *Poc) (bool, error, string, map[string]string)

3. Declare searchVars after variableMap (line ~80)

variableMap := make(map[string]interface{})
defer func() { variableMap = nil }()
searchVars := make(map[string]string)  // ADD THIS
variableMap["request"] = req

4. Populate searchVars in DealWithRule closure

Change the search block inside DealWithRule from:
if rule.Search != "" {
 result := doSearch(rule.Search, GetHeader(resp.Headers)+string(resp.Body))
 if len(result) > 0 { // 正则匹配成功
     for k, v := range result {
         variableMap[k] = v
     }
 } else {
     return false, nil
 }
}
To:
if rule.Search != "" {
 result := doSearch(rule.Search, GetHeader(resp.Headers)+string(resp.Body))
 if len(result) > 0 { // 正则匹配成功
     for k, v := range result {
         variableMap[k] = v
         if k != "" { // only named groups; unnamed groups have empty-string key
             searchVars[k] = v
         }
     }
 } else {
     return false, nil
 }
}

5. Update all return statements in executePoc

┌──────┬────────────────────────────────────────┬───────────────────────────────────────┐
│ Line │                  From                  │                  To                   │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~72  │ return false, err, ""                  │ return false, err, "", nil            │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~77  │ return false, err, ""                  │ return false, err, "", nil            │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~86  │ return false, nil, ""                  │ return false, nil, "", nil            │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~100 │ return success, nil, "" (Sets/cluster) │ return success, nil, "", nil          │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~193 │ return success, nil, name (Groups)     │ return success, nil, name, searchVars │
├──────┼────────────────────────────────────────┼───────────────────────────────────────┤
│ ~198 │ return success, nil, "" (Rules final)  │ return success, nil, "", searchVars   │
└──────┴────────────────────────────────────────┴───────────────────────────────────────┘

6. Update CheckMultiPoc to display extracted variables

From:
isVul, _, name := executePoc(task.Req, task.Poc)
if isVul {
 result := fmt.Sprintf("[+] PocScan %s %s %s", task.Req.URL, task.Poc.Name, name)
 common.LogSuccess(result)
}
To:
isVul, _, name, extractedVars := executePoc(task.Req, task.Poc)
if isVul {
 result := fmt.Sprintf("[+] PocScan %s %s %s", task.Req.URL, task.Poc.Name, name)
 if len(extractedVars) > 0 {
     keys := make([]string, 0, len(extractedVars))
     for k := range extractedVars {
         keys = append(keys, k)
     }
     sort.Strings(keys)
     for _, k := range keys {
         result += fmt.Sprintf("\n    * %s: %s", k, extractedVars[k])
     }
 }
 common.LogSuccess(result)
}

Design Decisions

- Sort keys alphabetically: Go map iteration is non-deterministic; sorting ensures consistent, reproducible output.
- Single LogSuccess call: Builds the full multi-line string before calling LogSuccess to prevent interleaving from concurrent goroutines.
fmt.Println/color.Red in SaveLog handle multi-line strings correctly. WriteFile also works with multi-line strings (plain text appends result + "\n";
JSON output: Go's json.Marshal escapes embedded newlines).
- Exclude unnamed groups (k != ""): doSearch can return "" as a key for unnamed capture groups; these are internal and should not appear in output.
- set variables not in searchVars: set variables are added to variableMap directly (not through doSearch), so they can never enter searchVars.
- brute-force path unchanged: clusterpoc already has its own output with credentials in tmpMap.
- Groups mode returns searchVars: For consistency, the groups path also returns searchVars (line 193) so POCs using groups format also display extracted
variables.

Verification

Step 1: Create a test POC YAML

Create /Users/veno/Projects/fscan/WebScan/pocs/poc-yaml-test-search-extract.yml:

name: poc-yaml-test-search-extract
transport: http
rules:
- method: GET
 path: /
 expression: status == 200 && body.bcontains(b"fscan-test")
 search: 'token=(?P<token>[a-z0-9]+).*?user=(?P<username>[a-zA-Z]+)'

Step 2: Start a local test HTTP server

Use Python to serve a response containing the expected fields:

python3 -c "
import http.server, socketserver
class H(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
     body = b'fscan-test token=abc123def user=admin'
     self.send_response(200)
     self.end_headers()
     self.wfile.write(body)
 def log_message(self, *a): pass
with socketserver.TCPServer(('', 18080), H) as s:
 s.serve_forever()
" &

Step 3: Build and run

go build -o fscan main.go

./fscan -h 127.0.0.1:18080 -m webonly -pocname poc-yaml-test-search-extract

Expected output

[+] PocScan http://127.0.0.1:18080 poc-yaml-test-search-extract
 * token: abc123def
 * username: admin

Step 4: Cleanup

kill %1  # stop the python server
rm WebScan/pocs/poc-yaml-test-search-extract.yml
````

{{< /details >}}

vibe 完之后看上去效果合理了。

![实现效果](image.png)

过程中 claude 踩了两个坑，它不知道 fscan 的 yaml 会被编译进二进制，当成了 nuclei 类似的外置模板模式。以及 fscan POC 语法中 `expression` 必须用 `response.status` 和 `response.body`，而非裸的 `status/body`。一并将它补进 CLAUDE.md

> 提交，然后在 CLAUDE.md 修复上述错误示例。并且新增说明，fscan 的 poc 模板设计是，yaml 会被编译进二进制，因此写了新模板希望使用，需要重新编译。
> 在 CLAUDE.md 中新补充一点，本项目基于原版新增了我们刚刚实现的 POC YAML 中允许正则提取 exp 关键字的功能相关的描述。并给出语法。

最终 CLAUDE.md 如下：

{{< details summary="CLAUDE.md" >}}

````markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

fscan 是一个用 Go 语言编写的内网综合扫描工具。支持主机存活探测、端口扫描、服务爆破、漏洞检测（包括 MS17-010、SMB Ghost）、Web 指纹识别，以及基于 YAML 格式的 Web 漏洞扫描（兼容 xray POC 格式）。

## 构建和开发命令

### 构建

```bash
# 标准编译
go build -ldflags="-s -w" -trimpath main.go

# 可选：使用 UPX 压缩体积
upx -9 fscan.exe

# 跨平台编译示例
# Windows 64位
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -trimpath -o fscan_windows_amd64.exe main.go

# Linux 64位
GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -trimpath -o fscan_linux_amd64 main.go

# macOS 64位
GOOS=darwin GOARCH=amd64 go build -ldflags="-s -w" -trimpath -o fscan_darwin_amd64 main.go

# macOS ARM64 (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -ldflags="-s -w" -trimpath -o fscan_darwin_arm64 main.go
```

### 编译参数说明

fscan 使用标准 Go 编译工具链，支持以下编译优化：

**ldflags 参数**：

- `-s`：去除符号表（strip symbol table），减小二进制文件大小
- `-w`：去除 DWARF 调试信息（strip debug info），进一步减小文件大小
- 组合使用 `-ldflags="-s -w"` 可显著减小可执行文件体积（约减少 30-40%）

**trimpath 参数**：

- `-trimpath`：从生成的可执行文件中删除所有文件系统路径
- 提高二进制文件的可重现性和安全性（不泄露本地路径信息）

**构建约束（Build Tags）**：

- fscan 代码库未使用构建标签（build tags），所有功能在所有平台上统一编译
- 跨平台兼容性通过 Go 标准库的平台抽象实现（如 `runtime.GOOS`、`runtime.GOARCH`）
- ICMP 功能在不同平台上使用 `golang.org/x/net/icmp` 包实现跨平台支持
- 某些功能在特定平台上有限制（如 ICMP 需要管理员权限）

**嵌入式资源（Embed）**：

- WebScan 模块使用 `//go:embed pocs` 将 380+ 个 YAML POC 文件嵌入到二进制文件中
- 编译时会自动打包 `WebScan/pocs/` 目录下的所有文件
- 无需额外的资源文件即可分发单个可执行文件

### 常用编译命令组合

```bash
# 开发调试版本（保留调试信息）
go build -o fscan main.go

# 生产发布版本（体积优化）
go build -ldflags="-s -w" -trimpath -o fscan main.go

# 交叉编译所有主流平台
for GOOS in darwin linux windows; do
  for GOARCH in 386 amd64 arm64; do
    # 跳过不支持的组合
    if [ "$GOOS" = "darwin" ] && [ "$GOARCH" = "386" ]; then continue; fi

    output_name="fscan_${GOOS}_${GOARCH}"
    if [ "$GOOS" = "windows" ]; then
      output_name="${output_name}.exe"
    fi

    echo "Building $output_name..."
    GOOS=$GOOS GOARCH=$GOARCH go build -ldflags="-s -w" -trimpath -o $output_name main.go
  done
done

# 编译后使用 UPX 进一步压缩（可选）
upx -9 fscan_*
```

### 依赖管理

```bash
# 下载依赖
go mod download

# 整理依赖（移除未使用的依赖）
go mod tidy

# 验证依赖
go mod verify

# 查看依赖树
go mod graph
```

### 运行

```bash
# 基本扫描
go run main.go -h 192.168.1.1/24

# 指定模块
go run main.go -h 192.168.1.1/24 -m ssh

# 指定端口
go run main.go -h 192.168.1.1/24 -p 22,80,443
```

### 测试

该代码库不包含单元测试。测试通过针对目标环境的手动执行完成。

## 架构总览

### 主要执行流程

1. **输入解析** (`common` 包)：解析命令行参数、IP 范围、端口范围和配置
2. **主机发现** (`Plugins/icmp.go`)：ICMP ping 扫描识别存活主机（可用 `-np` 跳过）
3. **端口扫描** (`Plugins/portscan.go`)：对存活主机进行 TCP 端口扫描
4. **服务检测** (`Plugins/*`)：针对特定协议的扫描和密码爆破
5. **Web 扫描** (`WebScan` 包)：指纹识别和基于 POC 的漏洞检测
6. **输出结果** (`common/log.go`)：结果输出到控制台，可选保存到文件

### 包结构

- **`main.go`**：程序入口，初始化 HostInfo，解析参数，调用 Plugins.Scan()

- **`common/`**：共享配置和工具函数
  - `flag.go`：命令行参数定义
  - `config.go`：默认字典、端口列表和全局状态（版本号、用户字典、密码字典、端口列表）
  - `ParseIP.go`：IP 范围解析（支持 CIDR、范围格式如 192.168.1.1-255、逗号分隔）
  - `ParsePort.go`：端口范围解析
  - `log.go`：带颜色输出的日志记录
  - `proxy.go`：HTTP/SOCKS5 代理配置

- **`Plugins/`**：服务特定的扫描模块
  - `scanner.go`：主调度器，将主机/端口路由到相应的插件
  - `portscan.go`：TCP 端口扫描器
  - `icmp.go`：ICMP ping 扫描用于主机发现
  - `base.go`：PluginList 映射表，注册端口号到扫描函数（如 "22" -> SshScan）
  - 服务扫描器：`ssh.go`、`smb.go`、`mysql.go`、`redis.go`、`ftp.go`、`mssql.go`、`postgres.go`、`oracle.go`、`rdp.go`、`mongodb.go`、`memcached.go`
  - 漏洞利用模块：`ms17010.go`、`ms17010-exp.go`、`CVE-2020-0796.go`（SMB Ghost）
  - `NetBIOS.go`：NetBIOS 枚举和域控识别
  - `webtitle.go`：HTTP 标题抓取和基础 Web 指纹识别
  - `fcgiscan.go`：FastCGI 协议扫描

- **`WebScan/`**：Web 漏洞扫描
  - `WebScan.go`：主入口，从嵌入式文件系统或自定义路径加载 POC
  - `InfoScan.go`：指纹检测
  - `lib/`：POC 引擎实现
    - `check.go`：指纹匹配和 POC 过滤
    - `eval.go`：CEL（通用表达式语言）表达式求值，用于 POC 规则
    - `client.go`：支持代理的 HTTP 客户端
    - `http.pb.go`：HTTP 请求/响应的 Protobuf 定义
  - `pocs/`：包含 380+ 个 YAML POC 文件的目录（使用 `//go:embed` 在编译时嵌入）

### 插件注册系统

插件在 `Plugins/base.go` 中通过 `PluginList` 映射表注册：

```go
var PluginList = map[string]interface{}{
    "22":      SshScan,
    "3306":    MysqlScan,
    "1000001": MS17010,     // 漏洞利用的特殊端口号
    "1000003": WebTitle,    // Web 扫描
    // ...
}
```

扫描器使用反射根据检测到的端口动态调用相应的函数。

### 并发模型

- 主协程池由 `-t` 参数控制（默认：600 个线程）
- `scanner.go` 中的 AddScan 函数使用基于 channel 的信号量限制并发扫描
- 每个服务扫描在自己的 goroutine 中运行
- WaitGroups 确保所有扫描在程序退出前完成
- Mutex 保护共享计数器（common.Num、common.End）

### 重要扫描模式（`-m` 参数）

- `all`（默认）：运行所有模块（ICMP → 端口扫描 → 服务扫描 → Web 扫描）
- `portscan`：仅执行端口扫描
- `icmp`：仅执行主机发现
- `webonly`：跳过端口扫描，直接探测常见 Web 端口的 HTTP/HTTPS
- `ssh`、`mysql`、`redis` 等：针对特定服务
- `ms17010`：扫描 MS17-010 漏洞

### 端口组

`common/config.go` 中的 `PortGroup` 映射定义了预设端口集：

- `main`：常用端口（21,22,80,81,135,139,443,445,1433,1521,3306,5432,6379,7001,8000,8080,8089,9000,9200,11211,27017）
- `db`：数据库端口
- `web`：Web 端口的扩展列表（80、8080、8443 等）
- `service`：常见服务端口

### Web POC 系统

- POC 是兼容 xray 格式的 YAML 文件
- 从嵌入式文件系统（`WebScan/pocs/`）或自定义路径（`-pocpath`）加载
- 使用 CEL 表达式进行匹配和提取
- 支持基于指纹的 POC 选择（仅根据检测到的 CMS/框架运行相关 POC）
- 通过 `-num` 参数限速（默认：20 个并发 POC 检查）

### WebScan 模块架构

WebScan 负责 Web 漏洞扫描，采用 CEL 表达式引擎和模块化设计。

#### 核心组件

- **WebScan.go**：主入口，从 `//go:embed pocs` 或 `-pocpath` 加载 POC，根据指纹过滤并并发执行
- **InfoScan.go**：指纹识别，包含 260+ 条规则（WAF、OA、中间件、CMS），支持 body/headers/cookie 正则匹配
- **lib/check.go**：POC 执行引擎
  - 普通模式：按顺序执行 rules
  - 爆破模式：使用 `sets` 字典生成笛卡尔积（如 Tomcat 弱口令、Shiro key）
  - 支持变量替换 `{{variable}}`、命名捕获组 `(?P<name>...)`、MD5 去重
- **lib/eval.go**：CEL 表达式引擎，30+ 自定义函数
  - 字符串：`bcontains`、`icontains`、`substr`、`startsWith`
  - 编码：`base64`、`urlencode`、`hexdecode`
  - 特殊：`shirokey`、`TDdate`（通达 OA）、`wait`（DNSLog）
- **lib/client.go**：HTTP 客户端，TLS 1.0+，支持 HTTP/SOCKS5 代理，连接池配置
- **info/rules.go**：指纹规则库和 POC 映射表（指纹 -> POC 别名）

#### 工作流程

1. 指纹识别：正则匹配 headers 和 body
2. POC 过滤：根据指纹查询 `PocDatas`，过滤相关 POC
3. 并发执行：worker 池（`-num` 控制）执行 POC，评估 CEL 表达式
4. 结果输出：`[+] PocScan <URL> <POC名称>` 及 `search` 提取的命名变量（每行 `    * key: value`）

#### POC YAML 格式

```yaml
name: poc-yaml-example
set:
  - key: var
    value: "value"
sets:  # 爆破字典（可选）
  - key: user
    value: ["admin", "root"]
rules:
  - method: POST
    path: /api/login
    body: '{"user":"{{user}}"}'
    search: '"token":"(?P<token>.*?)"'  # 命名捕获组
    expression: response.status == 200 && response.body.bcontains(b'success')
```

#### search 字段：正则提取并展示关键变量（本项目扩展）

原版 xray 格式的 `search` 字段仅用于提取命名捕获组并注入到后续 rule 的变量替换中。本项目在此基础上扩展：**所有命名捕获组的值会在 POC 命中时一并打印到输出**，适用于提取 accessToken、凭据、版本号等敏感信息。

**语法**：在任意 rule 中添加 `search` 字段，使用 Python 风格的命名捕获组 `(?P<name>...)`：

```yaml
name: poc-yaml-example-with-extraction
transport: http
rules:
  - method: POST
    path: /api/auth
    body: '{"username":"admin","password":"admin"}'
    search: '"accessToken":"(?P<accessToken>[^"]+)".*?"username":"(?P<username>[^"]+)"'
    expression: response.status == 200 && response.body.bcontains(b'accessToken')
```

命中时输出格式：

```
[+] PocScan http://10.0.0.1:8848 poc-yaml-example-with-extraction
    * accessToken: eyJhbGc...
    * username: nacos
```

**说明**：
- `search` 匹配范围为 `响应头 + 响应体` 的拼接字符串
- 多个 rule 中的 `search` 均会被收集，后续 rule 提取的变量会覆盖同名变量
- 提取的变量同时注入 `variableMap`，可在后续 rule 中通过 `{{varName}}` 引用
- key 按字母序排列输出，空 key（未命名组）自动忽略
- 实现位置：`WebScan/lib/check.go`，函数 `executePoc` 和 `CheckMultiPoc`

#### 特殊机制

- Shiro POC 默认测试 10 个 key（`-full` 测试 100 个），位置：lib/check.go:283
- DNSLog 支持使用 ceye.io，需 `-dns` 参数
- 基于指纹的智能过滤减少无效请求

## 常见开发模式

### 添加新的服务插件

1. 创建 `Plugins/newservice.go`，函数签名为：`func NewServiceScan(info *common.HostInfo)`
2. 在 `Plugins/base.go` 的 PluginList 中注册：`"PORT": NewServiceScan`
3. 在 `common/config.go` 的 PORTList 和 PortGroup 中添加默认端口
4. 如适用，在 `Userdict` 中添加默认凭据

### 添加新的 POC

在 `WebScan/pocs/` 目录中放置 YAML 文件。示例结构：

```yaml
name: poc-name
transport: http
rules:
  - method: GET
    path: /vulnerable/path
    expression: response.status == 200 && response.body.bcontains(b'marker')
```

> **注意**：POC YAML 文件通过 `//go:embed pocs` 在**编译期**嵌入二进制。新增或修改 POC 后，必须重新编译才能生效：
>
> ```bash
> go build -ldflags="-s -w" -trimpath -o fscan main.go
> ```
>
> 如需在不重新编译的情况下临时加载外部 POC，可使用 `-pocpath <目录>` 参数从文件系统加载。

### 错误处理

- 大多数函数使用 `defer recover()` 捕获 panic
- 通过 `common.LogError()` 和 `common.LogSuccess()` 记录错误
- 静默模式（`-silent`）抑制实时输出，用于自动化工具

## 关键全局变量

- `common.Threads`：并发扫描线程数
- `common.Timeout`：TCP 连接超时（默认：3秒）
- `common.WebTimeout`：HTTP 请求超时（默认：5秒）
- `common.NoPing`：跳过 ICMP 主机发现
- `common.NoPoc`：跳过 Web 漏洞扫描
- `common.IsBrute`：跳过密码爆破

## 值得注意的实现细节

- **IP 解析**：支持 /8 范围的智能采样（扫描每个 C 段的 .1 和 .254，加上随机 IP）
- **ICMP 实现**：使用原始套接字和自定义 ICMP 数据包构造（在 Linux/Windows 上需要 root/管理员权限）
- **密码爆破**：默认串行；使用 `-br N` 进行并发尝试（注意账户锁定）
- **MS17-010 利用**：内置 shellcode 生成用于添加用户（`-sc add`），但 README 推荐使用专用工具
- **代理支持**：HTTP 代理（`-proxy`）用于 Web 扫描；SOCKS5（`-socks5`）用于 TCP 连接（并非所有模块都支持）
- **哈希认证**：支持 SMB 的 pass-the-hash（`-hash`）和 WMI 执行

## 安全和授权上下文

此工具专为经授权的渗透测试和安全评估而设计。README 包含了全面的免责声明，要求在使用前获得合法授权。修改漏洞利用模块（ms17010-exp.go 等）时，请确保更改符合道德使用约束。

````

{{</details>}}

### 通过参数保存 http 请求包和响应包

这里的功能感觉不是很复杂，并且架构相关内容已经被 Claude Sonnet 4.6 理清楚了，换了个便宜且快的模型 MiniMax-M2.5 ~~(其实是 Claude 用到限流了)~~。因为只有 10B，平时用起来响应真的快。

先检查了一下文档，发现似乎好像有一些关于输出系统的描述。如果已经有这个功能的话，就不要重复实现了，记录一下怎么用就行。让 M2.5 帮我先查一下。

> 检查 <https://fscan.club/#/docs> 和 fscan --help 中关于输出系统的描述，确认其中将 http
请求响应包保存为文件的描述。如果不存在此功能，请参考分类输出，使用类似的参数风格，新增命令行参数，允许用户保存 poc 触发时所使用的 http 请求响应，注意并不是保存所有扫描的 http 请求响应。之后启动一个 python 服务，编写测试用 poc-yaml，测试该参数。在一切确认完成之后，在 CLAUDE.md 中精简描述新增的这一功能。

{{< details summary="POC 请求响应保存功能实现计划" >}}

````markdown
POC 请求响应保存功能实现计划

背景

用户希望在 fscan 中新增功能：当 POC 扫描命中漏洞时，能够保存触发漏洞所使用的 HTTP 请求和响应到本地文件。

经检查：
- https://fscan.club/#/docs 网站无有用内容
- fscan --help 中无此功能描述
- 当前 fscan 版本（1.8.4）不支持保存 HTTP 请求响应

实现方案

1. 新增命令行参数

参考现有参数风格（单破折号 - 前缀），新增：

// common/flag.go 第70行附近
flag.StringVar(&PocSavePath, "hs", "", "save poc http request and response to file when poc hits")

参数说明：
- -hs: http save，指定保存目录路径（当 POC 命中时自动创建文件）

2. 定义全局变量

// common/config.go 第134行附近
var PocSavePath string  // 保存目录路径

3. 核心实现

3.1 修改 executePoc 函数签名

在 WebScan/lib/check.go 中，修改 executePoc 函数返回额外信息：

// 修改前
func executePoc(oReq *http.Request, p *Poc) (bool, error, string, map[string]string)

// 修改后
func executePoc(oReq *http.Request, p *Poc) (bool, error, string, map[string]string, *http.Request, *Response)

返回的两个额外值为：
- *http.Request: 最后执行的请求（用于保存）
- *Response: 最后执行的响应（用于保存）

3.2 修改 CheckMultiPoc 函数

在 CheckMultiPoc 函数（第29-64行）中：
1. 接收返回的 request 和 response
2. 当 isVul 为 true 且 PocSavePath 不为空时，保存请求响应

3.3 保存函数实现

创建保存函数 savePocHttpInfo：

func savePocHttpInfo(req *http.Request, resp *Response, pocName, savePath string) error {
 // 1. 创建目录（如果不存在）
 os.MkdirAll(savePath, 0755)

 // 2. 生成文件名
 urlHash := md5.Sum([]byte(req.URL.String()))
 timestamp := time.Now().Unix()
 filename := fmt.Sprintf("%s_%x_%d.txt", pocName, urlHash, timestamp)
 filepath := filepath.Join(savePath, filename)

 // 3. 格式化请求响应内容
 var content strings.Builder
 content.WriteString("============== Request ==============\n")
 content.WriteString(fmt.Sprintf("%s %s HTTP/1.1\n", req.Method, req.URL.RequestURI()))
 content.WriteString(fmt.Sprintf("Host: %s\n", req.Host))
 for k, v := range req.Header {
     content.WriteString(fmt.Sprintf("%s: %s\n", k, strings.Join(v, ", ")))
 }
 if req.Body != nil {
     body, _ := io.ReadAll(req.Body)
     content.WriteString("\n")
     content.WriteString(string(body))
 }

 content.WriteString("\n\n============== Response ==============\n")
 content.WriteString(fmt.Sprintf("HTTP/1.1 %d %s\n", resp.Status, http.StatusText(resp.Status)))
 for k, v := range resp.Headers {
     content.WriteString(fmt.Sprintf("%s: %s\n", k, v))
 }
 content.WriteString("\n")
 content.WriteString(string(resp.Body))

 // 4. 写入文件
 return os.WriteFile(filepath, []byte(content.String()), 0644)
}

4. 文件命名策略

为避免文件名冲突和覆盖，使用：
{poc_name}_{md5(url)}_{timestamp}.txt

例如：poc-weblogic_1a2b3c4d_1709000000.txt

5. 关键代码位置

┌──────────────────────┬────────┬───────────────────────────────────────┐
│         文件         │  行号  │               修改内容                │
├──────────────────────┼────────┼───────────────────────────────────────┤
│ common/flag.go       │ ~70    │ 添加 -hs 参数定义                     │
├──────────────────────┼────────┼───────────────────────────────────────┤
│ common/config.go     │ ~134   │ 添加 PocSavePath 变量                 │
├──────────────────────┼────────┼───────────────────────────────────────┤
│ WebScan/lib/check.go │ ~66    │ 修改 executePoc 函数签名和返回        │
├──────────────────────┼────────┼───────────────────────────────────────┤
│ WebScan/lib/check.go │ ~29-64 │ 修改 CheckMultiPoc 函数调用和保存逻辑 │
├──────────────────────┼────────┼───────────────────────────────────────┤
│ WebScan/lib/check.go │ 新增   │ 添加 savePocHttpInfo 函数             │
└──────────────────────┴────────┴───────────────────────────────────────┘

6. 依赖

需要添加以下 import：
import (
 "crypto/md5"
 "path/filepath"
 "time"
)

测试计划

6.1 启动 Python HTTP 测试服务

# 创建简单的 Python HTTP 服务
python3 -m http.server 8080

6.2 编写测试 POC YAML

在 WebScan/pocs/ 或使用 -pocpath 指定目录，创建测试 POC：

name: poc-test-save-http
set:
- key: test
 value: "test"
rules:
- method: GET
 path: /test
 expression: response.status == 200 && response.body.bcontains(b"test")

6.3 运行测试

fscan -hs ./poc-output -u http://localhost:8080 -pocname poc-test-save-http

6.4 验证

1. 检查 ./poc-output 目录是否生成文件
2. 验证文件内容包含完整的请求和响应

CLAUDE.md 更新

在 CLAUDE.md 的 "Web POC 系统" 部分添加：

#### POC 请求响应保存

当 POC 命中时，可使用 `-hs <目录>` 参数保存触发漏洞的 HTTP 请求和响应：

```bash
fscan -hs ./poc-output -u http://target.com -pocname weLOGIC
```

命中后会在指定目录生成 {poc_name}_{url_hash}_{timestamp}.txt 文件，包含完整的请求头/请求体和响应头/响应体。
````

{{< /details >}}

M2.5 完美完成任务，可以用这样的指令

```bash
./fscan -hs ./poc-output -u http://target.com -pocname poc-yaml-name
```

效果如图：

![请求响应包格式](image-1.png)
