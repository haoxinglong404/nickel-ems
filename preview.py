"""本地预览服务器。双击或命令行 py preview.py 启动。

启动后自动打开浏览器到 http://localhost:8000/?preview=1
预览模式下，本地 SEED_EQUIPMENTS 里的字段会"盖"在云端数据上显示，
方便 push 前看效果。关闭窗口即停止。
"""
import http.server
import socketserver
import webbrowser
import threading
import os
import sys

PORT = 8000
URL = f'http://localhost:{PORT}/?preview=1'

# 切到脚本所在目录（保证 index.html 能被访问到）
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    webbrowser.open(URL)

threading.Timer(1.2, open_browser).start()

Handler = http.server.SimpleHTTPRequestHandler

print('=' * 60)
print(f' Nickel EMS · 本地预览服务器')
print('=' * 60)
print(f' 地址: {URL}')
print(f' 工作目录: {os.getcwd()}')
print(' 关闭此窗口或按 Ctrl+C 停止')
print('=' * 60)

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print('\n已停止')
    sys.exit(0)
except OSError as e:
    if 'Address already in use' in str(e) or '10048' in str(e):
        print(f'\n❌ 端口 {PORT} 已被占用。请先关掉旧的预览窗口，或修改 preview.py 里的 PORT。')
        input('按回车退出...')
        sys.exit(1)
    raise
