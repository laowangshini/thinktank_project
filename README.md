# 智库内容管理系统

一个基于 Django 5.2.4 的智库内容爬取和管理系统，支持多个智库网站的自动化内容抓取、展示和摘编。

## 🚀 快速部署

### 环境要求

- Python 3.10+
- SQLite 或 PostgreSQL/MySQL
- Chrome 浏览器（用于爬虫）

### 部署步骤

#### 1. 克隆项目并安装依赖

```bash
# 进入项目目录
cd thinktank_project

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置数据库

```bash
# 运行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 初始化智库数据
python manage.py init_thinktanks
```

#### 3. 收集静态文件（生产环境）

```bash
python manage.py collectstatic --noinput
```

#### 4. 启动服务

**开发环境：**
```bash
python manage.py runserver 0.0.0.0:8000
```

**生产环境（使用 Gunicorn）：**
```bash
gunicorn thinktank_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

#### 5. 访问系统

浏览器打开: `http://your-server-ip:8000/`

---

## 📋 功能模块

- **文章管理** - 自动爬取和展示智库文章
- **智库管理** - 管理智库信息和爬取任务
- **文章摘编** - 人工摘编和批量处理
- **任务调度** - 定时爬取任务管理
- **搜索功能** - 全文搜索文章内容

---

## 🌐 访问地址

- **首页**: http://your-server:8000/
- **文章列表**: http://your-server:8000/articles/
- **智库列表**: http://your-server:8000/thinktanks/
- **任务管理**: http://your-server:8000/tasks/
- **搜索**: http://your-server:8000/search/

---

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

# 初始化智库和任务数据
python manage.py init_thinktanks

# 创建超级管理员
python manage.py createsuperuser
```

---

## 🔧 生产环境配置

### 1. 修改 settings.py

```python
# thinktank_project/settings.py

# 关闭 DEBUG
DEBUG = False

# 设置允许的主机
ALLOWED_HOSTS = ['your-domain.com', 'your-server-ip']

# 配置静态文件
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# 使用 WhiteNoise 处理静态文件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 添加这一行
    # ... 其他中间件
]

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True  # 如果使用 HTTPS
CSRF_COOKIE_SECURE = True     # 如果使用 HTTPS
```

### 2. 使用 Nginx 反向代理（推荐）

创建 `/etc/nginx/sites-available/thinktank` 配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/thinktank_project/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/thinktank /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. 使用 Systemd 服务（Linux）

创建 `/etc/systemd/system/thinktank.service`：

```ini
[Unit]
Description=Thinktank Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/thinktank_project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    thinktank_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start thinktank
sudo systemctl enable thinktank
```

---

## 📝 支持的智库

1. 中国国际工程咨询有限公司
2. 中国人民大学国家发展与战略研究院
3. 国务院发展研究中心
4. 中国科学院
5. 中国宏观经济研究院
6. CCiD赛迪研究院
7. 上海社会科学院

---

## 🗑️ 可删除的文件夹

以下文件夹是旧版本或开发用的，部署时可以删除：

- `core/` - Flask旧代码
- `proj released/` - 旧版爬虫脚本
- `.ipynb_checkpoints/` - Jupyter笔记本缓存

---

## 🔒 安全建议

1. 修改 `settings.py` 中的 `SECRET_KEY`
2. 在生产环境关闭 `DEBUG = False`
3. 使用环境变量管理敏感信息
4. 配置 HTTPS
5. 定期更新依赖包
6. 配置防火墙规则

---

## 📊 性能优化

1. 使用 Redis 做缓存
2. 配置数据库连接池
3. 使用 CDN 加速静态文件
4. 启用 Gzip 压缩
5. 配置合适的 Gunicorn workers 数量

---

## 🐛 故障排除

### 静态文件加载失败

```bash
python manage.py collectstatic --clear
python manage.py collectstatic --noinput
```

### 数据库连接错误

检查 `settings.py` 中的数据库配置

### 爬虫无法启动

确保服务器已安装 Chrome 浏览器和对应的 ChromeDriver

---

## 📞 技术支持

如有问题，请检查：
1. Python 版本 >= 3.10
2. 所有依赖已正确安装
3. 数据库已正确配置
4. 防火墙端口已开放

---

**祝部署顺利！** 🎉
