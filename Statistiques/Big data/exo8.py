from multiprocessing import Process
import multiprocessing as mp
import os 
import random
import time

def producteur(queue):
    print('Producteur: début', flush=True)
    for i in range(10):
        value = random.randrange(1,3)
        time.sleep(value)
        queue.put(value)
    queue.put(None)
    print('Producteur: fin', flush=True)

def consommateur(queue):
    print('Consommateur: début', flush=True)
    while True:
        item = queue.get(timeout=3)
        
        if not item:
            break
        
        print(f'>retire {item}', flush=True)
    
    print('Consommateur: fin', flush=True)

if __name__ == "__main__":      


    q = mp.Queue()

    process_sender = Process(target = producteur, args=[q])
    process_receiver = Process(target = consommateur, args=[q])

    process_sender.start()
    process_receiver.start()

    process_sender.join()
    process_receiver.join()