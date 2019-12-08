#!/usr/bin/env python3

import sys
from cmd import Cmd
from config_manager.config_manager import ConfigManager
from ennio_core.ennio_core import EnnIOCore

class UserInterface(Cmd):
    def __init__(self, ennio):
        super(UserInterface, self).__init__()
        self.ennio = ennio
        self.prompt = 'ennIO> '
        self.intro = "Welcome to ennIO! Type ? to list commands"

    def do_exit(self, input):
        """Exit the application"""
        print("Bye!")
        return True

    do_EOF = do_exit

    def do_construct_model(self, input):
        """
        Create and train a model
        """
        self.ennio.ennio_core.construct_model()

    def do_use_model(self, input):
        """
        Use an existing model to predict the score
        Usage: use_model <filename>
        """
        if not input:
            print("Video file name needed")
        self.ennio.ennio_core.use_model(input_file=input)

    def do_download_video_from_url(self, input):
        """
        Download Youtube video from url
        Usage: download_video_from_url <URL>
        """
        if not input:
            print("Youtube URL needed for download")
        self.ennio.ennio_core.download_video_from_url(url=input)

    def do_download_video_from_url_file(self):
        """
        Download Youtube video from url CSV
        """
        self.ennio.ennio_core.download_video_from_url_file()

    def do_show_status(self, input):
        """
        Show status information about the ennIO
        """
        self.ennio.ennio_core.get_status()

    def do_extract_features(self, input):
        """
        Extract audio and video features from downloaded file
        Usage: extract_features <filename> <filename> ...
        """
        if not input:
            print("Video file names needed for feature extraction")
        self.ennio.ennio_core.extract_features(filenames=input.split())


class EnnIO:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config_manager.read_config()
        self.ennio_core = EnnIOCore(self.config_manager)


if __name__=='__main__':
    try:
        ui = UserInterface(EnnIO())
        ui.cmdloop()
    except Exception as e:
        print("ERROR: {}".format(e))
        sys.exit(1)
    sys.exit(0)