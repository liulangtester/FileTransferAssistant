import sys
import traceback
import cv2
import subprocess
import os


def remove_black_borders(input_file, analysis_duration=2):
    """
    使用FFMPEG的cropdetect过滤器从视频中删除黑边
    :param input_file: 需要处理的视频文件的路径（字符串）
    :param analysis_duration: 用于分析黑边的视频持续时间（以秒为单位）（整数）
    :return: 裁剪参数（字符串），格式为 "宽度:高度:x:y"
    """

    # ffmpeg_command = [
    #     "ffmpeg", "-i", input_file, "-t", str(analysis_duration),
    #     "-vf", "cropdetect", "-f", "null", "-"
    # ]

    if getattr(sys, 'frozen', False):
        current_path = os.path.dirname(sys.executable)
    else:
        current_path = os.path.dirname(os.path.realpath(__file__))
    directory = os.path.join(current_path, 'ffmpeg')

    ffmpeg_command = [
        directory, "-i", input_file, "-t", str(analysis_duration),
        "-vf", "cropdetect", "-f", "null", "-"
    ]

    try:
        output = subprocess.check_output(ffmpeg_command, stderr=subprocess.STDOUT)
        last_line = [line for line in output.decode().split('\n') if "crop=" in line][-1]
        crop_params = last_line.split("crop=")[1].split(" ")[0]
        w, h, x, y = map(int, crop_params.split(":"))
        w = w - w % 2
        h = h - h % 2
        crop_params = f"{w}:{h}:{x}:{y}"
        return crop_params
    except Exception as e:
        print("remove_black_borders:异常 ", e)
        return None


def get_video_duration(input_file):
    """
    返回视频的持续时间
    :param input_file: 需要处理的视频文件的路径（字符串）
    :return: 视频的持续时间（以秒为单位）（浮点数）
    """
    cap = cv2.VideoCapture(input_file)
    duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
    return duration


def get_video_resolution(input_file):
    """
    返回视频的分辨率（宽度和高度）
    :param input_file: 需要处理的视频文件的路径（字符串）
    :return: 元组，包含视频的宽度和高度（整数）
    """
    if getattr(sys, 'frozen', False):
        current_path = os.path.dirname(sys.executable)
    else:
        current_path = os.path.dirname(os.path.realpath(__file__))
    directory = os.path.join(current_path, 'ffprobe')

    ffprobe_command = [directory, "-v", "error", "-select_streams", "v:0",
                       "-show_entries", "stream=width,height", "-of",
                       "default=noprint_wrappers=1:nokey=1", input_file]
    try:
        output = subprocess.check_output(ffprobe_command).decode()
    except subprocess.CalledProcessError as e:
        print("Error running ffprobe: ", e)
        return

    output = output.strip()
    if not output:
        print("Invalid output from ffprobe")
        return

    width, height = output.split("\n")
    try:
        width = int(width)
        height = int(height)
    except ValueError:
        print("Invalid width/height in ffprobe output")
        return

    return width, height


def apply_crop(input_file, crop_params):
    """
    将裁剪应用于视频
    :param input_file: 需要处理的视频文件的路径（字符串）
    :param crop_params: 裁剪参数（字符串），格式为 "宽度:高度:x:y"
    :return: 裁剪后的视频的路径（字符串）
    """
    output_file = os.path.splitext(input_file)[0] + "_cropped.mp4"
    print('apply_crop', output_file)
    if getattr(sys, 'frozen', False):
        current_path = os.path.dirname(sys.executable)
    else:
        current_path = os.path.dirname(os.path.realpath(__file__))
    directory = os.path.join(current_path, 'ffmpeg')
    ffmpeg_command = [directory, "-i", input_file, "-vf", f"crop={crop_params}", output_file]
    try:
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error applying crop: {e}")
    return output_file


def convert_to_mp4(input_file, output_file):
    """
    将输入文件转换为MP4格式
    :param input_file: 需要转换的视频文件的路径（字符串）
    :param output_file: 转换后的MP4文件的路径（字符串）
    """
    print('convert_to_mp4', input_file)
    print('convert_to_mp4', output_file)
    if getattr(sys, 'frozen', False):
        current_path = os.path.dirname(sys.executable)
    else:
        current_path = os.path.dirname(os.path.realpath(__file__))
    directory = os.path.join(current_path, 'ffmpeg')
    ffmpeg_command = [directory, "-i", input_file, "-c:v", "libx264", "-c:a", "aac", output_file]
    try:
        subprocess.run(ffmpeg_command, check=True)
        print('Conversion to MP4 successful')
    except subprocess.CalledProcessError as e:
        print(f"Error converting to MP4: {e}")


