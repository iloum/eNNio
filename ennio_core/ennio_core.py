class EnnIOCore:
    def __init__(self, config_manager):
        pass

    def construct_model(self):
        """
        Method to create and train an ML model
        :return:
        """
        pass

    def use_model(self, input_file):
        """
        Method to use the existing model in order to predict a
        suitable music score
        :return:
        """
        pass

    def download_video_from_url(self, url):
        """
        Method to download a video file from a youtube URL
        :param url: A youtube video URL
        :return: Downloaded file name
        """
        pass

    def download_video_from_url_file(self):
        """
        Method to download video files from CSV file listing youtube URLs
        :return: List of downloaded file names
        """
        pass

    def get_status(self):
        """
        Method to display systems status
        :return:
        """
        pass

    def extract_features(self, filenames):
        """
        Method to extract audio and video features from files
        :param filenames: List of file names to be used
        :return: Dictionary containing video and audio features
        """
        return {'audio_features': None,
                'video_features': None}