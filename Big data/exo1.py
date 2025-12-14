from threading import Thread, current_thread
import random as r
import time

def worker():
    time.sleep(r.randrange(1,4))
    print('Task number',current_thread().name ,'is done')

if __name__ == "__main__":        
    threads = []
    num_threads = 10

    # create threads and asign a function for each thread    
    for i in range(num_threads):
        thread = Thread(name = i+1, target = worker)
        threads.append(thread)

    # start all threads
    for thread in threads:
        thread.start()

    # wait for all threads to finish
    # block the main thread until these threads are finished    
    for thread in threads:
        thread.join()