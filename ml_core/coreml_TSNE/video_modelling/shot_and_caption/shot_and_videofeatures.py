#added peak finding from scipy
from .video_features import video_features as vf
import numpy as np

from scipy.signal import find_peaks
import os
from PIL import Image
from matplotlib import pyplot as plt
import cv2


def generate_videofeatures(filepath,show_peaks=False):
    v = vf.VideoFeatureExtractor(["colors", "lbps", "hog","extra","flow"], step = 0.1)
    f, t, fn = v.extract_features(str(filepath))
    basename=os.path.basename(filepath)

    # normalize
    m = f.mean(axis=0)
    s = np.std(f, axis=0)
    s[s==0]=1
    f2 = (f-m) / s
    d = np.nansum(np.abs(f2[1::] - f2[:-1]), axis = 1)



    #plt.plot(t[1:], d, '-')
    maxh=np.max(d)
    minh=np.min(d)
    min_distance=(maxh-minh)*9/10
    peaks=find_peaks(d,height=min_distance)[0]
    shot_feature = np.arange(f.shape[0])
    prv_peak=0
    if len(peaks)>0:
        for idx,peak in enumerate(peaks):
            shot_feature[np.logical_and(shot_feature<peak, shot_feature>=prv_peak)]=idx
            prv_peak=peak
        shot_feature[shot_feature>=peak] = idx+1
    else:
        pass

    f=np.hstack([f,shot_feature.reshape(f.shape[0],1)])
    fn.append("shots")
    if show_peaks:
        plt.plot(t[1:][peaks],d[peaks],"o",c="r")
        plt.draw()

    return f,fn
