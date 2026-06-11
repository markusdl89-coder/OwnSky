import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class RenderPingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("OwnSky Alpha: На связи.".encode("utf-8"))

    def log_message(self, format, *args):
        pass # Отключаем спам-логи в консоль смартфона

def run_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), RenderPingHandler)
    print(f"[System] Веб-сервер запущен на порту {port}")
    server.serve_forever()

def start_hosting():
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Запуск в отдельном потоке daemon=True
    # Теперь сервер не будет блокировать запуск бота
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print("[System] Фоновый поток сервера успешно запущен.")
