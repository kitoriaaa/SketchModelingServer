from flask import Flask, request, make_response, jsonify, redirect, url_for, send_file, render_template
import os
import sys
import werkzeug
from datetime import datetime
import subprocess
import shutil
import configparser
import shlex
from modules import hololens
from modules import rgb2grayscale
from modules import ply2obj


app = Flask(__name__)

# read config file and create HoloLens instance
config = configparser.ConfigParser()
config.read('config.ini')
holo_conf = config['HoloLens']
upload = config['Upload']
unity = config['Unity']
# create instance
hololens2 = hololens.Hololens(
    holo_conf['username'], holo_conf['password'], holo_conf['ipaddress'])


cmd2 = "python main.py --test --data_dir ../../../Media/Uploads/Chair/ --train_dir ../Checkpoint/Chair/ --test_dir ../../../Media/Output --sketch_views FS"
cmd3 = "bash ReconstructMesh.sh"

# AssetBundle Build command
buildAssetBundle = unity['UnityPath'] + " -batchmode -quit -logFile ./build.log -projectPath " + unity['projectPath'] + " -executeMethod " + unity['methodName']

app.config['UPLOAD_FOLDER'] = './Media/Uploads/Chair/sketch/p1'
app.config['OUTPUT_FOLDER'] = "./Media/Output"
app.config['PLY_FOLDER'] = "./Media/Ply/p1/mesh.ply"


@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'file' not in request.files:
            sys.stderr.write("file not in request.files")
            return make_response(jsonify({'result':'upload files is required'}))

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # if os.path.exists("Media/Ply"):
        #     shutil.rmtree("Media/Ply")

        object_type = request.form["obj-type"]
        print(object_type)
        upload_files = request.files.getlist('file')
        for file in upload_files:
            if file.filename == "":
                return redirect(request.url)
            file_name = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))

        print("exsists : {}".format(os.path.exists(app.config['UPLOAD_FOLDER'])))

        # rgb2grayscale
        app.logger.info("convert rgb2grayscale")
        rgb2grayscale.convert(app.config['UPLOAD_FOLDER'])

        # calc depth and normal map
        os.chdir("Network/code/MonsterNet")
        subprocess.call(cmd2.split())
        # create point cloud and poisson surface reconstruction
        os.chdir("../../../Fusion/output/ReconstructMesh/Win32/Release")
        subprocess.call(cmd3.split(), shell=True)
        # ply2obj
        os.chdir("../../../../../")
        ply2obj.convert(app.config['PLY_FOLDER'])

        # copy obj file to Unity AssetBundleResources folder
        shutil.copy2("Media\Ply\p1\mesh.obj", unity['projectPath']+unity['AssetBundleResources'])

        # build AssetBundle
        app.logger.info("Build AssetBundle...")
        subprocess.call(shlex.split(buildAssetBundle))

        # AssetBundle send hololens
        app.logger.info("Upload HoloLens...")
        hololens2.upload(upload['directory'], upload['filename'])

        # Delete Upload image directory and normal,depth map
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
        if os.path.exists(app.config['OUTPUT_FOLDER']):
            shutil.rmtree(app.config['OUTPUT_FOLDER'])

        # return mesh file
        return send_file(filename_or_fp="Media/Ply/p1/mesh.obj", as_attachment=True)
    
    return render_template("index.html")


if __name__ == "__main__":
    print(app.url_map)
    app.run(host='0.0.0.0', debug=True)
    