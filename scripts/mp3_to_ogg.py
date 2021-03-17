'''
需要安装两个依赖，pydub和ffmpeg
'''
import argparse
import glob
from pydub import AudioSegment


def trans_mp3_ogg(bookname):
    pattern = f"../library/{bookname}/mp3/1/*.mp3"
    mp3_path_list = glob.glob(pattern)
    count = 0
    for path in mp3_path_list:
        song = AudioSegment.from_mp3(path)
        path_name = path.split('/')[-1].split('.')[0]
        out_path = f'../library/{bookname}/ogg/{path_name}.ogg'
        song.export(out_path, format='ogg')
        count += 1
        print('完成处理：', path_name, '.mp3', count, '/', len(mp3_path_list))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bookname", help="输入需要转换的MP3文件所在文件夹名称")
    args = parser.parse_args()
    trans_mp3_ogg(args.bookname)
