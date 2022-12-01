import os
import sys
import threading
import time
import subprocess
import uuid
import signal
import hashlib
import shutil

BASE_DIR="${BASE_DIR_PLACEHOLDER}".rstrip("/")

SCRATCH_DIR = BASE_DIR + "/scratch"
SCRATCH_DIR_VNAMES = BASE_DIR + "/scratch_var_names"

BUILD_DIR = BASE_DIR + "/build"

BUILDIT_INCLUDE_DIR = BASE_DIR + "/buildit/include"
BUILDIT_BUILD_DIR = BASE_DIR + "/buildit/build"
BUILDIT_BUILD_DIR_VNAMES = BASE_DIR + "/buildit/build_var_names"

BUILDIT_DIR = BASE_DIR + "/buildit"

CXX = "g++"

CXX_FLAGS = " -O3 -std=c++11 -static -I " + BUILDIT_INCLUDE_DIR + " "
CXX_FLAGS_AFTER = " -lbuildit -L " + BUILDIT_BUILD_DIR + " "

CXX_FLAGS_VNAMES = " -g -std=c++11 -static -I " + BUILDIT_INCLUDE_DIR + " -I " + BUILDIT_DIR + "/deps/libelfin/dwarf/ -I " + BUILDIT_DIR + "/deps/libelfin/elf/ "
CXX_FLAGS_AFTER_VNAMES = " -lbuildit -L " + BUILDIT_BUILD_DIR_VNAMES + " -L " + BUILDIT_DIR + "/deps/libelfin/dwarf -L " + BUILDIT_DIR + "/deps/libelfin/elf " + BASE_DIR + "/libunwind/install/usr/local/lib/libunwind.a -l:libelf++.a -l:libdwarf++.a -llzma " + BUILD_DIR + "/open.o " + BUILD_DIR + "/dladdr.o"

STATUS_RUNNING = 0
STATUS_COMPILE_ERROR = 1
STATUS_RUNTIME_ERROR = 2
STATUS_DONE = 3

class Queue:
	def __init__(self, main_mutex):
		self.queue = []
		self.main_mutex = main_mutex
	def enqueue(self, obj):
		self.main_mutex.acquire()
		try:
			self.queue.append(obj)
		finally:
			self.main_mutex.release()

	def dequeue(self):
		self.main_mutex.acquire()
		try:
			if len(self.queue) == 0:
				return None
			obj = self.queue[0]
			self.queue = self.queue[1:]
			return obj
		finally:
			self.main_mutex.release()


