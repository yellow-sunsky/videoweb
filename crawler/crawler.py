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

def crawl_and_save(url, classification_id):
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

        # 显式等待，最多等待 10 秒，直到符合条件的元素加载完成
        try:
            if 'gdtv.cn' in url:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.index__card-title___1ZasM'))
                )
            elif 'gztv.com' in url:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.row-video.row-video'))
                )
            elif 'sztv.com.cn' in url:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.dianbo_list_title'))
                )
        except Exception as e:
            logger.error(f"等待元素加载时出错: {e}")

        # 获取页面源代码
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # 找到所有视频卡片
        if 'gdtv.cn' in url:
            video_cards = soup.find_all('div', class_='index__card-box___2Angp index__card-box-bottom___2wir8')
        elif 'gztv.com' in url:
            video_cards = soup.find_all('div', class_='row-video row-video')
        elif 'sztv.com.cn' in url:
            video_cards = soup.find_all('div', class_='dianbo_list_title')

        for card in video_cards:
            # 查找标题和页面链接
            if 'gdtv.cn' in url:
                title_link = card.find('a', class_='index__card-title___1ZasM')
                if title_link:
                    title = title_link.text.strip()  # 获取标题并去除两端空白字符
                else:
                    continue
            elif 'gztv.com' in url:
                title_element = card.find('div', class_='title text-line-2')
                if title_element:
                    title = title_element.get('title')
                else:
                    continue
            elif 'sztv.com.cn' in url:
                title = card.get('title')
                if not title:
                    continue

            print(f"开始title: {title}")
            if title:
                # 检查数据库中是否存在相同标题的视频
                if Video.objects.filter(title=title).exists():
                    print("遇到重复标题，停止抓取。")
                    break

                # 查找封面图链接
                if 'gdtv.cn' in url:
                    cover_img = card.find('img')
                elif 'gztv.com' in url:
                    cover_img = card.find('img', class_='el-image__inner')
                elif 'sztv.com.cn' in url:
                    if "id=7901" in url:
                        cover_url = "https://www.sztv.com.cn/ysz/upload/Image/mrtp/2022/04/14/e7bdd4da3cea43daae2aa229bd50b3c1.jpg"
                    elif "id=7900" in url:
                        cover_url = "https://www.sztv.com.cn/ysz/upload/Image/mrtp/2019/09/10/f1b38a3da3f64e84a36e571635b95714.jpg"
                    else:
                        cover_url = None
                    cover_img = None

                if cover_img:
                    cover_url = cover_img.get('src')
                elif cover_url is None:
                    cover_url = "https://www.sztv.com.cn/ysz/upload/Image/mrtp/2019/09/10/f1b38a3da3f64e84a36e571635b95714.jpg"

                # 查找视频链接（针对 sztv.com.cn 的情况）
                if 'sztv.com.cn' in url:
                    video_element = card.find_parent().find('video')
                    if video_element:
                        video_src = video_element.get('src')
                    else:
                        video_src = None
                elif 'gdtv.cn' in url:
                    href = title_link.get('href')
                    video_url = f"https://www1.gdtv.cn{href}"
                    driver.get(video_url)
                    try:
                        video_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'video.vjs-tech'))
                        )
                        video_src = video_element.get_attribute('src')
                    except Exception as e:
                        logger.error(f"等待视频元素加载时出错: {e}")
                        video_src = None
                elif 'gztv.com' in url:
                    video_src = None  # 按照之前逻辑，gztv.com 未获取视频链接

                # 打印标题、链接和封面图链接
                print(f"标题: {title}, 视频链接: {video_src if video_src else '无'}, 封面图链接: {cover_url}")

                try:
                    # 保存到数据库
                    if video_src and cover_url:
                        Video.objects.create(title=title, file=video_src, cover=cover_url, status='0', classification_id=classification_id)
                    elif video_src:
                        Video.objects.create(title=title, file=video_src, status='0', classification_id=classification_id)
                    elif cover_url:
                        Video.objects.create(title=title, cover=cover_url, status='0', classification_id=classification_id)
                    print("数据保存成功！")
                except Exception as e:
                    logger.error(f"保存数据时出错: {e}")
        print("数据抓取并保存成功！")
        return {'status': 'success', 'message': '数据抓取并保存成功！'}
    except Exception as e:
        logger.error(f"发生未知错误: {e}")
        return {'status': 'error', 'message': f'发生未知错误: {e}'}
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    # 示例调用
    url = 'https://www.sztv.com.cn/dianbo_list.shtml?pid=7867&id=7901'  # 替换为实际的 sztv.com.cn 网址
    classification_id = 2  # 替换为实际的分类 ID
    crawl_and_save(url, classification_id)