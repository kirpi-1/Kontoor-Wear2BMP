import os, stat
from flask import Flask, flash, request, redirect, url_for, send_file, Response
from werkzeug.utils import secure_filename
import shutil
import threading
import queue
import time
import atexit

UPLOAD_FOLDER = './tmp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'zip', '7z'}
num_files = 0
managerThread = threading.Thread()
commandQueue = queue.Queue()
clientRequestStatus = dict()
clientRequestStatusLock = threading.Lock()
quitEvent = threading.Event()
def createApp():
    app = Flask(__name__)
    global managerThread
    global commandQueue
    global clientRequestStatus
    global clientRequestStatusLock

    def manageQueue():
        while not quitEvent.wait(5.0):
            #print("checking queue, is there a request?", not commandQueue.empty())
            if not commandQueue.empty():  # execute next item in queue
                args = commandQueue.get()
                clientDir = args['clientDir']
                clientRequestStatusLock.acquire()
                clientRequestStatus[args['ip']] = 'running'
                clientRequestStatusLock.release()
                print("========================================")
                print("Processing request from: ", args['ip'])
                print("========================================")
                print(args['command'])
                rval = os.system(args['command'])
                print("========================================")
                print("Finished processing request from: ", args['ip'])
                print("returned value of ", rval)
                print("========================================")
                clientRequestStatusLock.acquire()
                if rval == 0:
                    clientRequestStatus[args['ip']] = 'finished'
                else:
                    clientRequestStatus[args['ip']] = "Error: " + str(rval)
                #print("client request status is now\n\t",clientRequestStatus)
                clientRequestStatusLock.release()
        return 0

    managerThread = threading.Thread(target=manageQueue)
    managerThread.start()

    return app
try:
    app = createApp()
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['USE_CPU'] = False
    app.config['NET_NAME'] = "whiskersBW3"
except KeyboardInterrupt:
    print("got a keyboard interrupt")


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return redirect("./index.html")

@app.route("/hello")
def helloWorld():
    return "Hello World"

@app.route("/GETtest")
def getTest():
    return "successfully pinged"

@app.route('/App',methods=['POST'])
def upload_file():

    files = request.files.getlist('images')
    ip = request.remote_addr
    clientDir = app.config['UPLOAD_FOLDER'] + '/' + ip
    if not os.path.isdir(app.config['UPLOAD_FOLDER']):
        os.mkdir(app.config['UPLOAD_FOLDER'])

    if os.path.isdir(clientDir):
        for f in os.listdir(clientDir):
            p = os.path.join(clientDir, f)
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
    else:
        os.mkdir(clientDir)
    if not os.path.isdir(os.path.join(clientDir, "images")):
        os.mkdir(os.path.join(clientDir, "images"))
    imagesDir = os.path.join(clientDir, "images")

    for f in files:
        name = secure_filename(f.filename)
        name = os.path.basename(name)
        # if this filename already exists
        path = os.path.join(imagesDir, name)
        if os.path.isfile(path):
            i = 0
            tmp, ext = os.path.splitext(name)
            while os.path.isfile(path):  # add "_i" until it is unique filename
                i += 1
                path = os.path.join(clientDir, tmp + "_{0}{1}".format(i, ext))
                print(path)
            name = tmp + "_" + str(i) + ext
        f.save(os.path.join(imagesDir, name))
    dataroot = imagesDir
    netname = app.config['NET_NAME']
    command = ("python ./pix2pix/test.py --dataroot " + dataroot + " " +
               "--results_dir " + clientDir+"/results/ "
               "--name " + netname + " --model test --netG unet_1024 --direction AtoB --dataset_mode single " +
               "--loadSize 1024 --fineSize 1024 --norm batch --use_upsample_conv --input_nc 1 --output_nc 1")
    if app.config["USE_CPU"]:
        command = command + " --gpu_ids -1"
    args = {'command': command, 'ip': ip, 'clientDir': clientDir, 'imagesDir': imagesDir}
    print("placing command in queue")
    commandQueue.put(args)
    clientRequestStatusLock.acquire()
    clientRequestStatus[ip] = 'received'
    print(clientRequestStatus)
    clientRequestStatusLock.release()
    return "received files"

@app.route('/CheckStatus',methods=['GET'])
def check_status():
    ip = request.remote_addr

    # check the status of their request and return
    clientRequestStatusLock.acquire()
    status = 'Not Found'
    if ip in clientRequestStatus:
        status = clientRequestStatus[ip]
    clientRequestStatusLock.release()
    return status

@app.route('/download',methods=['GET'])
def download_file():
    ip = request.remote_addr
    clientDir = app.config['UPLOAD_FOLDER'] + '/' + ip
    imagesDir = os.path.join(clientDir, "images")
    outputFolder = os.path.join(clientDir, "results/whiskersBW3/test_latest/images")
    # if their request is finished, return zip data to them
    files = [f for f in os.listdir(outputFolder) if os.path.isfile(os.path.join(outputFolder, f)) and
             f.find("fake") != -1]
    os.mkdir(os.path.join(clientDir, "laserfiles"))
    for f in files:
        newname = f.replace("_fake_B", "")
        os.rename(os.path.join(outputFolder, f), os.path.join(clientDir, "laserfiles", newname))
    shutil.make_archive(os.path.join(clientDir, "laserfiles"), 'zip', os.path.join(clientDir, "laserfiles"))
    shutil.rmtree(os.path.join(clientDir, "results"))
    shutil.rmtree(imagesDir)
    shutil.rmtree(os.path.join(clientDir, "laserfiles"))
    clientRequestStatusLock.acquire()
    clientRequestStatus.pop(ip)
    clientRequestStatusLock.release()
    return send_file(os.path.join(clientDir, "laserfiles.zip"), mimetype="application/zip")



if __name__ == '__main__':
    app.run(host='192.168.1.13',port='5000')
      
