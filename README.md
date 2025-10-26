# 智库内容管理系统 🏛️

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.2.4-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 Django 5.2.4 的智库内容爬取和管理系统，支持多个智库网站的自动化内容抓取、展示和摘编。

## ✨ 功能特点

- 🔍 **智能爬虫** - 自动爬取多个智库网站的最新内容
- 📰 **内容管理** - 文章展示、搜索、筛选和分类
- ✏️ **内容摘编** - 支持人工摘编和批量处理
- ⏰ **任务调度** - 定时自动执行爬取任务
- 🎨 **现代化UI** - 响应式Web界面，支持移动端访问
- 🔐 **用户管理** - 多角色权限管理系统

## 🎯 支持的智库

- 中国国际工程咨询有限公司
- 中国人民大学国家发展与战略研究院
- 国务院发展研究中心
- 中国科学院
- 中国宏观经济研究院
- CCiD赛迪研究院
- 上海社会科学院

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Chrome 浏览器（用于爬虫）
- 2GB+ RAM
- 10GB+ 可用磁盘空间

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/你的用户名/thinktank_project.git
cd thinktank_project
```

2. **创建虚拟环境**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **初始化数据库**

```bash
python manage.py migrate
python manage.py init_thinktanks
```

5. **启动服务**

```bash
python manage.py runserver
```

6. **访问系统**

打开浏览器访问: http://127.0.0.1:8000/

## 📖 详细文档

- [部署指南](部署指南.md) - 生产环境部署说明
- [API文档](docs/API.md) - 接口文档（待完善）
- [开发指南](docs/DEVELOPMENT.md) - 开发者文档（待完善）

## 🌐 主要页面

| 页面 | 路径 | 说明 |
|------|------|------|
| 首页 | `/` | 系统概览和最新文章 |
| 文章列表 | `/articles/` | 所有文章的浏览和筛选 |
| 智库管理 | `/thinktanks/` | 智库信息和统计 |
| 任务管理 | `/tasks/` | 爬虫任务配置和执行 |
| 搜索 | `/search/` | 全文搜索功能 |

## 💻 管理命令

### 爬虫相关

```bash
# 运行所有激活的爬虫任务
python manage.py crawl_thinktanks --all

# 运行指定ID的任务
python manage.py crawl_thinktanks --task-id 1
```

### 数据库相关

```bash
# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 初始化智库数据
python manage.py init_thinktanks

# 创建超级管理员
python manage.py createsuperuser
```

## 🏗️ 项目结构

```
thinktank_project/
├── manage.py                 # Django 管理脚本
├── requirements.txt          # Python 依赖
├── README.md                # 项目说明
├── 部署指南.md               # 部署文档
├── .gitignore               # Git 忽略配置
│
├── thinktank_project/       # Django 项目配置
│   ├── settings.py          # 项目设置
│   ├── urls.py              # URL 路由
│   └── wsgi.py              # WSGI 配置
│
├── webui/                   # Web 界面
│   ├── views.py             # 视图函数
│   ├── urls.py              # URL 配置
│   └── templates/           # 模板文件
│
├── articles/                # 文章管理模块
│   ├── models.py            # 数据模型
│   ├── views.py             # 视图逻辑
│   └── management/          # 管理命令
│
├── thinktanks/             # 智库管理模块
│   ├── models.py            # 智库模型
│   └── management/          # 初始化命令
│
├── crawlers/               # 爬虫模块
│   ├── models.py            # 任务模型
│   ├── management/          # 爬虫命令
│   └── utils/               # 爬虫工具
│
└── users/                  # 用户管理模块
    ├── models.py            # 用户模型
    └── admin.py             # 管理界面
```

## 🔧 生产环境部署

详细的生产环境部署步骤请参考 [部署指南.md](部署指南.md)

### 快速部署（Ubuntu/Debian）

```bash
# 安装依赖
sudo apt update
sudo apt install python3-pip python3-venv nginx

# 配置项目
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置数据库
python manage.py migrate
python manage.py collectstatic --noinput

# 使用 Gunicorn 运行
pip install gunicorn
gunicorn thinktank_project.wsgi:application --bind 0.0.0.0:8000
```

## 🔒 安全配置

在生产环境中，请务必：

1. 修改 `settings.py` 中的 `SECRET_KEY`
2. 设置 `DEBUG = False`
3. 配置 `ALLOWED_HOSTS`
4. 使用 HTTPS
5. 配置防火墙
6. 定期更新依赖

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 开发计划

- [ ] 添加更多智库支持
- [ ] 实现文章自动分类
- [ ] 添加数据可视化功能
- [ ] 支持 PDF 导出
- [ ] 添加 API 接口
- [ ] 实现定时任务管理
- [ ] 添加邮件通知功能

## 🐛 已知问题

- Windows 下爬虫可能需要手动配置 ChromeDriver 路径
- 大量数据时建议使用 PostgreSQL 替代 SQLite

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Django](https://www.djangoproject.com/) - Web 框架
- [Selenium](https://www.selenium.dev/) - 浏览器自动化
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析

## 📧 联系方式

如有问题或建议，欢迎：

- 提交 [Issue](https://github.com/laowangshini/thinktank_project/issues)
- 发送邮件至: 320220942091@lzu.edu.cn
- 
## 写给开发人员

没错！你的云服务器每次重启，由于 CentOS 的环境变量不会自动生效，必须**手动设置环境变量、激活虚拟环境并启动 gunicorn**，否则会出现 sqlite3 version/动态库混用问题导致 Django 启动失败。

***

### 重启后项目手动启动流程指导

只需每次进入服务器后按如下5步操作：

1. **登录到你的 ECS 服务器（通过 SSH 或云控制台）**
   ```bash
   ssh root@你的公网IP
   ```

2. **设置 Python/SQLite 环境变量（务必每次重新设置！）**
   ```bash
   export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
   export CPPFLAGS="-I/usr/local/include"
   export LDFLAGS="-L/usr/local/lib"
   ```

3. **进入项目目录并激活虚拟环境**
   ```bash
   cd /opt/thinktank_project
   source venv39/bin/activate
   ```

4. **确认 gunicorn 没有残留进程，占用 8000 端口，如有则清理**
   ```bash
   pkill gunicorn
   ```

5. **后台启动 gunicorn 项目服务**
   ```bash
   nohup gunicorn thinktank_project.wsgi:application --bind 0.0.0.0:8000 --workers 4 &
   ```

6. **检查并启动/重载 Nginx 服务（如自动启动可略过）**
   ```bash
   systemctl start nginx
   nginx -s reload
   ```

***

---

⭐ 如果这个项目对你有帮助，请给个 Star！
