import fcntl

class SharedRWLock:
	def __init__(self,fn):
		self.fn=fn
		self.fi=file(fn,'a')
		self.fd=self.fi.fileno()

	def sharedLock(self):
		fcntl.flock(self.fd,fcntl.LOCK_SH)

	def exclusiveLock(self):
		fcntl.flock(self.fd,fcntl.LOCK_EX)

	def unlock(self):
		fcntl.flock(self.fd,fcntl.LOCK_UN)