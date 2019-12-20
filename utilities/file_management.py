from os import listdir
from os.path import isfile, join


def getfilelist(path):
    files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]
    return files


def getfiledictionary(path):
    filedict = dict()
    for f in listdir(path):
        if isfile(join(path, f)):
            filedict[f] = join(path, f)
    return filedict