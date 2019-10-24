from gevent.pywsgi import WSGIServer
from wear2bmp import app
from wear2bmp import quitEvent
from wear2bmp import managerThread
import threading

http_server = WSGIServer(('0.0.0.0',5000), app)
try:
    http_server.serve_forever()
except KeyboardInterrupt as e:
    print("received KeyboardInterrupt", e)
    quitEvent.set()

