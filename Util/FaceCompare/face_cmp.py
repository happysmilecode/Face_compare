import argparse
import json
import cv2
import os
import sys
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from insightface.data import *
import ntpath
import logging
from Util import Log
from Util import ImageUtil

assert insightface.__version__>='0.3'

ntpath.basename("a/b/c")

isConfig = False
def config(_onnxRootPath):
    global app
    global args
    global isConfig

    if isConfig:
        return

    isConfig = True
    parser = argparse.ArgumentParser(description='insightface app test')
    # general
    parser.add_argument('--ctx', default=0, type=int, help='ctx id, <0 means using cpu')
    parser.add_argument('--det-size', default=640, type=int, help='detection size')
    args = parser.parse_args()
    app = FaceAnalysis(name='antelopev2', root=_onnxRootPath)
    app.prepare(ctx_id=args.ctx, det_size=(args.det_size, args.det_size))

def ResetFacesInfo(faces):
    feats = []
    faceInfo = {}
    for face in faces:
        #eye, noise, mouth
        kps = face.kps.astype(np.intp)
        face['new_eye'] = [kps[0], kps[1]]
        face['new_noise'] = kps[2]
        face['new_mouth'] = [kps[3], kps[4]]
        #face-w, face-h
        face['new_width'] = float("{:.2f}".format(face.bbox[2] - face.bbox[0]))
        face['new_height'] = float("{:.2f}".format(face.bbox[3] - face.bbox[1]))

        face['new_feat'] = face.normed_embedding

        feats.append(face.normed_embedding)
    feats = np.array(feats, dtype=np.float32)
    sims = np.dot(feats, feats.T)
    return sims
def getFacesFromFile(strImgPath):
    dir, name = ntpath.split(strImgPath)
    image, w, h = ImageUtil.get_image(dir, name)

    faces = app.get(image)

    if len(faces) == 0:
        return None

    imgInfo = {}
    imgInfo['path'] = strImgPath
    imgInfo['faces'] = faces
    imgInfo['image'] = image
    imgInfo['ImgWidth'] = w
    imgInfo['ImgHeight'] = h
    imgInfo['sims'] = ResetFacesInfo(imgInfo['faces'])

    return imgInfo

# by Daniel Yoshida
def compareFaces(subjectFaces=[], targetFaces=[]):
    if len(subjectFaces) != 0 and len(targetFaces) != 0:
        for subject in subjectFaces:
            i = 0
            index = 0
            diffEmbedding = 1
            for target in targetFaces:
                diffEmbeddingBuf = np.linalg.norm(subject.normed_embedding - target.normed_embedding)
                if diffEmbeddingBuf < diffEmbedding:
                    index = i
                    diffEmbedding = diffEmbeddingBuf
                i = i + 1

            cmpInfo = {}
            cmpInfo['new_match_face'] = targetFaces[index]
            if diffEmbedding < 1:
                cmpInfo['new_match_status'] = True
                cmpInfo['new_match_msg'] = "Subject photo has matched to target photo"
                if diffEmbedding < 0.8:
                    if diffEmbedding < 0.7:
                        fConfidenceScore = 90 + ((.77 - diffEmbedding) / 0.07 - 1) * 1
                        cmpInfo['new_match_value'] = str('Highest match')
                    else:
                        fConfidenceScore = 80 + ((.81 - diffEmbedding) / 0.01 - 1) * 1
                        cmpInfo['new_match_value'] = str('High match')
                else:
                    fConfidenceScore = 70 + ((1.02 - diffEmbedding) / 0.02 - 1) * 1
                    cmpInfo['new_match_value'] = str('Low match')

                fConfidenceScore /= 100
                fConfidenceScore = float("{:.3f}".format(fConfidenceScore))
                cmpInfo['new_match_score'] = fConfidenceScore
                cmpInfo['new_match_score_str'] = str(fConfidenceScore) + " (" + str(
                    float("{:.3f}".format(fConfidenceScore * 100))) + "%)"
            else:
                cmpInfo['new_match_status'] = False
                cmpInfo['new_match_msg'] = "Subject photo has not matched to target photo"

            subject['new_cmp_info'] = cmpInfo
        return True
    return False

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

# by Daniel Yoshida
def DrawMatchFacesRect(strImgPath, image, faces, _outDirPath, includeMachingInfo = False, imgWidth = 100, o_aryMatchFaces = []):
    for n, face in enumerate(faces):
        cmpInfo = face['new_cmp_info']
        if cmpInfo['new_match_status'] == False:
            continue

        newImage = draw_on(image, [cmpInfo['new_match_face']])
        if includeMachingInfo:
            imEmptyForTxt = CreateWhiteImage(
                ["Score:" + str(float("{:.3f}".format(cmpInfo['new_match_score'] * 100))) + "%",
                 cmpInfo['new_match_value']],
                imgWidth, 70)
            newImage = cv2.vconcat([newImage, imEmptyForTxt])

        dir, name = ntpath.split(strImgPath)
        strPath = _outDirPath + "/" + name + "_" + str(n) + ".jpg"
        cv2.imwrite(strPath, newImage)
        face['new_path'] = strPath
        o_aryMatchFaces.append(face.copy())

    return o_aryMatchFaces

def draw_on(img, faces):
    dimg = img.copy()
    for i in range(len(faces)):
        face = faces[i]
        box = face.bbox.astype(np.intp)
        color = (0, 0, 255)
        cv2.rectangle(dimg, (box[0], box[1]), (box[2], box[3]), color, 2)
        if face.kps is not None:
            kps = face.kps.astype(np.intp)
            #print(landmark.shape)
            for l in range(kps.shape[0]):
                color = (0, 0, 255)
                if l == 0 or l == 3:
                    color = (0, 255, 0)
                cv2.circle(dimg, (kps[l][0], kps[l][1]), 1, color,
                           2)
        if face.gender is not None and face.age is not None:
            cv2.putText(dimg,'%s,%d'%(face.sex,face.age), (box[0]-1, box[1]-4),cv2.FONT_HERSHEY_COMPLEX,0.7,(0,255,0),1)

        for key, value in face.items():
           if key.startswith('landmark_3d'):
               # print(key, value.shape)
               # print(value[0:10,:])
               lmk = np.round(value).astype(np.intp)
               for l in range(lmk.shape[0]):
                   color = (255, 0, 0)
                   cv2.circle(dimg, (lmk[l][0], lmk[l][1]), 1, color,
                              1)
    return dimg

# by Daniel Yoshida
def hasOnnxFiles(onnx_dir):
    return os.path.exists(onnx_dir + "/1k3d68.onnx") and  \
            os.path.exists(onnx_dir + "/2d106det.onnx") and \
            os.path.exists(onnx_dir + "/genderage.onnx") and \
            os.path.exists(onnx_dir + "/glintr100.onnx") and \
            os.path.exists(onnx_dir + "/scrfd_10g_bnkps.onnx")

def isImgFile(strFile):
    return strFile.endswith(".png") or strFile.endswith(".jpg") \
                  or strFile.endswith(".jpeg") or strFile.endswith(".bmp")

def extract_time(json):
    try:
        # Also convert to int since update_time will be string.  When comparing
        # strings, "10" is smaller than "2".
        return float(json['new_cmp_info']['new_match_score'])
    except KeyError:
        return 0
