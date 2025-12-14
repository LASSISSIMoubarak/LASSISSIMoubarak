from multiprocessing import Process, Pipe
import os 
import random
import time

def sender(pipe_in):
    
    while True:
        
        value = random.randrange(0,100,1)

        time.sleep(random.randrange(1,3))
        pipe_in.send(value)

def receiver(pipe_out):
    
    while True:
        
        time.sleep(1)

        if pipe_out.poll():
            print(pipe_out.recv())
        else:
            print(f'Waiting for data.')

if __name__ == "__main__":      


    (pipe_in, pipe_out) = Pipe()

    process_sender = Process(target = sender, args=[pipe_in])
    process_receiver = Process(target = receiver, args=[pipe_out])

    process_sender.start()
    process_receiver.start()

    time.sleep(30)

    process_sender.terminate()
    process_receiver.terminate()