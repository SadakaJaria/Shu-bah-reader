#!/usr/bin/env python3
"""خادم تطوير محلّي.

صفحات المصحف مخزّنة مضغوطةً بـBrotli (‎.svg.br)، والمتصفّح يفكّها من تلقائه
متى وصلته ترويسة Content-Encoding: br. خادم http.server العادي لا يرسلها،
فتصل الصفحة بايتاتٍ لا معنى لها. هذا الخادم يرسلها — وVercel يفعل المثل
عبر vercel.json.

    python3 serve.py            # http://127.0.0.1:8000
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith('.svg.br'):
            self.send_header('Content-Encoding', 'br')
            self.send_header('Content-Type', 'image/svg+xml; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, *a):
        pass


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
print('http://127.0.0.1:%d' % port)
ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