def compress_video(input_file, target_fraction):
    """
    将视频文件压缩到其原始大小的指定比例
    :param input_file: 需要压缩的视频文件的路径（字符串）
    :param target_fraction: 目标大小为原始大小的比例（浮点数）
    :return: 压缩后的视频的路径（字符串）
    """
    output_file = f'{input_file.split(".")[0]}_compressed.mp4'
    print('compress_video', input_file)
    print('compress_video', output_file)
    original_size = os.path.getsize(input_file)
    duration = get_video_duration(input_file)
    target_size = original_size * target_fraction / duration
    width, height = get_video_resolution(input_file)
    target_bitrate = int((target_size * 8) / 60) / 20

    fast_encode = True
    if fast_encode:
        preset = "ultrafast"
    else:
        preset = "medium"

    if getattr(sys, 'frozen', False):
        current_path = os.path.dirname(sys.executable)
    else:
        current_path = os.path.dirname(os.path.realpath(__file__))
    directory = os.path.join(current_path, 'ffmpeg')

    ffmpeg_command = [directory, "-i", input_file,
                      "-c:v", "libx264",
                      "-b:v", "{}k".format(target_bitrate),
                      "-s", "{}x{}".format(width, height),
                      "-preset", preset, "-r", "30", "-c:a", "aac", "-b:a", "32K",
                      output_file]

    print("Running ffmpeg command: {}".format(" ".join(ffmpeg_command)))
    try:
        subprocess.run(ffmpeg_command)
        print("Compression completed!")
    except Exception as e:
        print("ffmpeg compress failed: {}".format(e))
    return output_file

# 判断是否为视频文件
def is_video_file(file_path):
    # 提取文件扩展名
    extension = os.path.splitext(file_path)[1]
    # 定义视频文件扩展名的列表
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    # 检查文件扩展名是否在视频文件扩展名的列表中
    if extension in video_extensions:
        return True
    else:
        return False

# 获取文件大小
def get_file_size(file_path):
    """
    返回文件的大小
    :param file_path: 文件的路径（字符串）
    :return: 文件的大小，单位是兆字节（MB）（浮点数）
    """
    try:
        size = os.path.getsize(file_path) / (1024 * 1024)
        return size
    except OSError as e:
        print(f"Error getting file size: {e}")
        return None

def process_video(input_file):
    """
    处理视频，包括转换格式、删除黑边、压缩
    :param input_file: 需要处理的视频文件的路径（字符串）
    :param target_fraction: 目标大小为原始大小的比例（浮点数）
    :return: 处理后的视频的路径（字符串）
    """
    # 如果是视频文件，才处理
    if is_video_file(input_file):
        print('process_video', input_file)
        if not (input_file.endswith('.mp4') or input_file.endswith('.mov')):
            temp_output = os.path.splitext(input_file)[0] + "_temp.mp4"
            convert_to_mp4(input_file, temp_output)
            input_file = temp_output
        print("去黑边1")
        print("input_file", input_file)
        crop_params = remove_black_borders(input_file)
        print("去黑边2")
        if crop_params:
            # 去黑边
            print("裁剪应用1")
            input_file = apply_crop(input_file, crop_params)
            print("裁剪应用2")

        if os.path.getsize(input_file) < 10 * 1024 * 1024:  # 10MB in bytes
            print("视频转换格式及去黑边后文件大小<10M，无需压缩")
            return input_file
        else:
            try:
                print("压缩1")
                # output_file_compress = compress_video(input_file, target_fraction)
                size = get_file_size(input_file)
                if size is not None:
                    if size <= 20:
                        output_file_compress = compress_video(input_file, 0.5)
                    elif 20 < size <= 30:
                        output_file_compress = compress_video(input_file, 10 / size)
                    elif 30 < size <= 40:
                        output_file_compress = compress_video(input_file, 10 / size)
                    else:
                        output_file_compress = compress_video(input_file, 0.2)
                print("压缩2")
                return output_file_compress
            except Exception:
                traceback.print_exc()


# if __name__ == '__main__':
#     input_file = "phone_to_pc/RPReplay_Final1702747412222.mov"
#     process_video(input_file, target_fraction=0.3)