import ennio_exceptions as exc
class WebEnnio(object):
    """
    Class that manages ennIO's basic pipelines as commanded by the web controller
    """

    def training_mode(self):
        """
        trains ennIO on existing clips
        :return:
        """
        return

    def evaluation_mode(self,url,start_time_str):
        """
        :param url: url for evaluation
        :param start_time_str: start time in string format
        :return: paths: a list of 4 combined videos in the form of tuples (id, model, path)
        """
        try:
            if any(i.isalpha() for i in start_time_str):
                raise
            paths = []
        except exc.EnnIOException("start time must be just digits!"):
            raise
        return paths

    def update_winner(self, winner_id, winner_model):
        """
        :param winner_id:
        :param winner_model:
        :return:
        """
        try:
            if not isinstance(winner_model, str):
                raise
            path = ""
        except exc.EnnIOException("winner model must be in string format!"):
            raise

        return

    def live_ennio(self, url,start_time_str):
        """
        the live version of ennIO
        :param url: video url
        :param start_time_str: starting time
        :return: the path of the combined video
        """
        try:
            if any(i.isalpha() for i in start_time_str):
                raise
            path = ""
        except exc.EnnIOException("start time must be just digits!"):
            raise
        return path

# for my testing
#if __name__=='__main__':
#    we = WebEnnio()
#    print(we.evaluation_mode("","12"))