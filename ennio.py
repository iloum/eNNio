#!/usr/bin/env python3
import os
import sys
import re
from time import time
from cmd import Cmd
from ennio_core.ennio_core import EnnIOCore
import subprocess
from ennio_exceptions import EnnIOException

VALID_URL = re.compile(r'^(?:http|ftp)s?://' # http:// or https://
                       r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                       r'localhost|' #localhost...
                       r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                       r'(?::\d+)?' # optional port
                       r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class UserInterface(Cmd):
    def __init__(self):
        super(UserInterface, self).__init__()
        self.ennio_core = EnnIOCore(os.path.dirname(os.path.realpath(__file__)))
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
        Create and train model
        To retrain model run 'drop models'
        """
        self.ennio_core.construct_models()

    def do_use_model(self, args):
        """
        Use all available models to predict the score
        Usage: use_model <youtube-url> [<timestamp>]
        Example: use_model https://www.youtube.com/watch?v=i-dJPoSlPfU 0:10
        """
        try:
            start_time, url = self._validate_url_start_time(args)
        except UserWarning as warn:
            print(warn)
            return

        video_name, results = self.ennio_core.use_models(url, start_time_str=start_time)
        print("Suggestions for video: {}".format(video_name))
        for model_name, file_path in results.items():
            print("{model_name}. {audio_path}".format(model_name=model_name,
                                                      audio_path=file_path))

    def do_download_video_from_url(self, args):
        """
        Download Youtube video from url and insert it in training data
        Usage: download_video_from_url <youtube-url> [<start-time(MM:SS)>]
        """
        try:
            start_time, url = self._validate_url_start_time(args)
        except UserWarning as warn:
            print(warn)
            return

        file_path = self.ennio_core.download_video_from_url(url=url,
                                                            start_time_str=start_time)
        if file_path:
            print('Downloaded file')
            print(file_path)
        else:
            print('Failed to download')
            print(args)

    @staticmethod
    def _validate_url_start_time(args):
        if not args:
            raise UserWarning("Youtube URL needed for download")

        inputs = args.split()
        url = inputs[0]
        if not re.match(VALID_URL, url):
            raise UserWarning("Not valid url")

        start_time = None
        try:
            start_time = inputs[1]
            if ":" not in start_time:
                raise UserWarning("Not valid start-time format - Valid format MM:SS")
        except IndexError:
            pass

        return start_time, url

    def do_download_video_from_url_file(self, args):
        """
        Download Youtube videos from CSV file configured in config.ini
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
        Show status information about the ennIO DB
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
        Remove created data. Available options: audio_features|video_features|tables|evaluation_table|models
        WARNING: THIS WILL PERMANENTLY REMOVE DATA
        Usage: drop [audio_features] [video_features] [tables] [evaluation_table] [models]
        """
        if not args:
            print("Please give one or more options")
            return

        for option in args.split():
            if input("Do you really want to drop {}? [y/n]: ".format(option)) == "y":
                print("Dropping {}".format(option))
                self.ennio_core.drop(option)
                print("Done")

    def do_create_dataframes(self, args):
        """
        Save extracted features to pickled dataframes
        """
        video_features_file, audio_features_file, metadata_file = self.ennio_core.create_dataframe_files()
        print("Saved to {file_name}".format(file_name=video_features_file))
        print("Saved to {file_name}".format(file_name=audio_features_file))
        print("Saved to {file_name}".format(file_name=metadata_file))


    def do_evaluate(self, args):
        """
        Evaluate models by voting the best match
        Usage: evaluate <youtube-url> [<start-time(MM:SS)>]
        Example: evaluate https://www.youtube.com/watch?v=CL5NeUZTzvw 0:15
        """
        try:
            start_time, url = self._validate_url_start_time(args)
        except UserWarning as warn:
            print(warn)
            return
        try:
            video_id, results = self.ennio_core.evaluation_mode(url, start_time_str=start_time)
        except EnnIOException as e:
            print(e)
            return

        num_to_model = {}
        for num, (model, exported_path) in enumerate(results.items(), start=1):
            print()
            print("Playing video number {}".format(num))
            print()
            num_to_model[num] = model
            subprocess.run(['ffplay', '-autoexit', '-loglevel', 'quiet', exported_path])
            while input("Replay [y/n]: ") == "y":
                subprocess.run(['ffplay', '-autoexit', '-loglevel', 'quiet', exported_path])

        user_preference = input("Which score did you find more suitable {}: ".format(list(num_to_model.keys())))

        self.ennio_core.update_evaluation_vote(video_id, num_to_model[int(user_preference)])
        print("Thanks! Try another?")

    def do_predict(self, args):
        """
        Predict audio
        Usage: predict <youtube-url> [<start-time(MM:SS)>]
        Example: evaluate https://www.youtube.com/watch?v=CL5NeUZTzvw 0:15
        """
        try:
            start_time, url = self._validate_url_start_time(args)
        except UserWarning as warn:
            print(warn)
            return

        exported_path = self.ennio_core.live_ennio(url, start_time_str=start_time)

        print()
        print("Playing selected number {}".format(exported_path))
        print()
        subprocess.run(['ffplay', '-autoexit', '-loglevel', 'quiet', exported_path])


if __name__=='__main__':
    # try:
    ui = UserInterface()
    ui.cmdloop()
    # except Exception as e:
    #     print("ERROR: {}".format(e))
    #     sys.exit(1)
    sys.exit(0)
