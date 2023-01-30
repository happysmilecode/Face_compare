import cv2
import os.path as osp
import numpy as np
class ImageCache:
    data = {}

def CreateWhiteImage(labels = ['Score:94%', 'Highest match'], width = 250, height = 70):
    im2 = np.zeros((height, width, 3), np.uint8)
    im2.fill(255)
    im2[:] = (255, 255, 255)
    lbls =labels

    offset = 35
    x, y = 0, 25
    for idx, lbl in enumerate(lbls):
        cv2.putText(im2, str(lbl), (x, y + offset * idx), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)

    return im2

def get_image(dir, name, to_rgb=False):
    key = (name, to_rgb)
    path = dir + "/" + name
    if not osp.exists(path):
        return

    img = cv2.imread(path)
    h, w, _ = img.shape
    if to_rgb:
        img = img[:,:,::-1]
    ImageCache.data[key] = img
    return img, w, h