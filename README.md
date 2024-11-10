背景：平时测试会用到很多台手机，每次要将文件传输到PC端需要使用第三方APP（微信、QQ、如流等）作为媒介传输文件，太麻烦了，也不是每台手机都会安装微信、QQ啥的。我需要的是轻量化的文件传输工具，先去网上找了下，发现有类似的工具，但是如视频需要自动压缩到10M以内等需求还是不能满足，所以决定还是自己写一个~

安装依赖：
* pip install -r requirements.txt

脚本打包：
* 安装打包依赖：pip install pyinstaller
* 打包命令：
  * win：不显示控制台
    * pyinstaller --onefile --windowed --add-binary 'tools/ffmpeg.exe;.' --add-binary 'tools/ffprobe.exe;.' app.py --add-data 'templates/upload.html:templates' --add-data 'templates/download.html:templates'
  * mac：不显示控制台并且指定应用图标
    * pyinstaller --onefile --windowed --icon=app_icon.icns --add-binary 'tools/ffmpeg.exe:.' --add-binary 'tools/ffprobe.exe:.' --add-data 'templates/upload.html:templates' --add-data 'templates/download.html:templates' app.py



功能简介：
基于局域网的文件传输助手，手机和电脑需要在同一个局域网下。
* 文件传输
  * 手机传文件到PC端
  * 手机获取PC端文件
* 文本传输
  * 手机传文本到PC端
  * 手机获取PC端文本

脚本使用：
* 脚本放在合适目录，双击启动
* 启动后会在脚本所在目录创建两个目录和一个文件
  * 两个目录：
    * pc_to_phone：手机端可以访问的文件目录
    * phone_to_pc：手机端上传的文件放置目录
  * 一个文件：
    * text.txt：手机端上传的文本放置文件，手机端获取的文本也是取自该文件
* 启动后界面如下图所示

* 两种访问页面方式
  * 手机扫描二维码
  * 浏览器输入界面显示的 ip:port
* 手机访问的页面如下图所示
  * 获取文本并复制：将text.txt文件的内容显示在文本输入框内，并复制文本输入框的内容
  * 复制：复制文本输入框的内容
  * 删除文本：删除文本输入框中的内容


功能详细介绍：
* 文件上传
  * 选择一个或多个文件，点击上传，上传成功的文件存储在目录phone_to_pc中
  * 上传进度

* 文本上传
  * 输入文本内容，点击上传，上传成功的文本内容存储在文件text.txt中，并且自动复制到剪切板

* 文件下载
  * PC端将需要传输到手机端的文件放入pc_to_phone目录中，手机端点击底部按钮切换到下载页面下载

* 文本下载
  * PC端将需要传输到手机端的文本内容放入text.txt中
  * 手机端点击获取文本icon，text.txt文件的内容就会显示在文本输入框内，并且自动复制到剪切板
  * 如果自动复制失败，可以手动点击复制icon
