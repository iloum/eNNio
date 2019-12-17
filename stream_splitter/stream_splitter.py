class StreamSplitter:
    def __init__(self):
        self._video_stream_location = None
        self._audio_stream_location = None

    def set_video_stream_location(self, path):
        self._video_stream_location = path

    def set_audio_stream_location(self, path):
        self._audio_stream_location = path

    def split_video_file(self, file_path):
        """
        Method to split video to separate audio and video streams
        :param file_path: path to video file
        :return: tuple(audio_stream_file_path, video_stream_file_path)
        """
        pass