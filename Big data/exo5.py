from threading import Thread, current_thread, Lock
from queue import Queue

import random as r
import time

sum_up = 0

def worker(lock,q):

	global sum_up

	
	while q.empty() == False:
		
		value = q.get()
		time.sleep(r.randrange(1,4))

		with lock:
			local_copy = sum_up
			local_copy += 1
			sum_up = local_copy 
			print('Task number', value, 'is done.')
			q.task_done()

if __name__ == "__main__":

	lock = Lock()
	q = Queue()

	num_threads = 10
	num_tasks = 20

	for i in range(num_tasks):
		q.put(i+1)


	for i in range(num_threads):
		t = Thread(target=worker, args=(lock,q))
		t.start()

	q.join()
		
	print('Final sum equals', sum_up)
	



