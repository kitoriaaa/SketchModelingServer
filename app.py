from flask import Flask, request, make_response, jsonify, redirect, url_for, send_file
import os
import sys
import werkzeug
from datetime import datetime
import subprocess
import shutil


app = Flask(__name__)


cmd1 = "python rgb2grayscale.py ./Media/Uploads/Chair/sketch/p1"
cmd2 = "python main.py --test --data_dir ../../../Media/Uploads/Chair/ --train_dir ../Checkpoint/Chair/ --test_dir ../../../Media/Output --sketch_views FS"
cmd3 = "bash ReconstructMesh.sh"
cmd4 = "python ply2obj.py ply_path Media/Ply/p1/mesh.ply"

app.config['UPLOAD_FOLDER'] = './Media/Uploads/Chair/sketch/p1'
app.config['OUTPUT_FOLDER'] = "./Media/Output"

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'file' not in request.files:
            sys.stderr.write("file not in request.files")
            return make_response(jsonify({'result':'upload files is required'}))

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        if os.path.exists("Media/Ply"):
            shutil.rmtree("Media/Ply")

        upload_files = request.files.getlist('file')
        for file in upload_files:
            if file.filename == "":
                return redirect(requst.url)
            file_name = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))

        print("exsists : {}".format(os.path.exists(app.config['UPLOAD_FOLDER'])))

        subprocess.call(cmd1.split())
        os.chdir("Network/code/MonsterNet")
        subprocess.call(cmd2.split())
        os.chdir("../../../Fusion/output/ReconstructMesh/Win32/Release")
        subprocess.call(cmd3.split(), shell=True)
        os.chdir("../../../../../")
        subprocess.call(cmd4.split())

        # Delete Upload image directory and normal,depth map
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        shutil.rmtree("Media/Output")
        # return mesh file
        return send_file(filename_or_fp="Media/Ply/p1/mesh.obj", as_attachment=True)

    return '''
    <!DOCTYPE html>
        <head>
            <metadata charset="UTF-8">
            <title> 3Dオブジェクト生成 </title>
        </head> 
        <body>
            <h1> ファイルをアップロードしてオブジェクトを生成します </h1>
            <form method=post enctype=multipart/form-data>
                <p><input type=file name=file multiple='multiple'>
                <input type=submit value=Upload>
            </form>
        <body>
    </html>
    '''



if __name__ == "__main__":
    print(app.url_map)
    app.run(host='0.0.0.0', debug=True)
    