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
        payload = {'knownfolderid': 'LocalAppData', 
                   'packagefullname': 'Template3D_1.0.0.0_arm__pzq3xp76mxafg', 
                   'path': '/LocalState'}

        file_binary = open(upload_file, 'rb')
        file = {'file': (filename, file_binary, 'AssetBundle')}
        res = requests.post(
                self.url, 
                params=payload, 
                files = file, 
                auth=(self.username, self.password))

        print(res.text)
        print(res.status_code)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    holo_conf = config['HoloLens']
    upload = config['Upload']
    
    hololens = Hololens(
        holo_conf['username'], holo_conf['password'], holo_conf['ipaddress'])
    
    hololens.upload(upload['directory'], upload['filename'])