import os
def removeAllFiles(dir=''):
    files = os.listdir(dir)
    for file in files:
        os.remove(dir + '/' + file)
