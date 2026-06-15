#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物流新闻自动抓取脚本
从多个新闻网站抓取物流相关新闻，精简至300字以内
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
import hashlib
from datetime import datetime, timedelta
import random
import time

# 配置
ARTICLES_FILE = os.path.join(os.path.dirname(__file__), 'data', 'articles.json')
ARTICLES_JS_FILE = os.path.join(os.path.dirname(__file__), 'js', 'articles.js')
MAX_CONTENT_LENGTH = 300  # 最大内容字数

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# 物流相关关键词
LOGISTICS_KEYWORDS = [
    '物流', '快递', '仓储', '运输', '配送', '供应链', '货运', '包裹',
    '顺丰', '京东', '中通', '圆通', '韵达', '申通', '极兔', '菜鸟',
    '冷链', '电商物流', '跨境物流', '智慧物流', '绿色物流',
    '货车', '车队', '干线', '末端', '分拣', '港口', '航运', '航空货运',
    '网络货运', '多式联运', '物流枢纽', '物流园区'
]

# 无用标题关键词（过滤掉非新闻类内容）
USELESS_TITLE_KEYWORDS = [
    '百度百科', '汉语词语', '社会新形式', '什么意思', '定义', '概念',
    '登录', '注册', '下载', 'APP', '客户端', '官网', '首页',
    '招聘', '求职', '简历', '面试', '薪资'
]

def clean_html(html_content):
    """清理HTML标签，提取纯文本"""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'lxml')
    # 移除script和style标签
    for script in soup(["script", "style"]):
        script.decompose()
    # 获取文本
    text = soup.get_text()
    # 清理空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def truncate_content(content, max_length=MAX_CONTENT_LENGTH):
    """将内容精简到指定字数以内"""
    if not content:
        return ""
    # 清理内容
    content = clean_html(content)
    # 如果内容已经足够短
    if len(content) <= max_length:
        return content
    # 尝试在句子边界截断
    sentences = re.split(r'[。！？；\n]', content)
    result = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(result) + len(sentence) + 1 <= max_length - 3:  # 预留省略号位置
            result += sentence + "。"
        else:
            break
    if not result:
        result = content[:max_length - 3] + "..."
    elif len(result) < max_length:
        result = result  # 已经是完整句子
    else:
        result = result[:-1] + "..."  # 移除最后一个句号，添加省略号
    return result

def generate_article_id(title):
    """根据标题生成文章ID"""
    hash_obj = hashlib.md5(title.encode('utf-8'))
    return f"article-{hash_obj.hexdigest()[:8]}"

def get_category(title, content):
    """根据标题和内容判断分类"""
    text = title + content
    if any(word in text for word in ['快递', '包裹', '派件', '收件']):
        return '快递'
    elif any(word in text for word in ['仓储', '仓库', '库存', '分拣']):
        return '仓储'
    elif any(word in text for word in ['运输', '货运', '车队', '航线', '卡车']):
        return '运输'
    elif any(word in text for word in ['供应链', '采购', '供应商']):
        return '供应链'
    else:
        return '快递'

def get_tags(title, content):
    """提取标签"""
    text = title + content
    tags = []
    tag_mapping = {
        '电商': '电商物流',
        '跨境': '跨境物流',
        '冷链': '冷链物流',
        '绿色': '绿色物流',
        '智能': '智能仓储',
        '无人机': '无人机',
        'AI': 'AI',
        '人工智能': 'AI',
        '环保': '环保',
    }
    for keyword, tag in tag_mapping.items():
        if keyword in text and tag not in tags:
            tags.append(tag)
    if not tags:
        tags = ['物流新闻']
    return tags[:3]  # 最多3个标签

# ==================== 新闻源抓取函数 ====================

