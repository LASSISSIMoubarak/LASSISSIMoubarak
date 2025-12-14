from multiprocessing import Process, current_process, Lock
import os 

def worker(lock):
    with lock:
        print('Process',current_process().name ,'is done')

if __name__ == "__main__":      

    lock = Lock()

    processes = []
    num_process = os.cpu_count()

    # create processes and asign a function for each process    
    for i in range(num_process):
        process = Process(name = i+1, target = worker, args=[lock])
        processes.append(process)

    # start all processes
    for process in processes:
        process.start()

    # wait for all processes to finish
    # block the main process until these processes are finished    
    for process in processes:
        process.join()