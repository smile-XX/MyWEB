# coding:utf-8
import socket
import threading
import re
import sys
from multiprocessing import Process

HTML_ROOT_DIR = "./html"
WSGI_PYTHON_DIR = "./wsgipython"


class HttpServer(object):
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 确保绑定的地址不冲突

    def start(self):
        self.server_socket.listen(10)
        while True:
            client_socket, client_addr = self.server_socket.accept()
            print("[%s, %s]用户连接了WEB SERVER!" % client_addr)
            handle_client_thread = Process(target=self.handle_client, args=(client_socket, ))
            handle_client_thread.start()
            client_socket.close()

    def handle_client(self, client_socket):
        """处理用户端请求"""
        request_data = client_socket.recv(1024)
        print("Request Data:", request_data)
        request_lines = request_data.splitlines()
        for line in request_lines:
            print(line)  # 打印请求报文
        request_start_line = request_lines[0]
        # "GET / HTTP/1.1"
        # 获取用户端传过来的文件名
        file_name = re.match(r"\w+ +(/[^ ]*) ", request_start_line.decode("utf-8")).group(1)
        method = re.match(r"(\w+) +/[^ ]* ", request_start_line.decode("utf-8")).group(1)
        if file_name.endswith(".py"):
            try:
                # 使用WSGI引入要执行的python文件
                m = __import__(file_name[1:-3])
            except Exception:
                self.response_headers = "HTTP/1.1 404 Not Found\r\n"
                response_body = "not found"
            else:
                env = {
                    "PATH_INFO": file_name,
                    "METHOD": method
                }
                response_body = m.application(env, self.start_response)
            response = self.response_headers + "\r\n" + response_body
        else:
            if "/" == file_name:
                file_name = "/index.html"
            try:
                file = open(HTML_ROOT_DIR + file_name, "rb")
            except IOError:
                response_start_line = "HTTP/1.1 404 Not Found\r\n"
                response_headers = "Server: My server\r\n"
                response_body = "not found"
            else:
                file_data = file.read()
                file.close()
                response_start_line = "HTTP/1.1 200 OK\r\n"
                response_headers = "Server: My server\r\n"
                response_body = file_data.decode("utf-8")
            response = response_start_line + response_headers + "\r\n" + response_body
        client_socket.send(bytes(response.encode("utf-8")))

    def start_response(self, status, headers):
        """处理py文件响应状态码和头部信息
           status = 200 OK
           headers = {
                ("Content-Type", "text/plain")
           }

        """
        response_headers = "HTTP/1.1 " + status + "\r\n"
        for header in headers:
            response_headers += "%s: %s\r\n" % header
        self.response_headers = response_headers

    def bind(self, port):
        self.server_socket.bind(("", port))


def main():
    # 将WSGI路径插入系统路径中
    sys.path.insert(1, WSGI_PYTHON_DIR)
    http_server = HttpServer()
    http_server.bind(8000)
    http_server.start()


if __name__ == "__main__":
    main()




