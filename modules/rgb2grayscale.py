
"""
python rgb2grayscale.py <DirectoryPath>(.\Sketch\sketch1)
"""

import cv2
import glob
import argparse

# Hyper parameters
hyper_params = {
    'directory': ''
}


# rgb png image to grayscale
def convert(directory_path):
    img_list = glob.glob(directory_path+"*.png")
    for img in img_list:
        im = cv2.imread(img)
        im = cv2.resize(im, (256, 256)) # Resize 256x256
        im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(img, im_gray)


def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('image_dir', help='RGB image directory', type=str)

    args = parser.parse_args()
    hyper_params['directory'] = args.image_dir

    convert(hyper_params['directory'])


if __name__ == "__main__":
    main()