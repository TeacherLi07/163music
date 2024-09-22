import requests
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

# 假设你有这些函数
# get_songid_from_playlist(playlist_id) -> 返回歌单的歌曲ID列表
# playlists_id -> 一个列表，存储待下载的歌单ID

console = Console()

def download_song(song_id):
    song_url = f"https://music.163.com/song?id={song_id}"
    try:
        response = requests.get(song_url)
        if response.status_code == 200:
            # 假设将下载的MP3文件保存
            with open(f"{song_id}.mp3", 'wb') as f:
                f.write(response.content)
            return True
        else:
            return False
    except Exception as e:
        console.print(f"下载歌曲 {song_id} 失败: {e}")
        return False

def cli_interface(playlists_id):
    total_songs_downloaded = 0
    total_songs_in_db = 0  # 可以从数据库查询
    playlists_queue = len(playlists_id)

    # 创建进度条
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:

        for playlist_id in playlists_id:
            playlist_songs = get_songid_from_playlist(playlist_id)
            playlist_total_songs = len(playlist_songs)
            downloaded_songs_in_playlist = 0

            playlist_task = progress.add_task(f"遍历歌单 {playlist_id}...", total=playlist_total_songs)
            
            for song_id in playlist_songs:
                song_task = progress.add_task(f"下载歌曲 {song_id}...", total=100)
                
                # 下载歌曲并更新进度
                if download_song(song_id):
                    downloaded_songs_in_playlist += 1
                    total_songs_downloaded += 1

                progress.advance(playlist_task, 1)
                progress.update(song_task, completed=100)
                time.sleep(0.1)  # 模拟一点延迟来观察下载过程

            # 歌单处理完成
            progress.remove_task(playlist_task)
            playlists_queue -= 1

            console.print(f"歌单 {playlist_id} 下载完成, 已下载 {downloaded_songs_in_playlist}/{playlist_total_songs} 首歌曲.")
        
        console.print(f"全部歌单下载完成，总共下载了 {total_songs_downloaded} 首歌曲。")

if __name__ == "__main__":
    playlists_id = [...]  # 需要下载的歌单ID列表
    cli_interface(playlists_id)
