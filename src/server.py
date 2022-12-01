import buildit_queue
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
import os
import re

from urllib.parse import urlparse
from urllib.parse import parse_qs

MAX_THREADS = 2
BUILDIT_ONLINE_PORT = 8234

BASE_DIR="${BASE_DIR_PLACEHOLDER}".rstrip("/")
SCRATCH_DIR = BASE_DIR + "/scratch"
SCRATCH_DIR_VNAMES = BASE_DIR + "/scratch_var_names"

queue_process = None


def is_valid_id(new_id):
	if re.search("^[0-9a-f\-]*$", new_id):
		return True
	return False

class RequestHandler(BaseHTTPRequestHandler):
	def bad_request(self):	
		self.send_response(404)
		self.end_headers()

	def serve_file_for_id(self, new_id, filetype, recover_vars):

		if not is_valid_id(new_id):
			return self.bad_request()
		if recover_vars == "1":
			status_file = SCRATCH_DIR_VNAMES + "/p" + str(new_id) + "/" + filetype
		else:
			status_file = SCRATCH_DIR + "/p" + str(new_id) + "/" + filetype

		if not os.path.isfile(status_file):
			return self.bad_request()
		self.send_response(200)
		self.end_headers()
		data = open(status_file, "r").read()
		self.wfile.write(data.encode())
		return


	def do_GET(self):
		self.close_connection = True
		url = self.path
		parsed_url = urlparse(url)	
		params = parse_qs(parsed_url.query)
		if "recover_vars" in params:
			recover_vars = params["recover_vars"][0]
		else:
			recover_vars = "0"
		path = parsed_url.path

		if path == "/hello":
			self.send_response(200)
			self.end_headers()
			self.wfile.write(bytes("Hello from server", 'utf-8'))
			return
		elif path.startswith("/status/"):
			new_id = path.split("/status/")[1]
			return self.serve_file_for_id(new_id, "status", recover_vars)
		elif path.startswith("/result/"):
			new_id = path.split("/result/")[1]
			return self.serve_file_for_id(new_id, "output.txt", recover_vars)
		elif path.startswith("/error/"):
			new_id = path.split("/error/")[1]
			return self.serve_file_for_id(new_id, "error.txt", recover_vars)	
		elif path.startswith("/code/"):
			new_id = path.split("/code/")[1]
			return self.serve_file_for_id(new_id, "input.cpp", recover_vars)
		else:
			return self.bad_request()
	
	def do_POST(self):
		self.close_connection = True
		global queue_process
		url = self.path
		if url == "/run" or url == "/run_with_vars":
			if url == "/run":
				recover_vars = "0"
			else:
				recover_vars = "1"
			length = int(self.headers['Content-Length'])
			body = self.rfile.read(length)
			new_id = queue_process.process_snippet(body.decode(), recover_vars)
			if new_id == None:
				self.send_response(503)
				self.end_headers()
				return
			else:
				self.send_response(200)
				self.end_headers()
				self.wfile.write(bytes(str(new_id), 'utf-8'))
				return
		else:
			return self.bad_request()


class ThreadingBuildItServer(ThreadingMixIn, HTTPServer):
	pass	

def main():
	global queue_process
	queue_process = buildit_queue.QueueProcessor(MAX_THREADS)
	server = ThreadingBuildItServer(('0.0.0.0', BUILDIT_ONLINE_PORT), RequestHandler)
	try:	
		server.serve_forever()
	except:
		print("Killing server and all queues")
	queue_process.finish()
	server.server_close()
	
if __name__ == "__main__":
	main()	
