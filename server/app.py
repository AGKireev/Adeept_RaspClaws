import os
from flask import Flask, Response, send_from_directory
from flask_cors import CORS
import threading
import logging
from camera_opencv import Camera

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebApp:
    def __init__(self):
        logger.info('WebApp: __init__')
        self.app = Flask(__name__)
        
        logger.info('WebApp: CORS')
        CORS(self.app, supports_credentials=True)

        logger.info('WebApp: Camera')
        self.camera = Camera()

        logger.info('WebApp: Routes')
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.setup_routes()
        
        logger.info('WebApp: __init__ done')

    def setup_routes(self):
        @self.app.route('/video_feed')
        def video_feed():
            return Response(self.gen(self.camera),
                            mimetype='multipart/x-mixed-replace; boundary=frame')

        @self.app.route('/api/img/<path:filename>')
        def send_img(filename):
            return send_from_directory(self.dir_path + '/dist/img', filename)

        @self.app.route('/js/<path:filename>')
        def send_js(filename):
            return send_from_directory(self.dir_path + '/dist/js', filename)

        @self.app.route('/css/<path:filename>')
        def send_css(filename):
            return send_from_directory(self.dir_path + '/dist/css', filename)

        @self.app.route('/api/img/icon/<path:filename>')
        def send_icon(filename):
            return send_from_directory(self.dir_path + '/dist/img/icon', filename)

        @self.app.route('/fonts/<path:filename>')
        def send_fonts(filename):
            return send_from_directory(self.dir_path + '/dist/fonts', filename)

        @self.app.route('/<path:filename>')
        def send_gen(filename):
            return send_from_directory(self.dir_path + '/dist', filename)

        @self.app.route('/')
        def index():
            return send_from_directory(self.dir_path + '/dist', 'index.html')

    def gen(self, camera):
        # Generator function that yields video frames
        while True:
            frame = camera.get_frame()
            # Yield a byte string that represents a single frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def mode_select(self, mode_input):
        Camera.modeSelect = mode_input

    def color_find_set(self, h, s, v):
        # Method to set the HSV color for object detection
        self.camera.color_find_set(h, s, v)

    def thread(self):
        # Run the Flask app as a separate thread
        self.app.run(host='0.0.0.0', threaded=True)

    def start_thread(self):
        logger.info('WebApp: start_thread')

        fps_threading = threading.Thread(target=self.thread)
        # Set daemon to False to prevent abrupt termination of the thread
        fps_threading.setDaemon(False)
        fps_threading.start()
        logger.info('WebApp: start_thread done')
