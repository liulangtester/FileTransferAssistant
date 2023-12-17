import os
import random
import socket
import sys
import traceback
import pyqrcode
from tools import video_compress
from flask import Flask, request, render_template, send_from_directory

app = Flask(__name__)
pc_to_phone = 'pc_to_phone'
phone_to_pc = 'phone_to_pc'

if getattr(sys, 'frozen', False):
    current_path = os.path.dirname(sys.executable)
else:
    current_path = os.path.dirname(os.path.realpath(__file__))

def run():
    create_directory(pc_to_phone)
    create_directory(phone_to_pc)
    create_file(os.path.join(current_path, 'text.txt'))
    host_ip = get_host_ip()
    port = 5000
    try:
        if is_port_in_use(port):
            url = pyqrcode.create(f'http://{host_ip}:{port}', version=2, error='L')
            qr_doble(url.text())
            app.run(host=host_ip, port=port)
        else:
            port = get_available_port()
            url = pyqrcode.create(f'http://{host_ip}:{port}', version=2, error='L')
            qr_doble(url.text())

            app.run(host=host_ip, port=port)
    except Exception:
        traceback.print_exc()

def create_directory(directory_name):
    directory = os.path.join(current_path, directory_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

def create_file(path):
    if not os.path.isfile(path):
        with open(path, 'w') as file:
            file.write('')

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def get_available_port(start_port=5000):
    port = start_port
    while True:
        if is_port_in_use(port):
            port = random.randint(2000, 9000)
        else:
            return port

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

@app.route('/get_txt')
def get_txt():
    path = os.path.join(current_path, 'text.txt')
    # 如果文件不存在则创建一个空文件
    create_file(path)
    # 读取文件内容
    with open(path, 'r') as file:
        data = file.read()
    return data

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # 获取文件列表
        files = request.files.getlist('file')
        # 获取文本内容
        text = request.form.get('text')
        # 文件保存路径
        save_file_path = os.path.join(get_directory_path(phone_to_pc))
        # 文本保存路径
        save_text_path = os.path.join(current_path, 'text.txt')
        # 如果文件夹不存在，则创建
        create_directory(pc_to_phone)
        create_directory(phone_to_pc)

        if not files[0] and not text:
            # 文件列表和文本都为空
            print('【文件上传失败】 - - 文件列表为空')
            print('【文本上传失败】 - - 文本内容为空')
            return '文件列表为空、文本内容为空', 403
        elif files[0] and text:
            # 文件列表和文本都不为空，文件和文本都上传
            for file in files:
                file_path = os.path.join(save_file_path, file.filename)
                file.save(file_path)

            with open(save_text_path, 'w') as f:
                f.write(text)

            print(f'【文件上传成功】 - - 文件数量：{len(files)}')
            print(f'【文本上传成功】 - - 文本内容：{text}')
            return '', 204
        elif files[0] and not text:
            # 文本内容为空，只上传文件
            for file in files:
                file_path = os.path.join(save_file_path, file.filename)
                file.save(file_path)
            print(f'【文件上传成功】 - - 文件数量：{len(files)}')
            # video_compress.process_video(file_path, target_fraction=0.5)
            # print('压缩成功====')
            return '', 204
        elif not files[0] and text:
            # 文件列表为空，只上传文本
            with open(save_text_path, 'w') as f:
                f.write(text)
            print(f'【文本上传成功】 - - 文本内容：{text}')
            return '', 204
        else:
            print('【文件上传失败】 - - 未知错误')
            print('【文本上传失败】 - - 未知错误')
            return '未知错误', 403
    else:
        return render_template('upload.html')

@app.route('/download/', defaults={'path': ''})
@app.route('/download/<path:path>', methods=['GET'])
def download_page(path):
    directory = os.path.join(get_directory_path(pc_to_phone), path)
    if not os.path.exists(directory):
        return "Directory not found", 404

    files = []
    directories = []
    for f in os.listdir(directory):
        full_path = os.path.join(directory, f)
        file_info = {'name': f, 'is_dir': os.path.isdir(full_path), 'path': os.path.join(path, f)}
        if not file_info['is_dir']:
            size_bytes = os.path.getsize(full_path)
            if size_bytes >= 1024 * 1024 * 1024:  # 大于等于 1 GB
                file_info['size'] = round(size_bytes / (1024 * 1024 * 1024), 2)  # 转换为 GB
                file_info['unit'] = 'GB'
            else:
                file_info['size'] = round(size_bytes / (1024 * 1024), 2)  # 转换为 MB
                file_info['unit'] = 'MB'
        if file_info['is_dir']:
            directories.append(file_info)
        else:
            files.append(file_info)

    items = directories + files  # 先文件夹后文件
    return render_template('download.html', files=items, current_path=path)


@app.route('/download/file/<path:filename>', methods=['GET'])
def download_file(filename):
    try:
        directory = get_directory_path(pc_to_phone)
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception:
        traceback.print_exc()

def get_directory_path(directory_name, path=''):
    return os.path.join(current_path, directory_name, path)


def qr_doble(txt):
    print(txt.replace('0', '\U00002588\U00002588').replace('1', '  '))

if __name__ == '__main__':
    run()
