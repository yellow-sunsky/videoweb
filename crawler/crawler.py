import os
import django
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time

# 设置 Django 项目的环境变量和初始化 Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videoproject.settings')
django.setup()

from video.models import Video  # 假设 v_video 模型名为 Video

logger = logging.getLogger(__name__)

def crawl_and_save():
    url = 'https://www1.gdtv.cn/tvColumn/687'
    try:
        # 设置 ChromeDriver 路径
        service = Service(r'D:\Program Files\chromedriver-win64\chromedriver.exe')

        # 设置 Chrome 浏览器可执行文件路径
        chrome_options = Options()
        chrome_options.binary_location = r'C:\Program Files\Google\Chrome Beta\Application\chrome.exe'

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)

        # 模拟正常滑动，滚动 5 次
        scroll_step = 300  # 每次滚动的像素数
        scroll_pause_time = 1  # 每次滚动后等待的时间（秒）
        for _ in range(5):
            # 滚动页面
            driver.execute_script(f"window.scrollBy(0, {scroll_step});")
            time.sleep(scroll_pause_time)

        # 显式等待，最多等待 10 秒，直到符合条件的 a 标签元素加载完成
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.index__card-title___1ZasM'))
            )
        except Exception as e:
            logger.error(f"等待元素加载时出错: {e}")

        # 获取页面源代码
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # 找到所有视频卡片
        video_cards = soup.find_all('div', class_='index__card-box___2Angp index__card-box-bottom___2wir8')
        for card in video_cards:
            # 查找标题和页面链接
            title_link = card.find('a', class_='index__card-title___1ZasM')
            if title_link:
                title = title_link.get('title')
                # 检查数据库中是否存在相同标题的视频
                if Video.objects.filter(title=title).exists():
                    print("遇到重复标题，停止抓取。")
                    break

                href = title_link.get('href')
                if title and href:
                    video_url = f"https://www1.gdtv.cn{href}"

                    # 查找封面图链接
                    cover_img = card.find('img')
                    if cover_img:
                        cover_url = cover_img.get('src')
                    else:
                        cover_url = None

                    # 打印标题、链接和封面图链接
                    print(f"标题: {title}, 链接: {video_url}, 封面图链接: {cover_url}")

                    try:
                        # 进入视频播放页面
                        driver.get(video_url)
                        # 显式等待，最多等待 10 秒，直到视频元素加载完成
                        try:
                            video_element = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'video.vjs-tech'))
                            )
                            video_src = video_element.get_attribute('src')

                            if video_src:
                                # 保存到数据库
                                if cover_url:
                                    Video.objects.create(title=title, file=video_src, cover=cover_url, status='0', classification_id=2)
                                else:
                                    Video.objects.create(title=title, file=video_src, status='0', classification_id=2)
                                print("数据保存成功！")
                            else:
                                logger.error(f"未找到视频直链: {video_url}")
                        except Exception as e:
                            logger.error(f"等待视频元素加载时出错: {e}")
                    except Exception as e:
                        logger.error(f"保存数据时出错: {e}")
        print("数据抓取并保存成功！")
    except Exception as e:
        logger.error(f"发生未知错误: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    crawl_and_save()