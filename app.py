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
from Network.code.MonsterNet import main
import time


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

# Run poisson surface reconstruction
poisson = """PoissonRecon.exe \
             --in ../../../../../Media/ply/p1/points.ply \
             --out ../../../../../Media/Ply/p1/mesh.ply \
             --depth 11 \
             --samplesPerNode 5.0\ 
             --pointWeight 0.1"""


# AssetBundle Build command
buildAssetBundle = unity['UnityPath'] \
                   + " -batchmode -quit -logFile ./build.log -projectPath " \
                   + unity['projectPath'] \
                   + " -executeMethod " \
                   + unity['methodName']

app.config['UPLOAD_FOLDER'] = './Media/Uploads/sketch/p1/'
app.config['OUTPUT_FOLDER'] = "./Media/Output"
app.config['PLY_FOLDER'] = "./Media/Ply/p1/mesh.ply"
app.config['CHECKPOINT_DIR'] = "Network/code/Checkpoint/"

obj_type_dict = {"plane":"TS", "chair":"FS", "character":"FS"}


@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        st = time.time()
        if 'file' not in request.files:
            sys.stderr.write("file not in request.files")
            return make_response(jsonify({'result':'upload files is required'}))


        # check obj-type is correct
        object_type = request.form["obj-type"]
        if (not (object_type in obj_type_dict.keys())):
            return make_response(jsonify({"result":"obj-type must be plane or chair or character"}))
        app.logger.info("Create object type is: %s", str(object_type))


        # make upload dir and save files
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        upload_files = request.files.getlist('file')
        for file in upload_files:
            if file.filename == "":
                #TODO: return message (ex) Please choose images
                return redirect(request.url)
            file_name = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))

        # remove previous ply dir
        if os.path.exists("Media/Ply"):
            shutil.rmtree("Media/Ply")

        # rgb2grayscale
        app.logger.info("convert rgb2grayscale")
        rgb2grayscale.convert(app.config['UPLOAD_FOLDER'])

        # calc depth and normal map
        run_network(object_type)

        # create point cloud and poisson surface reconstruction
        os.chdir("Fusion/output/ReconstructMesh/Win32/Release")
        reconstruct = "ReconstructMesh.exe 1 " \
                       + obj_type_dict[object_type] \
                       + " ../../../../." + app.config['UPLOAD_FOLDER'] \
                       + " ../../../../../Media/Output/images/p1/ ../../../../../Media/Ply/p1/ ../../../../../Media/Uploads/view/" \
                       + object_type + ".off"
                       
        subprocess.call(reconstruct.split(), shell=True)
        subprocess.call(poisson.split(), shell=True)
        os.chdir("../../../../../")

        app.logger.info("Complete Objct create Time: %s", time.time()-st)

        # ply2obj
        ply2obj.convert(app.config['PLY_FOLDER'])

        # copy obj file to Unity AssetBundleResources folder
        try:
            shutil.copy2("Media\Ply\p1\mesh.obj", unity['projectPath'] + unity['AssetBundleResources'])
        except FileNotFoundError as e:
            app.logger.error("Failed to copy obj file to AssetBundleResouces: %s", e)
        except Exception as e:
            app.logger.error("Failed to copy obj file to AssetBundleResouces: %s", e)

        # build AssetBundle
        try:
            app.logger.info("Build AssetBundle...")
            subprocess.call(shlex.split(buildAssetBundle))
            app.logger.info("Finish: Build AssetBundle")
        except FileNotFoundError as e:
            app.logger.error("Failed to build AssetBundle: %s", e)
        except Exception as e:
            app.logger.error("Failed to build AssetBundle: %s", e)


        # AssetBundle send hololens
        try:
            app.logger.info("Upload HoloLens...")
            hololens2.upload(upload['directory'], upload['filename'])
            app.logger.info("Finished: Upload HoloLens")
        except FileNotFoundError as e:
            app.logger.error("Failed to send AssetBundle to HoloLens: %s", e)
        except Exception as e:
            app.logger.error("Failed to send AssetBundle to HoloLens: %s", e)


        # Delete Upload image directory and normal,depth map
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
        if os.path.exists(app.config['OUTPUT_FOLDER']):
            shutil.rmtree(app.config['OUTPUT_FOLDER'])

        app.logger.info("Time: %s", time.time()-st)
        # return mesh file
        return send_file(filename_or_fp="Media/Ply/p1/mesh.ply", as_attachment=True)
    
    return render_template("index.html")


def run_network(obj_type):
    main.FLAGS.test = True
    main.FLAGS.data_dir = "./Media/Uploads/"
    main.FLAGS.test_dir = app.config['OUTPUT_FOLDER']
    main.FLAGS.train_dir = app.config['CHECKPOINT_DIR'] + str(obj_type)
    main.FLAGS.sketch_views = obj_type_dict[obj_type]
    main.FLAGS.view_file = str(obj_type) + ".off"

    try:
        main.main()
    except Exception as e:
        app.logger.error("Can\'t run tensorflow cnn: %s", e)



if __name__ == "__main__":
    print(app.url_map)
    app.run(host='0.0.0.0', debug=True)
    