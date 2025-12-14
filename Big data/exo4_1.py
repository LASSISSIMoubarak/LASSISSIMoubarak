from threading import Thread, current_thread, Lock

import random as r
import time

sum_up = 0

def worker(lock):

	global sum_up

	time.sleep(r.randrange(1,4))

	with lock:
		local_copy = sum_up
		local_copy += 1
		sum_up = local_copy 
		print(f'Actual value is',sum_up)
		
if __name__ == "__main__":

	lock = Lock()

	threads = []
	num_threads = 100

	for i in range(num_threads):
		thread = Thread(name = i+1, target = worker, args=[lock])
		threads.append(thread)

	for thread in threads:
		thread.start()

	for thread in threads:
		thread.join()
		
	print('Final sum equals', sum_up)
	



