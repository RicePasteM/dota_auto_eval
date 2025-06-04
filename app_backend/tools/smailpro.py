import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import http.client
import os

# 禁用所有代理设置
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

def create_session():
    """创建一个配置好的请求会话"""
    session = requests.Session()
    
    # 配置重试策略
    retry_strategy = Retry(
        total=3,  # 总重试次数
        backoff_factor=0.5,  # 重试间隔
        status_forcelist=[500, 502, 503, 504]  # 需要重试的HTTP状态码
    )
    
    # 配置适配器
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 显式禁用所有代理
    session.trust_env = False  # 不使用环境变量中的代理设置
    session.proxies.clear()  # 清除所有代理设置
    session.proxies.update({
        'http': None,
        'https': None,
        'no_proxy': '*'
    })
    
    return session

def get_default_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }

def create_payload(email, url, mid=None):
    """使用requests库创建payload"""
    session = create_session()
    base_url = "https://smailpro.com/app/payload"
    params = {
        'url': url
    }
    
    if email:
        params['email'] = email

    if mid:
        params['mid'] = mid
    
    try:
        response = session.get(
            base_url,
            params=params,
            headers=get_default_headers()
        )
        return response.text
    except requests.exceptions.RequestException as e:
        return str(e)

def create_email(payload):
    session = create_session()
    url = f"https://app.sonjj.com/v1/temp_email/create?payload={payload}"
    
    try:
        response = session.get(url, headers=get_default_headers())
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_inbox(payload):
    session = create_session()
    url = f"https://app.sonjj.com/v1/temp_email/inbox?payload={payload}"
    
    try:
        response = session.get(url, headers=get_default_headers())
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_message_content(payload):
    """获取指定邮件的内容
    
    Args:
        email: 邮箱地址
        message_id: 邮件ID
        
    Returns:
        dict: 包含邮件内容的响应
    """
    session = create_session()
    url = "https://app.sonjj.com/v1/temp_email/message"
    params = {
        'payload': payload
    }
    
    try:
        response = session.get(
            url,
            params=params,
            headers=get_default_headers()
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}