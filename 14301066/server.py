# server.py
# coding: utf-8
from __future__ import unicode_literals
import socket
import StringIO
import sys
import datetime
import os

class wsgiServer(object):
    socket_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 10

    def __init__(self, address):
        self.socket = socket.socket(self.socket_family, self.socket_type)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(address)
        self.socket.listen(self.request_queue_size)
        host, port = self.socket.getsockname()[:2]
        self.host = host
        self.port = port


    def setApplication(self, application):
        self.application = application

    #服务器监听
    def serverForever(self):
        while 1:
            self.connection, client_address = self.socket.accept()
            self.handelRequest()

    #处理请求
    def handelRequest(self):
        self.request_data = self.connection.recv(1024)
        self.request_lines = self.request_data.splitlines()
        try:
            self.getUrl()
            env = self.getEnv()

            if env['PATH_INFO'][1:].endswith(".html"):
                application = 'app_html'
            else:
                application = 'app_str'

            application = getattr(module, application)
            httpd.setApplication(application)

            app_data = self.application(env, self.startResponse)
            self.finishResponse(app_data)
            print '[{0}] "{1}" {2}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                           self.request_lines[0], self.status)
        except Exception, e:
            pass

    #获取url
    def getUrl(self):
        self.request_dict = {'Path': self.request_lines[0]}
        for itm in self.request_lines[1:]:
            if ':' in itm:
                self.request_dict[itm.split(':')[0]] = itm.split(':')[1]
        self.request_method, self.path, self.request_version = self.request_dict.get('Path').split()

    def getEnv(self):
        env = {
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': StringIO.StringIO(self.request_data),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'REQUEST_METHOD': self.request_method,
            'PATH_INFO': self.path,
            'SERVER_NAME': self.host,
            'SERVER_PORT': self.port,
            'USER_AGENT': self.request_dict.get('User-Agent')
        }
        return env

    def startResponse(self, status, response_headers):
        headers = [
            ('Date', datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')),
            ('Server', 'RAPOWSGI0.1'),
        ]
        self.headers = response_headers + headers
        self.status = status

    def finishResponse(self, app_data):
        try:
            response = 'HTTP/1.1 {status}\r\n'.format(status=self.status)
            for header in self.headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in app_data:
                response += data
            self.connection.sendall(response)
        finally:
            self.connection.close()

#处理静态文件（html)
def app_html(environ, start_response):

    filename = environ['PATH_INFO'][1:]

    if os.path.exists(filename):
        f = open(filename, "r")
        line = f.readline()
        message = line
        while line:
            line = f.readline()
            message = message + line

        status = '200 OK'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return [message]
    else:
        status = '404 NOT FOUND'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return ['404 NOT FOUND:  Not find the resource!']

#处理动态资源
def app_str(environ, start_response):

    status = '200 OK'
    response_headers = [('Content-Type', 'text/plain')]
    start_response(status, response_headers)

    return ['Hello ', environ['PATH_INFO'][1:]]


if __name__ == '__main__':
    port = 7000
    httpd = wsgiServer(('', int(port)))

    print 'Server Serving HTTP service on port {0}....'.format(port)

    module = 'server'
    module = __import__(module)
    httpd.serverForever()
