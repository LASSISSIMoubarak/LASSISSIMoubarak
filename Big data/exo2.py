import threading
import time

def a():

    global run_status    
    stop = input()
    if stop == '':
        run_status = False

thread_a = threading.Thread(target=a)

stop_thread_a = False

thread_a.start()

c = 0
run_status = True

while run_status:
    c += 1
    print(c)
    time.sleep(1)

thread_a.join()
