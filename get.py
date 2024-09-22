import requests
from lxml import etree
import json
import random
import time


proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}

# 请求歌曲页面的 headers
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    ),
    "Referer": "https://music.163.com/"
}

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time



def get_songid_from_playlist(url):
    """
    使用 Selenium 从嵌入 iframe 的歌单页面提取所有歌曲的 song id。
    
    参数:
    - url (str): 歌单页面的 URL
    
    返回:
    - List[str]: 包含所有 song id 的列表
    """
    options = Options()
    options.add_argument("--headless")  # 运行无头模式，不显示浏览器界面
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 初始化 WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        
        # 等待页面加载
        # time.sleep(5)
        
        # 在控制台执行 document.cookie="os=pc"
        driver.execute_script('document.cookie="os=pc"')
        
        # 刷新页面
        driver.refresh()
        
        # 等待页面重新加载
        time.sleep(5)

        # 切换到 iframe
        iframe = driver.find_element(By.ID, "g_iframe")  # 获取 iframe 的元素 (可能需要检查 iframe 的 ID 或者其他属性)
        driver.switch_to.frame(iframe)
        
        # 提取所有 song id
        song_id_elements = driver.find_elements(By.XPATH, '//a[contains(@href, "/song?id=")]')
        song_ids = [element.get_attribute('href').split('=')[-1] for element in song_id_elements]
        
        return song_ids
    
    except Exception as e:
        print(f"发生错误: {e}")
        return []
    
    finally:
        driver.quit()

def download_song_and_lyrics(song_id):
    """
    根据歌曲ID下载歌曲和歌词，保存为MP3和LRC文件。

    参数:
    - song_id (str): 网易云音乐的歌曲ID
    """
    try:
        # 验证song_id是字符串
        if not isinstance(song_id, str):
            song_id = str(song_id)
        
        # 构造歌曲信息页面的 URL
        song_info_url = f"https://music.163.com/song?id={song_id}"

        # 请求歌曲页面
        response = requests.get(song_info_url, headers=headers, proxies=proxies)
        if response.status_code != 200:
            print(f"请求歌曲页面失败，状态码: {response.status_code}, 信息: {response.text}")
            return
        response.raise_for_status()

        # 检查页面内容是否包含“很抱歉，你要查找的网页找不到”
        if "很抱歉，你要查找的网页找不到" in response.text:
            print("请求的歌曲页面不存在。")
            return

        # 解析 HTML 内容
        html = etree.HTML(response.text)

        # 使用 XPath 获取歌曲名称
        song_name_xpath = '/html/body/div[3]/div[1]/div/div/div[1]/div[1]/div[2]/div[1]/div/em'
        song_name_elements = html.xpath(song_name_xpath)

        # 检查是否成功获取歌曲名称
        if not song_name_elements:
            print("歌曲名称未找到。")
            return

        song_name = song_name_elements[0].text
        print(f"Song name: {song_name}")

        # 替换歌曲名中的非法字符
        valid_filename = "".join(c for c in song_name if c.isalnum() or c in (' ', '_')).rstrip()

        # MP3 文件下载链接
        mp3_url = f"http://music.163.com/song/media/outer/url?id={song_id}.mp3"

        # 下载 MP3 文件
        print("正在下载 MP3 文件...")
        mp3_response = requests.get(mp3_url, allow_redirects=True, headers=headers, proxies=proxies)
        if mp3_response.status_code != 200:
            print(f"下载 MP3 文件失败，状态码: {mp3_response.status_code}, 信息: {mp3_response.text}")
            return
        mp3_response.raise_for_status()

        # 保存 MP3 文件
        mp3_filename = f".\\data\\{valid_filename}.mp3"
        with open(mp3_filename, "wb") as f:
            f.write(mp3_response.content)
        print(f"MP3 文件已保存为 {mp3_filename}")

        # 获取歌词并保存为 .lrc 文件
        def get_lyric(song_id):
            """
            获取网易云音乐的歌词

            参数:
            - song_id (str): 歌曲ID

            返回:
            - str: 歌词文本
            """
            lyric_url = f"http://music.163.com/api/song/lyric?id={song_id}+&lv=1&tv=-1"
            r = requests.get(lyric_url, headers=headers, proxies=proxies)
            if r.status_code != 200:
                print(f"获取歌词失败，状态码: {r.status_code}, 信息: {r.text}")
                return None
            r.raise_for_status()
            json_obj = json.loads(r.text)
            if "lrc" in json_obj and "lyric" in json_obj["lrc"]:
                return json_obj["lrc"]["lyric"]
            else:
                print("未找到歌词。")
                return None

        # 获取歌词文本
        lyrics = get_lyric(song_id)

        if lyrics:
            # 保存歌词为 .lrc 文件
            lrc_filename = f".\\data\\{valid_filename}.lrc"
            with open(lrc_filename, "w", encoding="utf-8") as f:
                f.write(lyrics)
            print(f"歌词文件已保存为 {lrc_filename}")
        else:
            print("未能下载歌词。")

    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

# while(True):
#     song_id = random.randint(10000000,99999999)
#     print(song_id)
#     download_song_and_lyrics(song_id)
#     time.sleep(random.random()*5)

# playlist_url = "https://music.163.com/#/discover/toplist?id=3778678" #2024/09/05top
playlist_urls = ['https://music.163.com/#/playlist?id=4894882141&creatorId=37847906','https://y.music.163.com/m/playlist?id=2427043875','https://y.music.163.com/m/playlist?id=2364520282','https://y.music.163.com/m/playlist?id=743655586','https://y.music.163.com/m/playlist?id=704150431']
for playlist_url in playlist_urls:
    song_ids = get_songid_from_playlist(playlist_url)
    print(song_ids)
    for i in song_ids:
        print(i)
        download_song_and_lyrics(i)
        time.sleep(random.random()*5)
