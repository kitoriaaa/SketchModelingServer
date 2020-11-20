import requests
import base64
import os
import configparser


class Hololens():
    """
    HoloLens
    """
    def __init__(self, username, password, ipaddress):
        self.username = username
        self.password = password
        self.ipaddress = ipaddress

        self.api = "/api/filesystem/apps/file"
        self.url = "http://" + self.ipaddress + self.api


    def upload(self, dirpath, filename):
        upload_file = os.path.join(dirpath, filename)
        header = {"Content-Type" : "multipart/form-data"}
        payload = {'knownfolderid': '3D Objects', 'packagefullname': '\\', 'path': '\\'}

        file_binary = open(upload_file, 'rb')
        file = {'file': (filename, file_binary, '3d/obj')}
        res = requests.post(
                self.url, params=payload, 
                files = file, 
                auth=(self.username, self.password))

        print(res.text)
        print(res.status_code)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    holo_conf = config['HoloLens']
    
    hololens = Hololens(
        holo_conf['username'], holo_conf['password'], holo_conf['ipaddress'])
    
    hololens.upload(r"./Media/Ply", "mesh.obj")
