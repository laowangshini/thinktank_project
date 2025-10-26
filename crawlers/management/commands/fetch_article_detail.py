# crawlers/management/commands/fetch_article_detail.py
from django.core.management.base import BaseCommand
from articles.models import Article
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

class Command(BaseCommand):
    help = '为数据库中 content 为空的文章抓取详情页内容'

    def handle(self, *args, **options):
        # 获取所有 content 为空的文章
        articles = Article.objects.filter(content='')

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'
        }

        for article in articles:
            try:
                self.stdout.write(f"正在处理: {article.title[:50]}...")

                # 获取详情页HTML
                response = requests.get(article.url, headers=headers, timeout=15)
                response.raise_for_status()  # 检查HTTP错误

                soup = BeautifulSoup(response.text, 'lxml')

                # 调用对应的解析函数
                data = self.parse_article_by_url(soup, article.url, article.publish_date)

                if data and data.get('content'):
                    # 更新文章的 content 字段
                    article.content = data['content']
                    article.save(update_fields=['content'])
                    self.stdout.write(self.style.SUCCESS(f"成功更新: {article.title[:50]}..."))
                else:
                    self.stdout.write(self.style.WARNING(f"未能提取内容: {article.title[:50]}..."))

            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"请求失败 {article.url}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"解析失败 {article.url}: {e}"))

    def parse_article_by_url(self, soup, url, publish_date):
        """
        根据URL判断并调用相应的解析函数
        """
        try:
            if 'www.ciecc.com.cn' in url:
                return self.parse_ciecc_article(soup, url, publish_date)
            elif 'nads.ruc.edu.cn' in url:
                return self.parse_ruc_article(soup, url, publish_date)
            elif 'www.drc.gov.cn' in url:
                return self.parse_drc_article(soup, url, publish_date)
            elif 'www.cas.cn' in url:
                return self.parse_cas_article(soup, url, publish_date)
            elif 'www.amr.org.cn' in url:
                return self.parse_amr_article(soup, url, publish_date)
            elif 'www.ccidgroup.com' in url:
                return self.parse_ccid_article(soup, url, publish_date)
            elif 'www.sass.org.cn' in url:
                return self.parse_sass_article(soup, url, publish_date)
            else:
                self.stdout.write(f"未知网站，无法解析: {url}")
                return None
        except Exception as e:
            self.stdout.write(f"解析页面 {url} 时发生错误: {e}")
            return None

    
    def get_current_date():
    """获取当前日期和时间"""
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    return current_date

    def clean_text(self, text):
        """清理文本内容，去除多余空白字符"""
        if text:
            text = re.sub(r'\s+', ' ', text.strip())
            return text
        return ''

    def generic_title_from_meta_or_h(self, soup: BeautifulSoup) -> str:
        # meta 优先
        meta_title = soup.select_one('meta[property="og:title"][content]') or soup.select_one('meta[name="title"][content]')
        if meta_title and meta_title.get('content'):
            return self.clean_text(meta_title['content'])
        # h1/h2 次之
        for sel in ['h1', '.title h1', '.article-title h1', '.arti_title', '.wp_article_title', 'h2']:
            node = soup.select_one(sel)
            if node and node.get_text(strip=True):
                return self.clean_text(node.get_text())
        # 最后用 <title>
        if soup.title and soup.title.string:
            return self.clean_text(soup.title.string)
        return ''

    def generic_content_by_candidates(self, soup: BeautifulSoup) -> str:
        # 移除无关节点
        for tag in soup(['script', 'style', 'noscript']):
            tag.extract()
        # 常见正文容器优先
        candidate_selectors = [
            '.TRS_Editor', '.v_news_content', '.wp_articlecontent', '.article-content',
            '.content', '.article', '.text', '.detail-content', '#content', '.read', '.articleText'
        ]
        for sel in candidate_selectors:
            node = soup.select_one(sel)
            if node and node.get_text(strip=True):
                return self.clean_text(node.get_text("\n"))
        # 兜底：选择文本量最大的块级元素
        max_text = ''
        max_len = 0
        for node in soup.find_all(['article', 'section', 'div']):
            text = node.get_text("\n", strip=True)
            tlen = len(text)
            if tlen > max_len:
                max_len = tlen
                max_text = text
        return self.clean_text(max_text)

    
    def parse_ciecc_article(self, soup, url, publish_date):
        """解析中国国际工程咨询有限公司的文章"""
        try:
            data = {}
            data['title'] = soup.select('.comnewsl.fl tr')[0].text.strip()
            data['url'] = url
            data['publish_date'] = publish_date
            data['authors'] = '中国国际工程咨询有限公司（智库建议）'
            data['thinkank_name'] = '中国国际工程咨询有限公司'
            data['summary'] = ''
            data['content'] = soup.select('.bt_content')[0].text
            data['attachments'] = ''
            data['crawl_date'] = self.get_current_date()
            return data
        except (IndexError, AttributeError) as e:
            self.stdout.write(f"解析中国国际工程咨询有限公司页面 {url} 失败: {e}")
            return None

    def parse_ruc_article(self, soup, url, publish_date):
        """解析中国人民大学国家发展与战略研究院的文章"""
        try:
            data = {}
            title_selectors = ['h1.title', '.article-title h1', '.content-title h1', 'h1', '.title']
            content_selectors = ['.article-content', '.content-text', '.article-text', '.content', '.text']

            title = ''
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break

            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self.clean_text(content_elem.get_text())
                    break

            if not title:
                title = self.generic_title_from_meta_or_h(soup)
            if not content:
                content = self.generic_content_by_candidates(soup)
            if not title or not content:
                self.stdout.write(f"中国人民大学文章解析失败，标题或内容为空: {url}")
                return None

            data['title'] = title
            data['url'] = url
            data['publish_date'] = publish_date
            data['authors'] = '中国人民大学国家发展与战略研究院'
            data['thinkank_name'] = '中国人民大学国家发展与战略研究院'
            data['summary'] = ''
            data['content'] = content
            data['attachments'] = ''
            data['crawl_date'] = self.get_current_date()
            return data
        except Exception as e:
            self.stdout.write(f"解析中国人民大学页面 {url} 失败: {e}")
            return None

    def parse_drc_article(self, soup, url, publish_date):
        """解析国务院发展研究中心的文章"""
        try:
            data = {}
            # 尝试多种可能的选择器
            title_selectors = [
                '.article-title',
                '.title',
                'h1',
                '.headline'
            ]
            
            content_selectors = [
                '.article-content',
                '.content',
                '.text',
                '.article-text',
                '.main-content'
            ]
            
            # 获取标题
            title = ''
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break
            
            # 获取内容
            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self.clean_text(content_elem.get_text())
                    break
            
            if not title:
                title = self.generic_title_from_meta_or_h(soup)
            if not content:
                content = self.generic_content_by_candidates(soup)
            if not title or not content:
                self.stdout.write(f"国务院发展研究中心文章解析失败，标题或内容为空: {url}")
                return None
                
            data['title'] = title
            data['url'] = url
            data['publish_date'] = publish_date
            data['authors'] = '国务院发展研究中心'
            data['thinkank_name'] = '国务院发展研究中心'
            data['summary'] = ''
            data['content'] = content
            data['attachments'] = ''
            data['crawl_date'] = self.get_current_date()
            return data
        except Exception as e:
            self.stdout.write(f"解析国务院发展研究中心页面 {url} 失败: {e}")
            return None

    def parse_cas_article(self, soup, url, publish_date):
        """解析中国科学院的文章"""
        try:
            data = {}
            # 尝试多种可能的选择器
            title_selectors = [
                '.article-title',
                '.title',
                'h1',
                '.headline',
                '.news-title'
            ]
            
            content_selectors = [
                '.article-content',
                '.content',
                '.text',
                '.article-text',
                '.news-content',
                '.main-content'
            ]
            
            # 获取标题
            title = ''
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break
            
            # 获取内容
            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self.clean_text(content_elem.get_text())
                    break
            
            if not title:
                title = self.generic_title_from_meta_or_h(soup)
            if not content:
                content = self.generic_content_by_candidates(soup)
            if not title or not content:
                self.stdout.write(f"中国科学院文章解析失败，标题或内容为空: {url}")
                return None
                
            data['title'] = title
            data['url'] = url
            data['publish_date'] = publish_date
            data['authors'] = '中国科学院'
            data['thinkank_name'] = '中国科学院'
            data['summary'] = ''
            data['content'] = content
            data['attachments'] = ''
            data['crawl_date'] = self.get_current_date()
            return data
        except Exception as e:
            self.stdout.write(f"解析中国科学院页面 {url} 失败: {e}")
            return None
        def parse_amr_article(self, soup, url, publish_date):
        """解析中国宏观经济研究院的文章"""
        try:
            data = {}
            # 尝试多种可能的选择器
            title_selectors = [
                '.article-title',
                '.title',
                'h1',
                '.headline',
                '.news-title'
            ]
            
            content_selectors = [
                '.article-content',
                '.content',
                '.text',
                '.article-text',
                '.news-content',
                '.main-content'
            ]
            
            # 获取标题
            title = ''
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break
            
            # 获取内容
            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self.clean_text(content_elem.get_text())
                    break
            
            if not title:
                title = self.generic_title_from_meta_or_h(soup)
            if not content:
                content = self.generic_content_by_candidates(soup)
            if not title or not content:
                self.stdout.write(f"中国宏观经济研究院文章解析失败，标题或内容为空: {url}")
                return None
                
            data['title'] = title
            data['url'] = url
            data['publish_date'] = publish_date
            data['authors'] = '中国宏观经济研究院'
            data['thinkank_name'] = '中国宏观经济研究院'
            data['summary'] = ''
            data['content'] = content
            data['attachments'] = ''
            data['crawl_date'] = self.get_current_date()
            return data
        except Exception as e:
            self.stdout.write(f"解析中国宏观经济研究院页面 {url} 失败: {e}")
            return None

    def parse_ccid_article(self, soup, url, publish_date):
        """解析CCiD赛迪研究院的文章"""
        try:
            data = {}
            # 尝试多种可能的选择器
            title_selectors = [
                '.article-title',
                '.title',
                'h1',
                '.headline',
                '.news-title'
            ]
            
            content_selectors = [
                '.article-content',
                '.content',
                '.text',
                '.article-text',
                '.news-content',
                '.main-content'
            ]
            
            # 获取标题
            title = ''
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break
            
            # 获取内容
            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self.clean_text(content_elem.get_text())
                    break
            
            if not title:
                title = self.generic_title_from_meta_or_h(soup)
            if not content:
                content = self.generic_content_by_candidates(soup)
            if not title or not content:
                self.stdout.write(f"CCiD赛迪研究院文章解析失败，标题或内容为空: {url}")
                return None
                
            data['title'] = title
            data['url'] = url
            data['publish_date'] = publish_date
            data['authors'] = 'CCiD赛迪研究院'
            data['thinkank_name'] = 'CCiD赛迪研究院'
            data['summary'] = ''
            data['content'] = content
            data['attachments'] = ''
            data['crawl_date'] = self.get_current_date()
            return data
        except Exception as e:
            self.stdout.write(f"解析CCiD赛迪研究院页面 {url} 失败: {e}")
            return None
            
    def parse_sass_article(self, soup, url, publish_date):
        """解析上海社会科学院的文章"""
        try:
            data = {}
            title_selectors = ['.article-title', '.title', 'h1', '.headline', '.news-title']
            content_selectors = ['.article-content', '.content', '.text', '.article-text', '.news-content', '.main-content']

            title = ''
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break

            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self.clean_text(content_elem.get_text())
                    break

            if not title:
                title = self.generic_title_from_meta_or_h(soup)
            if not content:
                content = self.generic_content_by_candidates(soup)
            if not title or not content:
                self.stdout.write(f"上海社会科学院文章解析失败，标题或内容为空: {url}")
                return None

            data['title'] = title
            data['url'] = url
            data['publish_date'] = publish_date
            data['authors'] = '上海社会科学院'
            data['thinkank_name'] = '上海社会科学院'
            data['summary'] = ''
            data['content'] = content
            data['attachments'] = ''
            data['crawl_date'] = self.get_current_date()
            return data
        except Exception as e:
            self.stdout.write(f"解析上海社会科学院页面 {url} 失败: {e}")
            return None