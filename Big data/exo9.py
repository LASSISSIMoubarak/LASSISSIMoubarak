import torch, time

import matplotlib.pyplot as plt 
import numpy as np
import random

d = 500

n_list = [i for i in range(100,10000,500)]
tensor_time = []
loop_time = []

for n in n_list:

	mean = [i for i in range(1,d+1)]
	cov = np.identity(d)

	# normal multivariate distribution 
	data = np.random.multivariate_normal(mean,cov,n)

	# tensoring computation
	start_time = time.time()
	
	A = torch.tensor(data, dtype = torch.float64,device = 'cpu')
	M = torch.ones(size=(d+1,n), dtype = torch.float64)/n
	mean_emp = M@A
	
	tensor_time.append(time.time()-start_time)

	# loop computation
	start_time = time.time()

	for i in range(d):
		mean_emp = np.mean(data,axis=0)
		
	loop_time.append(time.time()-start_time)

plt.plot(n_list,tensor_time,label='Tensor')
plt.plot(n_list,loop_time,label='Loop')

plt.xlabel('n')
plt.ylabel('Time in sec')
plt.legend(loc='upper left')
plt.show()

