import os
import random
import socket
import sys
import traceback
import pyqrcode
import threading
import pyperclip
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from tools import video_compress
from flask import Flask, request, render_template, send_from_directory

app = Flask(__name__)
pc_to_phone = 'pc_to_phone'
phone_to_pc = 'phone_to_pc'
url = ''
qr_code_path = ''

if getattr(sys, 'frozen', False):
    current_path = os.path.dirname(sys.executable)
else:
    current_path = os.path.dirname(os.path.realpath(__file__))


def start_flask():
    global url
    global qr_code_path
    create_directory(pc_to_phone)
    create_directory(phone_to_pc)
    create_file(os.path.join(current_path, 'text.txt'))

    # 获取主机IP
    host_ip = get_host_ip()
    port = get_available_port()
    url = f'http://{host_ip}:{port}'
    qr_code_path = create_qr_code(url)

    # 创建一个事件来同步 Flask 服务器和窗口创建（不再阻塞）
    event = threading.Event()

    def run_app_and_set_event():
        try:
            print(f"Flask server starting at {url}...")
            app.run(host=host_ip, port=port, use_reloader=False)  # use_reloader=False 防止 Flask 重启
        except Exception as e:
            print(f"Flask server error: {e}")
        event.set()  # Flask 启动后通知主线程

    # 在新线程中运行 Flask 应用
    flask_thread = threading.Thread(target=run_app_and_set_event, daemon=True)  # 设置为后台线程
    flask_thread.start()

    # 创建 Tkinter 窗口
    create_window()


def create_window():
    # 确保 qr_code_path 是一个有效的文件路径
    if not os.path.isfile(qr_code_path):
        print(f"Error: The file {qr_code_path} does not exist.")
        return

    print("Creating Tkinter window...")
    root = tk.Tk()
    root.title("文件传输助手")

    # 加载二维码图片
    try:
        img = Image.open(qr_code_path)
        img_tk = ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    # 显示二维码
    label = tk.Label(root, image=img_tk)
    label.pack()

    # 显示IP和端口
    info_label = tk.Label(root, text=f"请使用手机扫描二维码访问: {url}", wraplength=300)
    info_label.pack()

    # 创建一个文本输入框，并设置提示文案
    text_entry = tk.Entry(root, width=40)
    # 在文本输入框中插入提示文案
    text_entry.insert(0, "发送文本内容～")
    text_entry.pack(pady=10)

    def send_text():
        # 获取文本输入框中的内容
        text = text_entry.get()

        # 文本保存路径
        save_text_path = os.path.join(current_path, 'text.txt')

        if text:
            with open(save_text_path, 'w') as f:
                f.write(text)
                messagebox.showinfo('发送成功', '发送成功')

    # 绑定回车键事件
    text_entry.bind('<Return>', lambda event: send_text())

    # 创建一个发送按钮
    send_button = tk.Button(root, text="发送", command=send_text)
    send_button.pack()

    # 关闭窗口时的关闭整个程序
    def on_close():
        root.quit()  # 退出 Tkinter 窗口
        sys.exit()  # 退出 整个程序

    # 绑定窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", on_close)

    # 运行窗口
    root.mainloop()  # 确保 Tkinter 窗口在主线程中运行

def create_qr_code(url):
    qr = pyqrcode.create(url)
    qr_file_path = os.path.join(current_path, 'qrcode.png')
    qr.png(qr_file_path, scale=6)
    # 返回二维码存储路径
    return qr_file_path

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
            print('【文件上传 - 失败】 - - 文件列表为空')
            print('【文本上传 - 失败】 - - 文本内容为空')
            return '文件列表为空、文本内容为空', 403
        elif files[0] and text:
            # 文件列表和文本都不为空，文件和文本都上传
            for file in files:
                file_path = os.path.join(save_file_path, file.filename)
                file.save(file_path)

            with open(save_text_path, 'w') as f:
                f.write(text)

            print(f'【文件上传 - 成功】 - - 文件数量：{len(files)}')
            print(f'【文本上传 - 成功】 - - 文本内容：{text}')
            # 将文本复制到剪贴板
            pyperclip.copy(text)

            return '', 204
        elif files[0] and not text:
            # 文本内容为空，只上传文件
            for file in files:
                file_path = os.path.join(save_file_path, file.filename)
                print(f'【文件上传 - 开始】 - - 文件路径：{file_path}')
                file.save(file_path)
                print(f'【文件上传 - 成功】 - - 文件路径：{file_path}')
                print(f'【文件压缩 - 开始】 - - 文件路径：{file_path}')
                video_compress.process_video(file_path)
            # print('压缩成功====')
            return '', 204
        elif not files[0] and text:
            # 文件列表为空，只上传文本
            with open(save_text_path, 'w') as f:
                f.write(text)
            print(f'【文本上传 - 成功】 - - 文本内容：{text}')
            # 将文本复制到剪贴板
            pyperclip.copy(text)

            return '', 204
        else:
            print('【文件上传 - 失败】 - - 未知错误')
            print('【文本上传 - 失败】 - - 未知错误')
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


if __name__ == '__main__':
    start_flask()
