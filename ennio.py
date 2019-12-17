#!/usr/bin/env python3

import sys
import re
from cmd import Cmd
from ennio_core.ennio_core import EnnIOCore


VALID_URL = re.compile(r'^(?:http|ftp)s?://' # http:// or https://
                       r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                       r'localhost|' #localhost...
                       r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                       r'(?::\d+)?' # optional port
                       r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class UserInterface(Cmd):
    def __init__(self):
        super(UserInterface, self).__init__()
        self.ennio_core = EnnIOCore()
        self.ennio_core.setup()
        self.prompt = 'ennIO> '
        self.intro = "Welcome to ennIO! Type ? to list commands"

    def do_exit(self, args):
        """Exit the application"""
        self.ennio_core.on_exit()
        print("Bye!")
        return True

    do_EOF = do_exit

    def do_construct_model(self, args):
        """
        Create and train a model
        """
        self.ennio_core.construct_model()

    def do_use_model(self, args):
        """
        Use an existing model to predict the score
        Usage: use_model <filename>
        """
        if not args:
            print("Video file name needed")
        self.ennio_core.use_model(input_file=args)

    def do_download_video_from_url(self, args):
        """
        Download Youtube video from url
        Usage: download_video_from_url <URL>
        """
        if not args:
            print("Youtube URL needed for download")
            return
        if not re.match(VALID_URL, args):
            print("Not valid url")
            return
        self.ennio_core.download_video_from_url(url=args)

    def do_download_video_from_url_file(self, args):
        """
        Download Youtube video from url CSV
        """
        self.ennio_core.download_video_from_url_file()

    def do_show_status(self, args):
        """
        Show status information about the ennIO
        """
        self.ennio_core.get_status()

    def do_extract_features(self, args):
        """
        Extract audio and video features from downloaded file
        Usage: extract_features <filename> <filename> ...
        """
        if not args:
            print("Video file names needed for feature extraction")
        self.ennio_core.extract_features(filenames=args.split())


if __name__=='__main__':
    # try:
    ui = UserInterface()
    ui.cmdloop()
    # except Exception as e:
    #     print("ERROR: {}".format(e))
    #     sys.exit(1)
    sys.exit(0)
