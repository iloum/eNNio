import feature_extractor.video_features as vf
import numpy as np
from utilities import file_management as fm
from feature_extractor.features_extractor import FeatureExtractor


class VideoFeatureExtractor(FeatureExtractor):
    def __init__(self, videopath):
        super().__init__(videopath)
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


    def extract_features(self):
        filelist = fm.getfilelist(self.path)
        videoFeatures = list()
        for file in filelist:
            featuresAvg, featureNames = self.extract_video_features(file)
            videoFeatures.append(featuresAvg)
        videoFeatures.append(featureNames)
        return videoFeatures

# for my testing
if __name__=="__main__":
    fe = VideoFeatureExtractor("D:\\test")
    r = fe.extract_features()
    print(r)