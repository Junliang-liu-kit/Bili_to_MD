# Bili_to_MD - B站收藏夹同步工具

Bili_to_MD 是一个基于 Python 的 Bilibili 自动化工具包，专注于将 B 站收藏夹信息同步为本地 Markdown 文件。项目提供了完整的收藏夹管理工作流，支持增量同步、视频信息获取和本地化存储。

## 🚀 功能特性

- ✅ **收藏夹同步**: 将 B 站收藏夹批量导出为 Markdown 文件
- ✅ **增量同步**: 智能识别已同步视频，仅同步新增内容
- ✅ **视频信息获取**: 批量获取视频详细信息，包括标题、UP主、发布时间等
- ✅ **配置化管理**: 通过配置文件管理收藏夹 ID、Cookie 路径等参数
- ✅ **跨平台支持**: 支持 Windows、macOS、Linux 系统
- ✅ **模块化架构**: 独立的功能模块，便于维护和扩展

## 📦 安装配置

### 环境要求

- Python 3.12+
- uv (推荐) 或 pip

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/Junliang-liu-kit/Bili_to_MD.git
cd Bili_to_MD
```

2. **使用 uv 环境配置 (推荐)**
```bash
# 安装 uv：关于uv的安装和使用可以参考https://www.zhihu.com/people/li-xing-yu-zi-lu/posts或其他文章

# 创建并激活虚拟环境
uv venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -e .
```

3. **使用 pip 安装**
```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -e .
# 或使用 requirements.txt
pip install -r requirements.txt
```

## 🔧 使用说明

### 1. Cookie 的获取与使用方法
- 方法1(推荐): 使用扫码登录生成 cookie 文件
```bash
python src/cookie_get.py
```

- 方法2: 
1. 在浏览器中登录 Bilibili
2. 按 F12 打开开发者工具
3. 刷新页面，在网络请求中找到包含 SESSDATA 和 bili_jct 的请求
4. 复制 Cookie 内容
5. 在项目根目录创建 `cookie` 文件夹
6. 创建 `cookie/qr_login.txt` 文件
7. 将复制的 Cookie 内容粘贴到文件中

### 2. MediaID 的获取与使用方法

**获取 MediaID**:
1. 打开目标收藏夹页面
2. 在 URL 中找到 `fid=` 后面的数字，例如：`https://www.bilibili.com/medialist/detail/ml1234567890` 中的 `1234567890`
3. 或在收藏夹页面右键检查元素，查找 `media_id` 相关信息

**配置 MediaID**:
- 编辑 `config/dev.ini` 文件
- 修改 `MEDIA_ID` 的值为你收藏夹的 ID

### 3. 本地文件同步路径的查看与修改方式

**默认路径**: `output/markdown`

**修改路径**:
1. 编辑 `config/dev.ini` 文件
2. 修改 `OUTPUT_DIR` 参数为你想要的输出路径
3. 可以使用相对路径或绝对路径

## 📁 项目介绍

### 1. 核心参数

程序会从 `config/dev.ini` 文件加载以下参数：

- `MEDIA_ID`: 收藏夹ID，用于指定要同步的目标收藏夹
- `COOKIE_PATH`: cookie文件路径（可选），未指定时使用默认路径 `cookie/qr_login.txt`
- `OUTPUT_DIR`: 输出目录路径，默认为 `output/markdown`

**配置文件示例**:
```ini
[Sync Parameters]
MEDIA_ID = "123456"
COOKIE_PATH =
OUTPUT_DIR = "output/markdown"
```

### 2. 代码架构，主要模块功能说明

**核心架构**:
```
Bili_to_MD/
├── main.py                 # 主程序入口，完整同步工作流
├── config/
    └── dev.ini             # 配置文件
├── src/
│   ├── get_favorite.py     # 收藏夹信息获取模块
│   ├── get_bv_info.py      # 视频详细信息获取模块
│   ├── data_sync.py        # 数据同步和Markdown转换模块
    ├── cookie_get.py       # Cookie管理工具
    └── Tools/                  # 底层工具库
        ├── bili_tools.py       # Bilibili API 封装
        └── util/               # 工具函数
```

**主要模块功能**:

- **main.py**: 主入口文件，协调各个模块完成完整的收藏夹同步流程
  - 加载配置参数
  - 执行6步同步工作流
  - 提供进度反馈和错误处理

- **get_favorite.py**: 收藏夹信息获取
  - 调用 Bilibili API 获取收藏夹中的视频列表
  - 支持 Cookie 认证
  - 提供命令行接口

- **get_bv_info.py**: 视频详细信息获取
  - 批量获取视频的详细信息
  - 包含标题、UP主、发布时间、简介等
  - 支持延时避免请求过频

- **data_sync.py**: 数据同步管理
  - 实现增量同步机制
  - 将视频信息转换为 Markdown 格式
  - 管理同步记录，避免重复同步

- **cookie_get.py**: Cookie 管理工具
  - 支持扫码登录获取 Cookie
  - 管理 Cookie 文件的创建和更新

### 3. 启动文件说明

**主启动方式**:
```bash
# 使用主程序（推荐）
python main.py

# 使用 uv
uv run main.py
```

**example_start.bat** 为样例启动文件，可根据个人实际需求自行修改配置：
- 自动切换到项目目录
- 激活虚拟环境
- 运行主程序
- 提供错误处理和用户友好的提示信息

## 🔄 同步流程

程序执行6步同步工作流：

1. **获取收藏夹视频列表**: 从 Bilibili API 获取收藏夹中的所有视频
2. **检查历史同步记录**: 读取本地的同步记录文件
3. **筛选待同步视频**: 对比当前列表和历史记录，筛选出需要同步的视频
4. **批量获取视频信息**: 获取视频的详细信息和元数据
5. **保存为Markdown文件**: 将视频信息转换为 Markdown 格式并保存到本地
6. **更新同步记录**: 更新同步记录，标记本次同步的视频

## 📝 输出格式

每个视频会生成一个 Markdown 文件，包含以下信息：

- **BV号和链接**: 视频的唯一标识符
- **标题**: 视频完整标题
- **UP主**: 视频创作者信息
- **发布时间**: 视频发布时间
- **视频简介**: 视频描述信息
- **获取时间**: 同步操作的时间戳
- **其他元数据**: 时长、播放量、点赞数等

## 🔧 故障排除

**常见问题**:

1. **获取收藏夹信息失败**
   - 检查网络连接
   - 确认 Cookie 文件是否存在且有效
   - 验证 MediaID 是否正确

2. **Cookie 过期**
   - 重新运行 `python src/cookie_get.py` 获取新 Cookie
   - 或手动更新 `cookie/qr_login.txt` 文件

3. **路径权限错误**
   - 确认输出目录有写入权限
   - 使用绝对路径避免相对路径问题

## 致谢
本项目部分代码基于以下项目开发：
- [virtualxiaoman/BiliTools: B站小工具[视频下载、评论、私信、扫码登录、收藏夹导出......]](https://github.com/virtualxiaoman/BiliTools)

开发过程中参考的相关案例：
- [ayasa520/bilibili-favorites-exporter: 用于导出并本地展示 B 站收藏夹](https://github.com/ayasa520/bilibili-favorites-exporter)
- [快速导出B站收藏单节目列表 - 鱼肉真好吃 - 博客园](https://www.cnblogs.com/toumingbai/p/11399238.html)

## 📄 许可证

本项目遵循原项目的许可证条款。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目！

## ⭐ 更新日志

- v0.1.0: 初始版本，支持基本的收藏夹同步功能
- 支持增量同步机制
- 添加配置文件管理
- 优化错误处理和用户体验