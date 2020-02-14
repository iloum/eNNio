import os
import time
import functools
from utilities.singleton import Singleton
import random


def instance_lock(func):
    @functools.wraps(func)
    def wrapper_lock(*args, **kwargs):
        print("Asking for lock by {}".format(func.__name__))
        InstanceLock().acquire_instance_lock()
        print("Lock acquired by {}".format(func.__name__))
        value = func(*args, **kwargs)
        InstanceLock().release_instance_lock()
        print("Lock released by {}".format(func.__name__))
        return value
    return wrapper_lock


class InstanceLock(object, metaclass=Singleton):
    """
    Class that manages the instance lock for the bookcase manager
    """
    def __init__(self, path='.'):
        self.file = os.path.join(path, ".lock")
        self.fd = -1

    def acquire_instance_lock(self):
        """
        Tries to acquire instance lock by polling the lock file
        """
        while os.path.isfile(self.file):
            time.sleep(random.randrange(1, 3))

        self.fd = os.open(self.file, os.O_CREAT | os.O_EXCL)

    def release_instance_lock(self):
        """
        Closes and removes lock file to release program lock
        :return:
        """
        if self.fd != -1:
            os.close(self.fd)
            os.remove(self.file)