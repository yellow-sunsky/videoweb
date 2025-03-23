import requests
from bs4 import BeautifulSoup
from .models import v_video  # 将yourappname替换为实际应用名称

def crawl_and_save():
    url = 'https://www1.gdtv.cn/tv/4a4fc503864405fdb8a9c87ab2e9f32f'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # 找到所有符合条件的a标签
        links = soup.find_all('a', class_='index__card-title___1ZasM')
        for link in links:
            title = link.get('title')
            href = link.get('href')
            if title and href:
                # 保存到数据库
                v_video.objects.create(title=title, file=href)
        print("数据抓取并保存成功！")
    else:
        print(f"请求失败，状态码: {response.status_code}")