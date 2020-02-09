#!/usr/bin/env python3

import sys
import re
from time import time
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
        # input example in terminal: ennIO> use_model https://www.youtube.com/watch?v=i-dJPoSlPfU 10
        if not args:
            print("Video url and start time are needed")
            return

        inputs = args.split()
        url = inputs[0]
        start_time = int(inputs[1])
        if not re.match(VALID_URL, inputs[0]):
            print("Not valid url")
            return

        self.ennio_core.use_model(url, start_time=start_time) #input_file=args)

    def do_download_video_from_url(self, args):
        """
        Download Youtube video from url
        Usage: download_video_from_url <URL>
        """
        if not args:
            print("Youtube URL needed for download")
            return
        inputs = args.split()
        if not re.match(VALID_URL, inputs[0]):
            print("Not valid url")
            return

        start_time = None
        try:
            start_time = inputs[1]
            if ":" not in start_time:
                print("Not valid start-time format - Valid format MM:SS")
                return
        except IndexError:
            pass
        print(inputs[0])
        print(start_time)
        file_path = self.ennio_core.download_video_from_url(url=inputs[0],
                                                            start_time_str=start_time)
        if file_path:
            print('Downloaded file')
            print(file_path)
        else:
            print('Failed to download')
            print(args)

    def do_download_video_from_url_file(self, args):
        """
        Download Youtube video from url CSV
        """
        downloaded, failed = self.ennio_core.download_video_from_url_file()
        print('Downloaded files')
        for f in downloaded:
            print(f)
        print()
        print('Failed to download')
        for f in failed:
            print(f)
        print()

    def do_show_status(self, args):
        """
        Show status information about the ennIO
        """
        self.ennio_core.get_status()

    def do_extract_features(self, args):
        """
        Extract audio and video features from downloaded file
        Usage: extract_features
        """
        start_time = time()
        video_extracted, audio_extracted = self.ennio_core.extract_features()
        print("Finished in {:.1f} secs".format(time()-start_time))
        print('Video features extracted from {} clips'.format(len(video_extracted)))
        print('Audio features extracted from {} clips'.format(len(audio_extracted)))

    def do_drop(self, args):
        """
        Drop information from db
        Usage: drop [audio_features] [video_features] [tables]
        """
        if not args:
            print("Please give one or more options")
            return

        for option in args.split():
            self.ennio_core.drop(option)

    def do_create_dataframes(self, args):
        """
        Save extracted features to pickled dataframes
        """
        self.ennio_core.create_dataframe_files()


if __name__=='__main__':
    # try:
    ui = UserInterface()
    ui.cmdloop()
    # except Exception as e:
    #     print("ERROR: {}".format(e))
    #     sys.exit(1)
    sys.exit(0)
