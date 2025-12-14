import torch as th 

class regressor:

	# x and y are tensors
	
	def __init__(self,x,y):
		self.beta = th.rand(x.size(1), requires_grad=True)
		self.likelihood = 0

	def grad_descent(self,epoch,learning):

		for i in range(epoch):

			self.likelihood =th.norm(y-x@self.beta)

			self.likelihood.backward()
	
			with th.no_grad():
				self.beta -=learning*self.beta.grad
				print(self.likelihood)

			self.beta.grad.zero_()

if __name__ == "__main__":  

	x = th.rand((100,3))
	y = x@th.tensor([1.0,2.0,3.0])+th.normal(mean=th.zeros(100)) 

	reg = regressor(x,y)
	reg.grad_descent(100,0.1)
	print(reg.beta)
		