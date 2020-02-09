import ennio_exceptions as exc
import sys
import re
from time import time
from cmd import Cmd
from ennio_core.ennio_core import EnnIOCore

VALID_URL = re.compile(r'^(?:http|ftp)s?://'  # http:// or https://
                       r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
                       r'localhost|'  # localhost...
                       r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                       r'(?::\d+)?'  # optional port
                       r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class WebEnnio(object):
    """
    Class that manages ennIO's basic pipelines as commanded by the web controller
    """

    def __init__(self):
        super(WebEnnio, self).__init__()
        self.ennio_core = EnnIOCore()
        self.ennio_core.setup()

    def training_mode(self):
        """
        trains ennIO on existing clips
        :return:
        """

        # do_download_video_from_url_file
        downloaded, failed = self.ennio_core.download_video_from_url_file()
        print('Downloaded files')
        for f in downloaded:
            print(f)
        print()
        print('Failed to download')
        for f in failed:
            print(f)
        print()

        # do_extract_features
        start_time = time()
        video_extracted, audio_extracted = self.ennio_core.extract_features()
        print("Finished in {:.1f} secs".format(time() - start_time))
        print('Video features extracted from {} clips'.format(len(video_extracted)))
        print('Audio features extracted from {} clips'.format(len(audio_extracted)))

        # do_create_dataframes
        self.ennio_core.create_dataframe_files()

        return

    def evaluation_mode(self, url, start_time_str):
        """
        :param url: url for evaluation
        :param start_time_str: start time in string format
        :return: paths: a list of 4 combined videos in the form of tuples (id, model, path)
        """
        paths = []
        if any(i.isalpha() for i in start_time_str):
            raise exc.EnnIOException("start time must be just digits!")

        # Download video
        video_name = self.do_download_video_from_url(url, start_time_str)

        # Extract video features
        video_extracted = self.ennio_core.extract_video_features_for_evaluation(video_name)

        # Call predict for all models

        # Join Video and suggested audio

        # Call predict for all models

        # Join Video and suggested audio

        return paths

    def update_winner(self, winner_id, winner_model):
        """
        :param winner_id:
        :param winner_model:
        :return:
        """
        if not isinstance(winner_model, str):
            raise exc.EnnIOException("winner model must be in string format!")
        path = ""
        return

    def live_ennio(self, url, start_time_str):
        """
        the live version of ennIO
        :param url: video url
        :param start_time_str: starting time
        :return: the path of the combined video
        """
        path = ""
        if any(i.isalpha() for i in start_time_str):
            raise exc.EnnIOException("start time must be just digits!")
        return path

    def do_download_video_from_url(self, url, start_time):
        """
        Download Youtube video from url
        Usage: download_video_from_url <URL>
        """
        try:
            if ":" not in start_time:
                print("Not valid start-time format - Valid format MM:SS")
                return
        except IndexError:
            pass
        print(start_time)
        file_path = self.ennio_core.download_video_from_url(url=url,
                                                            start_time_str=start_time, mode="evaluation")
        if file_path:
            print('Downloaded file')
            print(file_path)
            return file_path
        else:
            print('Failed to download')
            print(url, start_time)

# for my testing
# if __name__=='__main__':
#    we = WebEnnio()
#    print(we.evaluation_mode("","1a"))
