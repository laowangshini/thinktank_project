# webui/templatetags/custom_filters.py
from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def nl2br(text):
    """将换行符转换为HTML换行标签"""
    if not text:
        return ''
    return mark_safe(text.replace('\n', '<br>'))

@register.filter
def highlight_search(text, query):
    """高亮搜索关键词"""
    if not query or not text:
        return text
    # 注意：mark_safe 会使内容不被转义，确保 query 是安全的或已转义
    escaped_query = re.escape(query)
    pattern = re.compile(escaped_query, re.IGNORECASE)
    highlighted = pattern.sub(f'<span class="highlight">{query}</span>', text)
    return mark_safe(highlighted) # 标记为安全 HTML

@register.filter
def floatratio(value, arg):
    """计算 value / arg 的比率，返回浮点数。处理除零和类型错误。"""
    try:
        v = float(value)
        a = float(arg)
        if a == 0:
            return 0 # 或者返回 None，或者返回一个特殊值
        return v / a
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def splitlines(text):
    """将文本按换行符分割成列表"""
    if not text:
        return []
    return text.splitlines() # Python 内置方法

@register.filter
def count_non_empty_lines(text):
    """统计文本中非空行的数量"""
    if not text:
        return 0
    # 使用列表推导式和 strip() 过滤空行
    return len([line for line in text.splitlines() if line.strip()])

# 如果需要在模板中进行字符串替换
# @register.filter
# def replace(text, args):
#     """替换文本中的子串。args 应该是 "old,new" 的格式"""
#     if not text or not args:
#         return text
#     parts = args.split(',', 1) # 只分割一次，防止 new 中有逗号
#     if len(parts) != 2:
#         return text
#     old, new = parts
#     return text.replace(old, new)

# 如果需要在模板中进行数学运算
# @register.filter
# def mul(value, arg):
#     """Multiply the value by the argument."""
#     try:
#         return float(value) * float(arg)
#     except (ValueError, TypeError):
#         return 0