from os import listdir
from os.path import isfile, join


def getfilelist(path):
    files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]
    return files
