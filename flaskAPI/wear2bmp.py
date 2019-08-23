import os, stat
from flask import Flask, flash, request, redirect, url_for, send_file, Response
from werkzeug.utils import secure_filename
import shutil

UPLOAD_FOLDER = './tmp'
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','zip','7z'}
num_files = 0

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return redirect("./index.html")

@app.route("/hello")
def helloWorld():
    return "Hello World"

@app.route("/GETtest")
def getTest():
    return "successfully pinged"

@app.route("/POSTtest",methods=['POST'])
def postTest():
    print("received POST")
    files = request.files.getlist('images')
    ip = request.remote_addr
    if not os.path.isdir(app.config['UPLOAD_FOLDER'] + '/' + ip):
        os.mkdir(app.config['UPLOAD_FOLDER'] + '/' + ip)
    for f in files:
        name = secure_filename(f.filename)
        name = os.path.basename(name)
        #if this filename already exists
        path = os.path.join(app.config['UPLOAD_FOLDER'],ip,name)
        if os.path.isfile(path):
            i=0
            tmp, ext = os.path.splitext(name)
            while os.path.isfile(path): #add "_i" until it is unique filename
                i += 1
                path = os.path.join(app.config['UPLOAD_FOLDER'], ip, tmp+"_{0}{1}".format(i,ext))
                print(path)
            name = tmp+"_"+str(i)+ext
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],ip,name))
    shutil.make_archive("./tmp/"+ip,'zip',"./tmp/"+ip)
    return "sucessfully uploaded"

@app.route('/App',methods=['GET','POST'])
def upload_file():
    if request.method == 'POST':
        print("received POST")
        files = request.files.getlist('images')
        ip = request.remote_addr
        clientDir = app.config['UPLOAD_FOLDER'] + '/' + ip
        if os.path.isdir(clientDir):
            for f in os.listdir(clientDir):
                p = os.path.join(clientDir,f);
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)
        else:
            os.mkdir(clientDir)
        if not os.path.isdir(os.path.join(clientDir,"images")):
            os.mkdir(os.path.join(clientDir,"images"))
        imagesDir = os.path.join(clientDir,"images")

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
        netname = "whiskersBW3"
        command = ("python ./pix2pix/test.py --dataroot "+ dataroot + " " +
                   "--results_dir " + clientDir+"/results/ "
                   "--name " + netname + " --model test --netG unet_1024 --direction AtoB --dataset_mode single "+
                   "--loadSize 1024 --fineSize 1024 --norm batch --use_upsample_conv --input_nc 1 --output_nc 1")
        print(command)
        os.system(command)

        #copy all "fake" images to new folder
        outputFolder = os.path.join(clientDir,"results/whiskersBW3/test_latest/images")
        files = [f for f in os.listdir(outputFolder) if os.path.isfile(os.path.join(outputFolder,f)) and f.find("fake")!=-1]
        os.mkdir(os.path.join(clientDir,"laserfiles"))
        for f in files:
            newname = f.replace("_fake_B","")
            os.rename(os.path.join(outputFolder,f),os.path.join(clientDir,"laserfiles",newname))

        shutil.make_archive(os.path.join(clientDir,"laserfiles"), 'zip', os.path.join(clientDir,"laserfiles"))
        shutil.rmtree(os.path.join(clientDir,"results"))
        shutil.rmtree(imagesDir)
        shutil.rmtree(os.path.join(clientDir,"laserfiles"));
        return send_file(os.path.join(clientDir,"laserfiles.zip"),mimetype="application/zip")
    if request.method == 'GET':
        return "Get Method Here"
@app.route("/download",methods=["GET"])
def downloadResults():
    print("Download results");
    ip = request.remote_addr;
    if os.path.isdir(app.config['UPLOAD_FOLDER'] + '/' + ip):
        os.rmdir()

@app.route("/setNumberOfFilesToUpload",methods=["POST"])
def set_num_files():
    print("what")
@app.route("/uploadFiles", methods=["GET","POST"])
def upload_files():
    if request.method == 'POST':
        print(request.files)
@app.route("/filenames", methods=["GET"])
def get_filenames():
    filenames = os.listdir("uploads/")

    #modify_time_sort = lambda f: os.stat("uploads/{}".format(f)).st_atime

    def modify_time_sort(file_name):
        file_path = "uploads/{}".format(file_name)
        file_stats = os.stat(file_path)
        last_access_time = file_stats.st_atime
        return last_access_time

    filenames = sorted(filenames, key=modify_time_sort)
    return_dict = dict(filenames=filenames)
    return jsonify(return_dict)


if __name__ == '__main__':
    app.run(host='192.168.1.13',port='5000')
      
