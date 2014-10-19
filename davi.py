#!/usr/bin/python
import os
import re
import sys
import glob
import urllib
import socket


class Davi():

    version = '0.4.0'
    debug = False
    port = 9000

    def __init__(self):
        if '--version' in sys.argv:
            print(self.version)
            sys.exit()
        if '--debug' in sys.argv:
            self.debug = True

        self.sock = None
        self.conn = None
        self.addr = None
        self.error = None
        self.is_dir = False
        self.is_windows = 'uname' not in dir(os)

        self.start()

    def start(self):
        print('======================================')
        print(' Davi micro HTTP server v' + str(self.version))
        print('======================================')
        print('')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.sock.bind(('', self.port))
            self.sock.listen(5)
        except:
             print('[Error] Unable to listen on port ' + str(self.port) + '. Exiting...\n')
             sys.exit(1)

        self.document_root = os.path.dirname(os.path.abspath(__file__))
        print('Directory: ' + str(self.document_root))
        print('URL: http://localhost:' + str(self.port))
        print('\nDavi is up and running!\n')

        while True:
            self.get_request()

    def get_request(self):
        self.error = None
        self.conn, self.addr = self.sock.accept()
        if self.debug:
            print 'Connected by', self.addr

        self.request = self.conn.recv(1024)
        self.app_path = self.request.split('\n')[0].replace('\r', '')
        self.app_path = re.sub('^[a-zA-Z]+ (.*) HTTP/[0-9\.]+$', r'\1', self.app_path)
        self.app_path = re.sub('^/', '', self.app_path)
        self.app_path = re.sub('^([^\?|#]+)[^\?|#]?.*$', r'\1', self.app_path)
        self.app_path = urllib.unquote(self.app_path)

        if self.is_windows:
            self.app_path = self.app_path.decode('utf8').encode('cp1252')
        
        davi_internals = '[.[.[_davi_].].]/'
        if self.app_path[:17] == davi_internals:
            self.app_path = self.app_path.replace(davi_internals, '')
            self.requested_path = self.get_asset(self.app_path)
            self.runtime_root = os.path.dirname(self.requested_path)
        else:
            self.requested_path = os.path.join(self.document_root, self.app_path)
            self.runtime_root = self.document_root

        self.app_path_ext = re.sub('^.*\.([^\.]+)$', r'\1', self.app_path)
        self.is_dir = os.path.isdir(self.requested_path)

        headers = self.request.split('\n')
        for l in headers:
            l = l.replace('\r', '').lower()
            l = l.split(':', 1)
            if l[0] == 'host':
                self.app_host = l[1].strip()
                os.environ['HTTP_HOST'] = self.app_host

        if self.debug:
            print(self.request)
            print('=====================')

        self.respond()

    def get_content(self):
        if self.app_path:
            try_files = [self.app_path]
        else:
            try_files = ['index.htm', 'index.html', 'index.php']

        content = None
        for target in try_files:
            if not content:
                abstarget = os.path.join(self.runtime_root, target)
                if os.path.exists(abstarget):
                    print('File found: ' + abstarget)

                    if re.sub('^.*\.([^\.]+)$', r'\1', target) == 'php':
                        print('PHP file detected...')
                        content = os.popen('php ' + abstarget).read()
                    else:
                        if os.path.isdir(abstarget):
                            content = None
                        else:
                            with open(abstarget, 'rb') as f:
                                content = f.read()

        if not content:
            if self.app_path and not self.is_dir:
                self.error = 404
                title = 'Not found'
                content = 'File not found: <span class="code">' + self.requested_path + '</span>'
                print('File not found: ' + self.requested_path)
            else:
                title = 'Index of /' + self.app_path
                content = self.directory_index()
            content = self.render(title, content)

        return content

    def get_response_status(self):
        status = 'HTTP/1.1 '
        if not self.error:
            status += '200 OK'
        elif self.error == 404:
            status += '404 Not found'
        else:
            status += '500 Internal server error'

        return status

    def respond(self):
        content = self.get_content()
        response = self.get_response_status() + '\n'
        response += 'Content-type: ' + self.get_mime_type() + '\n'
        response += 'Server: Davi v' + str(self.version) + '\n'
        response += 'Content-length: ' + str(len(content)) + '\n'
        response += 'Connection: close\n'
        response += '\n'

        if self.debug:
            print(response)
            print('=====================')
            print(content)

        try:
            self.conn.send(response)
            self.conn.send(content)
        except:
            pass

        self.conn.close()

    def get_mime_type(self):
        if self.error in [400, 500]:
            mime_type = 'text/plain'
        else:
            if self.is_dir:
                mime_type = 'text/html'
            else:
                mime_type = os.popen('file --mime-type ' + os.path.join(self.runtime_root, self.app_path)).read()
                mime_type = re.sub('^([^:]+): (.*)$', r'\2', mime_type).strip('\n')


        charset = 'windows-1252' if self.is_windows else 'utf-8'
        mime_type += '; charset=' + charset

        return mime_type

    def render(self, title, content):
        if os.path.exists(self.get_asset('template.html')):
            with open(self.get_asset('template.html'), 'r') as f:
                tpl = f.read()
            tpl = tpl.replace('{{CHARSET}}', 'windows-1252' if self.is_windows else 'utf-8')
            tpl = tpl.replace('{{TITLE}}', title)
            tpl = tpl.replace('{{CONTENT}}', content)
        else:
            self.error = 500
            tpl = '[Error] Template not found: ' + self.get_asset('template.html') + '\n'
            tpl += '[Error] ' + content

        return tpl

    def get_asset(self, filename):
        filename = os.path.join('assets', filename)
        if hasattr(sys, '_MEIPASS'):
            os.chdir(sys._MEIPASS)
            filename = os.path.join(sys._MEIPASS, filename)
        else:
            filename = os.path.join(os.path.dirname(__file__),  filename)
        return filename

    def directory_index(self):
        base = self.app_path
        if base:
            base = '/' + base
        base = re.sub('/$', '', base)

        html = '<div id="DirectoryIndex">'
        icon_up = '<span class="icon folder"></span>'
        icon_file = '<span class="icon file"></span>'
        icon_folder = '<span class="icon folder"></span>'

        if self.app_path:
            html += '<a href="' + base + '/..">' + icon_up + ' <span class="t">..</span></a>'
        files = glob.glob(self.requested_path + '/*')
        for ff in files:
            f = os.path.basename(ff)
            flag = icon_folder if os.path.isdir(ff) else icon_file
            html += '<a href="' + base + '/' + f +'">' + flag + ' <span class="t">' + f + '</span></a>'

        html += '</div>'
        return html


if __name__ == '__main__':
    Davi()