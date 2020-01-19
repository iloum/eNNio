import feature_extractor.video_features as vf
import numpy as np
from feature_extractor.features_extractor import FeatureExtractor


class VideoFeatureExtractor(FeatureExtractor):
    def __init__(self):
        pass

    def extract_video_features(self, filename, ftlist =["lbps", "hogs", "colors", "flow"] , width = 300, step = 3):
        """
        Method to extract video features from an video file
        :param filename: Name of the video file
        :return: Numpy array containing video features
        """
        v = vf.VideoFeatureExtractor(ftlist, resize_width=width, step=step)
        features, time, featureNames = v.extract_features(filename)
        features_avg = np.average(np.array(features, dtype=np.float64), axis=0)
        features_std = np.std(np.array(features, dtype=np.float64), axis=0)
        all_features = np.concatenate((features_avg, features_std), axis=None)
        features_stdNames = [x + "_std" for x in featureNames]
        all_featuresNames = featureNames + features_stdNames

        return all_features, all_featuresNames



# for my testing
if __name__=="__main__":
    fe = VideoFeatureExtractor()
    r, n = fe.extract_video_features("D:\\test\\Zoobi Doobi 3 Idiots Full Song Feat. Aamir Khan, Kareena Kapoor-yJ1uLVgv3Vg.mp4")
    print(r)
