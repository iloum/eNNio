import feature_extractor.video_features as vf
import numpy as np
from feature_extractor.features_extractor import FeatureExtractor


class VideoFeatureExtractor(FeatureExtractor):
    def __init__(self, videopath):
        super().__init__(videopath)
        pass
    #TODO:
    #Remove path from constructor. Check george code to be the same and then remove it.

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



# for my testing
if __name__=="__main__":
    fe = VideoFeatureExtractor("D:\\test\\Zoobi Doobi 3 Idiots Full Song Feat. Aamir Khan, Kareena Kapoor-yJ1uLVgv3Vg.mp4")
    r, n = fe.extract_video_features("D:\\test\\Zoobi Doobi 3 Idiots Full Song Feat. Aamir Khan, Kareena Kapoor-yJ1uLVgv3Vg.mp4")
    print(r)