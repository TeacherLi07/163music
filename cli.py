import curses
import time
import random
import requests
import os
from tqdm import tqdm
from io import BytesIO
import math
from datetime import timedelta

class MusicDownloaderCLI:
    def __init__(self):
        self.playlists_downloaded = 0
        self.songs_downloaded = 0
        self.total_playlists = 100  # 假设总歌单数
        self.total_songs = 1000      # 假设总歌曲数
        self.current_playlist = {
            'name': '当前歌单',
            'id': '123456',
            'total_songs': 10,
            'songs_downloaded': 0
        }
        self.downloading_song = {
            'name': '正在下载歌曲',
            'id': '654321',
            'progress': 0,
            'size': 0,
            'speed': 0,
            'eta': 0
        }
        self.waiting_playlists = 5
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.proxies = None

    def download_song(self, url, save_path):
        # 获取文件大小
        response = requests.head(url, headers=self.headers, proxies=self.proxies)
        file_size = int(response.headers.get('content-length', 0))
        self.downloading_song['size'] = file_size / 1024 / 1024  # 以MB为单位
        downloaded_size = 0
        
        # 下载文件并展示进度条
        start_time = time.time()
        with requests.get(url, stream=True, headers=self.headers, proxies=self.proxies) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新进度信息
                        elapsed_time = time.time() - start_time
                        self.downloading_song['progress'] = (downloaded_size / file_size) * 100
                        self.downloading_song['speed'] = downloaded_size / 1024 / elapsed_time
                        remaining_size = file_size - downloaded_size
                        self.downloading_song['eta'] = remaining_size / 1024 / self.downloading_song['speed'] if self.downloading_song['speed'] > 0 else float('inf')
                        time.sleep(0.1)  # 模拟下载延迟

    def format_eta(self, seconds):
        return str(timedelta(seconds=int(seconds)))

    def progress_bar(self, progress, total):
        bar_length = 30  # 进度条的长度
        filled_length = int(bar_length * progress // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        return f"[{bar}] {progress}/{total}"

    def update_display(self, stdscr):
        stdscr.clear()
        # 彩色输出
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        
        stdscr.addstr(0, 0, f"已下载歌单数: ", curses.color_pair(1))
        stdscr.addstr(0, 16, f"{self.playlists_downloaded}")
        
        stdscr.addstr(1, 0, f"已下载歌曲数: ", curses.color_pair(1))
        stdscr.addstr(1, 16, f"{self.songs_downloaded}")
        
        stdscr.addstr(2, 0, f"数据库中全部歌单数: {self.total_playlists}", curses.color_pair(3))
        stdscr.addstr(3, 0, f"数据库中全部歌曲数: {self.total_songs}", curses.color_pair(3))
        
        stdscr.addstr(5, 0, f"正在遍历的歌单: {self.current_playlist['name']} (ID: {self.current_playlist['id']})", curses.color_pair(2))
        stdscr.addstr(6, 0, f"已下载歌曲数: {self.current_playlist['songs_downloaded']}/{self.current_playlist['total_songs']}")
        
        stdscr.addstr(8, 0, f"正在下载的歌曲: {self.downloading_song['name']} (ID: {self.downloading_song['id']})", curses.color_pair(2))
        stdscr.addstr(9, 0, f"下载进度: {self.downloading_song['progress']:.2f}%")
        
        # 进度条
        stdscr.addstr(10, 0, self.progress_bar(self.downloading_song['progress'], 100))
        
        # 显示下载速度和 ETA
        stdscr.addstr(12, 0, f"速度: {self.downloading_song['speed']:.2f} KB/s", curses.color_pair(1))
        stdscr.addstr(13, 0, f"ETA: {self.format_eta(self.downloading_song['eta'])}", curses.color_pair(1))
        
        stdscr.addstr(15, 0, f"等候下载歌单数: {self.waiting_playlists}", curses.color_pair(3))
        
        stdscr.refresh()

    def run(self, stdscr):
        curses.curs_set(0)
        song_url = "http://music.163.com/song/media/outer/url?id=123456.mp3"  # 替换为实际的 MP3 URL
        save_path = "song.mp3"
        
        while self.songs_downloaded < self.total_songs:
            self.update_display(stdscr)
            
            # 下载歌曲
            self.download_song(song_url, save_path)
            self.songs_downloaded += 1
            self.current_playlist['songs_downloaded'] += 1
            
            if self.current_playlist['songs_downloaded'] >= self.current_playlist['total_songs']:
                self.playlists_downloaded += 1
                self.current_playlist['songs_downloaded'] = 0  # 重置当前歌单下载计数
                self.current_playlist['name'] = f"新歌单{self.playlists_downloaded + 1}"
                self.current_playlist['id'] = str(123456 + self.playlists_downloaded)  # 假设新ID
            

if __name__ == "__main__":
    cli = MusicDownloaderCLI()
    curses.wrapper(cli.run)
