from multiprocessing import Process
import time, itertools, sys

def worker(*lst):
    for i in lst:
        print("Doing task : {}".format(i))
        time.sleep(2)
        print("Task done!")

        
if __name__ == "__main__":

    l = [1,2,3,4,5,6,7,8,9,0]

    for e in [[1,2,3,4],[5,6,7,8]]:
        p = Process(target=worker, args=(e))
        #p.daemon = True # bez ovoga glavni proces se nikada ne zavrsi
        p.start()
