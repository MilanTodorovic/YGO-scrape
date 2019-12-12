from multiprocessing import Pool, Queue, Process, Semaphore
import time, sys

def worker(queue):

    print("Doing task : {}".format(queue))
    time.sleep(2)
    print("Task done!")
    return 0

        
if __name__ == "__main__":
    sema = Semaphore(2)
    queue = Queue()
    pool = Pool(2)
    #queue = JoinableQueue()

    for i in range(5):
        res = pool.map_async(worker, [i])
        res.get()
    #queue.join()
