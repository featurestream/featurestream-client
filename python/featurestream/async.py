import threading
import sys

class AsyncTrainer (threading.Thread):
	stream = None
	it = None
	types = None

	running = True
	train_count = 0
	error_count = 0
	last_error = None
	batch = 1

	def __init__(self, stream, it, types, batch):
		threading.Thread.__init__(self)
		self.daemon = True
		self.stream = stream
		self.it = it
		self.batch = batch
		self.types = types

	def __repr__(self):
		return 'AsyncTrainer[stream_id='+str(self.stream.stream_id)+', is_running='+str(self.running)+', train_count='+str(self.train_count)+', error_count='+str(self.error_count)+', batch='+str(self.batch)+']'

	def run(self):
		if (self.batch < 1):
			print 'error: batch size cannot be < 1'
			return

		try:
			events = []
			for line in self.it:
				if line:
					events.append(line)
					if (len(events) >= self.batch):
						try:
							ok = self.stream.train_batch(events,self.types)
							if not ok:
								self.error_count += 1
								self.last_error = ('Error training batch')
							else:
								self.train_count += len(events)
						except:
							self.error_count += 1
							self.last_error = sys.exc_info()[:2]
						events = []
				if not self.running:
					self.it.close()
					break
			# any leftovers
			if (len(events)>0):
				try:
					ok = self.stream.train_batch(events,self.types)
					if not ok:
						self.error_count += 1
						self.last_error = ('Error training batch')
					else:
						self.train_count += len(events)
				except:
					self.error_count += 1
					self.last_error = sys.exc_info()[:2]
		finally:
			self.running = False

	def is_running(self):
		return self.running

	def stop(self):
		self.running = False

	def get_train_count(self):
		return self.train_count

	def get_error_count(self):
		return self.error_count

	def get_last_error(self):
		return self.last_error
