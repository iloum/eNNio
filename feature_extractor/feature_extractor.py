import video_features as vf
import numpy as np
from os import listdir
from os.path import isfile, join

class FeatureExtractor:
    def __init__(self, videopath, audiopath):
        self.videopath = videopath
        self.audiopath = audiopath
        pass

    def extract_audio_features(self, filename):
        """
        Method to extract audio features from an audio file
        :param filename: Name of the audio file
        :return: Numpy array containing audio features
        """
        pass

    def extract_video_features(self, filename):
        """
        Method to extract video features from an video file
        :param filename: Name of the video file
        :return: Numpy array containing video features
        """
        v = vf.VideoFeatureExtractor(["lbps", "hogs", "colors", "flow"], resize_width=300, step=3)
        features, time, featureNames = v.extract_features(filename)
        featuresAvg = np.average(features, axis=0)
        return featuresAvg, featureNames

    def extract_all_videoFiles_features(self):
        filelist = getfilelist(self.videopath)
        videoFeatures = list()
        for file in filelist:
            featuresAvg, featureNames = self.extract_video_features(file)
            videoFeatures.append(featuresAvg)
        videoFeatures.append(featureNames)
        return videoFeatures

def getfilelist(path):
    files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]
    return files


# for my testing
if __name__=="__main__":
    fe = FeatureExtractor(videopath="D:\\test",audiopath="")
    r = fe.extract_all_videoFiles_features()
    print(r)