class QueueProcessor:
	def __init__(self, thread_count):
		self.main_mutex = threading.Lock()
		self.code_instance = 0
		self.queue = Queue(self.main_mutex)
		self.to_run = True
	
		self.hashtable = {}
		self.ready_compiled = []
		self.ready_compiled_vnames = []
			
		self.threads = []
		for i in range(thread_count):
			t = threading.Thread(target=self.thread_function)
			t.start()
			self.threads.append(t)

	def finish(self):
		self.to_run = False
		for t in self.threads:
			t.join()
		
	def set_status(self, new_id, status, scratch_to_use):
		f = open(scratch_to_use + "/p" + str(new_id) + "/status", "w")
		f.write(str(status))
		f.close()

	def compile_buildit_program(self, new_id, input_file, output_file, compile_error, recover_var_names):
		if recover_var_names != "1":	
			compile_command = CXX + CXX_FLAGS + input_file + " -o " + output_file + CXX_FLAGS_AFTER
		else:
			compile_command = CXX + CXX_FLAGS_VNAMES + input_file + " -o " + output_file + CXX_FLAGS_AFTER_VNAMES
		if recover_var_names == "1":
			scratch_to_use = SCRATCH_DIR_VNAMES
		else:	
			scratch_to_use = SCRATCH_DIR
		f = open(compile_error, "w")	
		try:
			output = subprocess.check_output(compile_command, stderr=f, shell=True)
		except:
			self.set_status(new_id, STATUS_COMPILE_ERROR, scratch_to_use)
			return 1
		finally:
			f.close()
		return 0
		
	def run_buildit_program(self, new_id, executable_name, output_file, execute_error, recover_var_names):
		command = BUILD_DIR + "/protect " + executable_name + " > " + output_file
		ferr = open(execute_error, "w")
		if recover_var_names == "1":
			scratch_to_use = SCRATCH_DIR_VNAMES
		else:	
			scratch_to_use = SCRATCH_DIR
		try:
			proc = subprocess.Popen(command, stderr = ferr, shell=True, preexec_fn=os.setsid)
			proc.communicate(timeout=2)
			if proc.returncode != 0:
				self.set_status(new_id, STATUS_RUNTIME_ERROR, scratch_to_use)
				return 1
		except subprocess.TimeoutExpired as e:
			os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
			ferr.close()
			ferr = open(execute_error, "w")
			ferr.write("Timed Out!");	
			self.set_status(new_id, STATUS_RUNTIME_ERROR, scratch_to_use)
			
			return 1	
		except Exception as e:
			print(e)
			self.set_status(new_id, STATUS_RUNTIME_ERROR, scrach_to_use)
			return 1
		finally:
			ferr.close()
		return 0

	def compile_and_run(self, new_id, recover_var_names):
		if recover_var_names == "1":
			scratch_to_use = SCRATCH_DIR_VNAMES
		else:	
			scratch_to_use = SCRATCH_DIR

		base_path = scratch_to_use + "/p" + str(new_id) + "/"		
		input_name = base_path + "input.cpp"
		error_name = base_path + "error.txt"
		executable_name = base_path + "a.out"
		output_name = base_path + "output.txt"	

		if (self.compile_buildit_program(new_id, input_name, executable_name, error_name, recover_var_names)):
			return 1
		
		if (self.run_buildit_program(new_id, executable_name, output_name, error_name, recover_var_names)):
			return 1	

		self.set_status(new_id, STATUS_DONE, scratch_to_use)
		return 0


	def thread_function(self):
		while self.to_run:
			dequeued = self.queue.dequeue()
			if dequeued == None:
				time.sleep(1)
				continue
			new_id, recover_var_names = dequeued
			self.compile_and_run(new_id, recover_var_names)
	
	def check_compiled(self, new_id, recover_var_names):
		self.main_mutex.acquire()
		if recover_var_names != "1":
			ret = new_id in self.ready_compiled
		else:
			ret = new_id in self.ready_compiled_vnames
			
		self.main_mutex.release()
		return ret
				
	def add_compiled(self, new_id, recover_var_names):
		self.main_mutex.acquire()
		if recover_var_names != "1":
			if new_id not in self.ready_compiled:
				self.ready_compiled += [new_id]
		else:
			if new_id not in self.ready_compiled_vnames:
				self.ready_compiled_vnames += [new_id]
			
		self.main_mutex.release()

	def get_id(self, code):
		hashm = hashlib.md5()
		hashm.update(code.encode())
		hashv = hashm.hexdigest()
		return hashv
			
	def process_snippet(self, code, recover_vars):
		new_id = self.get_id(code)
		if recover_vars == "1":
			scratch_to_use = SCRATCH_DIR_VNAMES
		else:	
			scratch_to_use = SCRATCH_DIR

		if self.check_compiled(new_id, recover_vars):
			return new_id
		try:
			if os.path.isdir(scratch_to_use + "/p" + str(new_id)):
				shutil.rmtree(scratch_to_use + "/p" + str(new_id))
			os.mkdir(scratch_to_use + "/p" + str(new_id))
			f = open(scratch_to_use + "/p" + str(new_id) + "/input.cpp", "w")
			f.write(code)
			f.close()
			self.set_status(new_id, STATUS_RUNNING, scratch_to_use)
			self.queue.enqueue((new_id, recover_vars))
			self.add_compiled(new_id, recover_vars)
			return new_id	
		except Exception as e:
			print (e)
			return -1
		
			

if __name__ == "__main__":
	QP = QueueProcessor(1)
	print(QP.process_snippet("#include<iostream>\nint main(void) {std::cout << \"Hello World\" << std::endl;}"))
	time.sleep(10)
	QP.finish()	