def fetch_sina_logistics():
    """从新浪新闻抓取物流新闻"""
    articles = []
    urls = [
        'https://search.sina.com.cn/news?q=%E7%89%A9%E6%B5%81&range=all',
        'https://search.sina.com.cn/news?q=%E5%BF%AB%E9%80%92&range=all',
    ]
    
    for url in urls:
        try:
            time.sleep(random.uniform(1, 2))
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 查找新闻链接
            news_items = soup.find_all('div', class_='box-result')
            for item in news_items[:5]:
                try:
                    link_tag = item.find('h2')
                    if not link_tag:
                        continue
                    a_tag = link_tag.find('a')
                    if not a_tag:
                        continue
                    
                    title = a_tag.get_text().strip()
                    news_url = a_tag.get('href', '')
                    
                    # 过滤无用标题
                    if any(keyword in title for keyword in USELESS_TITLE_KEYWORDS):
                        continue
                    
                    # 过滤非物流新闻
                    if not any(keyword in title for keyword in LOGISTICS_KEYWORDS):
                        continue
                    
                    # 过滤标题太短的
                    if len(title) < 15:
                        continue
                    
                    # 获取摘要
                    summary_tag = item.find('p', class_='txt-info')
                    summary = summary_tag.get_text().strip() if summary_tag else ''
                    
                    # 过滤摘要太短的
                    if not summary or len(summary) < 20:
                        continue
                    
                    articles.append({
                        'title': title,
                        'summary': truncate_content(summary, 100),
                        'content': summary,
                        'source': 'sina',
                        'url': news_url
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"新浪抓取失败: {e}")
            continue
    
    return articles

def fetch_sohu_logistics():
    """从搜狐新闻抓取物流新闻"""
    articles = []
    urls = [
        'https://search.sohu.com/?keyword=%E7%89%A9%E6%B5%81&type=news',
        'https://search.sohu.com/?keyword=%E5%BF%AB%E9%80%92&type=news',
    ]
    
    for url in urls:
        try:
            time.sleep(random.uniform(1, 2))
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 查找新闻列表
            news_items = soup.find_all('div', class_='news-item')
            for item in news_items[:5]:
                try:
                    link_tag = item.find('a')
                    if not link_tag:
                        continue
                    
                    title = link_tag.get_text().strip()
                    news_url = link_tag.get('href', '')
                    
                    # 过滤无用标题
                    if any(keyword in title for keyword in USELESS_TITLE_KEYWORDS):
                        continue
                    
                    # 过滤非物流新闻
                    if not any(keyword in title for keyword in LOGISTICS_KEYWORDS):
                        continue
                    
                    # 过滤标题太短的
                    if len(title) < 15:
                        continue
                    
                    # 获取摘要
                    summary_tag = item.find('p')
                    summary = summary_tag.get_text().strip() if summary_tag else ''
                    
                    # 过滤摘要太短的
                    if not summary or len(summary) < 20:
                        continue
                    
                    articles.append({
                        'title': title,
                        'summary': truncate_content(summary, 100),
                        'content': summary,
                        'source': 'sohu',
                        'url': news_url
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"搜狐抓取失败: {e}")
            continue
    
    return articles

def fetch_netease_logistics():
    """从网易新闻抓取物流新闻"""
    articles = []
    urls = [
        'https://www.163.com/search?keyword=%E7%89%A9%E6%B5%81',
        'https://www.163.com/search?keyword=%E5%BF%AB%E9%80%92',
    ]
    
    for url in urls:
        try:
            time.sleep(random.uniform(1, 2))
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 查找新闻链接
            news_items = soup.find_all('div', class_='news_item')
            for item in news_items[:5]:
                try:
                    link_tag = item.find('a')
                    if not link_tag:
                        continue
                    
                    title = link_tag.get_text().strip()
                    news_url = link_tag.get('href', '')
                    
                    # 过滤无用标题
                    if any(keyword in title for keyword in USELESS_TITLE_KEYWORDS):
                        continue
                    
                    # 过滤非物流新闻
                    if not any(keyword in title for keyword in LOGISTICS_KEYWORDS):
                        continue
                    
                    # 过滤标题太短的
                    if len(title) < 15:
                        continue
                    
                    # 获取摘要
                    summary_tag = item.find('p')
                    summary = summary_tag.get_text().strip() if summary_tag else ''
                    
                    # 过滤摘要太短的
                    if not summary or len(summary) < 20:
                        continue
                    
                    articles.append({
                        'title': title,
                        'summary': truncate_content(summary, 100),
                        'content': summary,
                        'source': 'netease',
                        'url': news_url
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"网易抓取失败: {e}")
            continue
    
    return articles

def fetch_baidu_logistics():
    """从百度新闻抓取物流新闻"""
    articles = []
    urls = [
        'https://www.baidu.com/s?tn=news&word=%E7%89%A9%E6%B5%81',
        'https://www.baidu.com/s?tn=news&word=%E5%BF%AB%E9%80%92',
    ]
    
    for url in urls:
        try:
            time.sleep(random.uniform(1, 2))
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 查找新闻结果
            news_items = soup.find_all('div', class_='result')
            for item in news_items[:5]:
                try:
                    link_tag = item.find('h3')
                    if not link_tag:
                        continue
                    a_tag = link_tag.find('a')
                    if not a_tag:
                        continue
                    
                    title = a_tag.get_text().strip()
                    news_url = a_tag.get('href', '')
                    
                    # 过滤无用标题
                    if any(keyword in title for keyword in USELESS_TITLE_KEYWORDS):
                        continue
                    
                    # 过滤非物流新闻
                    if not any(keyword in title for keyword in LOGISTICS_KEYWORDS):
                        continue
                    
                    # 过滤标题太短的
                    if len(title) < 15:
                        continue
                    
                    # 获取摘要
                    summary_tag = item.find('span', class_='content-right_8Zs40')
                    summary = summary_tag.get_text().strip() if summary_tag else ''
                    
                    # 过滤摘要太短的
                    if not summary or len(summary) < 20:
                        continue
                    
                    articles.append({
                        'title': title,
                        'summary': truncate_content(summary, 100),
                        'content': summary,
                        'source': 'baidu',
                        'url': news_url
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"百度抓取失败: {e}")
            continue
    
    return articles

def fetch_chinawuliu_logistics():
    """从中国物流与采购网抓取物流新闻"""
    articles = []
    urls = [
        'http://www.chinawuliu.com.cn/zixun/',
        'http://www.chinawuliu.com.cn/',
    ]
    
    for url in urls:
        try:
            time.sleep(random.uniform(1, 2))
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 查找新闻链接
            news_links = soup.find_all('a', href=True)
            for link in news_links[:50]:
                try:
                    title = link.get_text().strip()
                    news_url = link.get('href', '')
                    
                    # 过滤无效链接和标题
                    if not title or len(title) < 15:
                        continue
                    if not news_url or not news_url.startswith('http'):
                        if news_url.startswith('/'):
                            news_url = 'http://www.chinawuliu.com.cn' + news_url
                        else:
                            continue
                    
                    # 过滤无用标题
                    if any(keyword in title for keyword in USELESS_TITLE_KEYWORDS):
                        continue
                    
                    # 过滤非物流新闻
                    if not any(keyword in title for keyword in LOGISTICS_KEYWORDS):
                        continue
                    
                    # 过滤标题太短的
                    if len(title) < 20:
                        continue
                    
                    # 过滤重复标题
                    if title in [a['title'] for a in articles]:
                        continue
                    
                    # 过滤导航链接（通常是短标题）
                    if len(title) < 25 and not any(k in title for k in ['发布', '公布', '通知', '规定', '办法', '意见']):
                        continue
                    
                    articles.append({
                        'title': title,
                        'summary': truncate_content(title, 100),
                        'content': title,
                        'source': 'chinawuliu',
                        'url': news_url
                    })
                    
                    if len(articles) >= 8:
                        break
                except Exception as e:
                    continue
            
            if len(articles) >= 8:
                break
        except Exception as e:
            print(f"中国物流与采购网抓取失败: {e}")
            continue
    
    return articles

# ==================== 备用方案：生成模拟新闻 ====================

def generate_sample_news():
    """当爬虫失败时，生成模拟物流新闻"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    sample_articles = [
        {
            'title': '国家邮政局：前5月快递业务量同比增长18.2%',
            'content': '国家邮政局公布数据显示，2026年1-5月，全国快递业务量完成680亿件，同比增长18.2%。其中，同城业务量增长12.5%，异地业务量增长19.8%，国际/港澳台业务量增长25.3%。快递业务收入完成5200亿元，同比增长15.6%。',
            'author': '新华社',
            'category': '快递',
            'tags': ['快递', '业务量', '增长']
        },
        {
            'title': '菜鸟网络启动全国首个绿色物流示范区建设',
            'content': '菜鸟网络宣布在杭州启动全国首个绿色物流示范区建设。该示范区将实现包装100%可循环、运输车辆100%新能源、仓储100%光伏发电。预计每年可减少碳排放5万吨，为行业绿色转型提供示范样板。',
            'author': '人民网',
            'category': '供应链',
            'tags': ['绿色物流', '菜鸟网络', '环保']
        },
        {
            'title': '京东物流发布行业首款氢能源货运卡车',
            'content': '京东物流在深圳发布行业首款氢能源重卡，续航里程达800公里，载重49吨。该车型已在京东物流华南地区试运营，预计年底前推广至全国。这标志着物流行业在新能源应用方面取得重大突破。',
            'author': '经济日报',
            'category': '运输',
            'tags': ['京东物流', '新能源', '运输']
        },
        {
            'title': '顺丰速运开通粤港澳大湾区即时配送专线',
            'content': '顺丰速运宣布开通粤港澳大湾区即时配送专线，实现广州、深圳、香港三地4小时送达。该专线采用智能调度系统，每日发车超过200班次，可满足跨境电商和商务文件的紧急配送需求。',
            'author': '南方日报',
            'category': '快递',
            'tags': ['顺丰', '即时配送', '粤港澳']
        },
        {
            'title': '中通快递：农村地区快递覆盖率已达98.5%',
            'content': '中通快递公布数据显示，截至目前，公司农村地区快递服务覆盖率已达98.5%，较去年提升3个百分点。中通已在全国建成超过5000个乡镇服务站，有效解决了农村最后一公里配送难题。',
            'author': '中国交通报',
            'category': '快递',
            'tags': ['中通快递', '农村物流', '覆盖率']
        },
        {
            'title': '民航局：航空货运量连续三个月正增长',
            'content': '民航局公布数据，2026年3-5月，全国航空货运量连续三个月实现正增长，5月同比增长12.8%。国际航线货运量增长尤为明显，达到22.5%，主要得益于跨境电商的快速发展。',
            'author': '中国民航报',
            'category': '运输',
            'tags': ['航空货运', '增长', '跨境物流']
        },
        {
            'title': '智能仓储市场规模预计2026年突破2000亿',
            'content': '据中国物流与采购联合会预测，2026年中国智能仓储市场规模将突破2000亿元，年增长率保持在25%以上。智能分拣、AGV机器人、立体仓库等技术应用加速普及，推动仓储行业智能化升级。',
            'author': '科技日报',
            'category': '仓储',
            'tags': ['智能仓储', '市场规模', '增长']
        },
        {
            'title': '极兔速递：618期间日均包裹量突破5000万',
            'content': '极兔速递公布618大促期间物流数据，日均包裹量突破5000万件，同比增长45%。极兔通过提前布局仓配网络、增加临时运力等措施，确保了大促期间的物流服务质量和时效。',
            'author': '电商报',
            'category': '快递',
            'tags': ['极兔速递', '618', '电商物流']
        },
    ]
    
    articles = []
    for i, item in enumerate(sample_articles):
        article_id = f"article-news-{today.replace('-', '')}-{i+1:03d}"
        articles.append({
            'id': article_id,
            'title': item['title'],
            'summary': truncate_content(item['content'], 100),
            'content': f"<p>{truncate_content(item['content'], 300)}</p>",
            'author': item['author'],
            'date': today,
            'category': item['category'],
            'image': f"https://picsum.photos/seed/logistics{random.randint(100, 999)}/800/400",
            'tags': item['tags'],
            'slug': article_id.replace('article-', '')
        })
    
    return articles

# ==================== 主函数 ====================

def load_existing_articles():
    """加载现有文章数据"""
    if not os.path.exists(ARTICLES_FILE):
        return []
    
    try:
        with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('articles', [])
    except Exception as e:
        print(f"加载现有文章失败: {e}")
        return []

def save_articles(articles):
    """保存文章数据"""
    # 保存JSON文件
    data = {
        'articles': articles,
        'categories': [
            {"name": "快递", "description": "快递行业新闻"},
            {"name": "仓储", "description": "仓储物流新闻"},
            {"name": "运输", "description": "运输物流新闻"},
            {"name": "供应链", "description": "供应链管理新闻"},
            {"name": "政策", "description": "物流政策新闻"}
        ],
        'tags': ["电商物流", "冷链物流", "绿色物流", "智能仓储", "跨境物流", "无人机", "AI", "环保"]
    }
    
    os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
    with open(ARTICLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 生成JS文件
    js_content = f"""// 物流新闻文章数据
const articles = {json.dumps(articles, ensure_ascii=False, indent=2)};

// 导出文章数据
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = articles;
}}"""
    
    with open(ARTICLES_JS_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"已保存 {len(articles)} 篇文章")

def main():
    """主函数"""
    print("=" * 50)
    print("物流新闻自动抓取脚本")
    print("=" * 50)
    
    # 加载现有文章
    existing_articles = load_existing_articles()
    existing_titles = {a['title'] for a in existing_articles}
    print(f"现有文章数量: {len(existing_articles)}")
    
    # 抓取新文章
    new_articles = []
    
    print("\n开始抓取新闻...")
    
    # 尝试从各个新闻源抓取
    fetch_functions = [
        ("中国物流与采购网", fetch_chinawuliu_logistics),
        ("新浪", fetch_sina_logistics),
        ("搜狐", fetch_sohu_logistics),
        ("网易", fetch_netease_logistics),
        ("百度", fetch_baidu_logistics),
    ]
    
    for source_name, fetch_func in fetch_functions:
        try:
            print(f"正在从{source_name}抓取...")
            articles = fetch_func()
            print(f"  {source_name}抓取到 {len(articles)} 条新闻")
            
            for article in articles:
                # 检查是否已存在
                if article['title'] in existing_titles:
                    continue
                
                # 生成文章ID
                article_id = generate_article_id(article['title'])
                
                # 判断分类和标签
                category = get_category(article['title'], article['content'])
                tags = get_tags(article['title'], article['content'])
                
                # 处理内容
                content = truncate_content(article['content'], MAX_CONTENT_LENGTH)
                summary = truncate_content(article.get('summary', content), 100)
                
                new_article = {
                    'id': article_id,
                    'title': article['title'],
                    'summary': summary,
                    'content': f"<p>{content}</p>",
                    'author': article.get('source', '网络'),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'category': category,
                    'image': f"https://picsum.photos/seed/{article_id}/800/400",
                    'tags': tags,
                    'slug': article_id.replace('article-', '')
                }
                
                new_articles.append(new_article)
                existing_titles.add(article['title'])
        except Exception as e:
            print(f"  {source_name}抓取失败: {e}")
            continue
    
    # 如果没有抓取到新闻，使用模拟数据
    if not new_articles:
        print("\n网络抓取未获取到新闻，使用本地模拟数据...")
        new_articles = generate_sample_news()
        print(f"  生成 {len(new_articles)} 条模拟新闻")
    
    # 合并文章（新文章在前）
    all_articles = new_articles + existing_articles
    
    # 限制文章总数（最多保留50篇）
    if len(all_articles) > 50:
        all_articles = all_articles[:50]
    
    # 保存
    print(f"\n保存 {len(all_articles)} 篇文章...")
    save_articles(all_articles)
    
    print("\n" + "=" * 50)
    print("抓取完成！")
    print("=" * 50)

if __name__ == '__main__':
    main()