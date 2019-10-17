import json
import ioplatform
from flask import Flask, request, jsonify
app = Flask(__name__)

class SmartEVote:
	def __init__(self):
		self.server_table = {}
		self.server_count = 0
		self.voters = []
		self.num_candidates = 10
		self.max_servers = 1500
		self.vote_poll = {}

		for i in range(self.num_candidates):
			self.vote_poll[i] = 1

	def new_server(self):
		if self.server_count >= self.max_servers:
			return None

		server = ioplatform.SmartServer(self.num_candidates)
		self.server_table[server.get_uuid()] = server
		self.server_count += 1

		print('Generated server with uuid {0}'.format(server.get_uuid()))
		return server

	def find_server(self, uuid):
		return self.server_table[uuid]

	def count_vote(self, uuid, remote_ip, candidate):
		del self.server_table[uuid]
		print('Voting was successful for server with uuid {0}, shutting down...'.format(uuid))
		self.voters += [remote_ip]

		if candidate in self.vote_poll:
			self.vote_poll[candidate] += 1

		print('Exit poll:' + repr(self.vote_poll))

	def has_voted(self, remote_ip):
		if remote_ip in self.voters:
			return True
		return False

evote_manager = SmartEVote()

@app.route('/api/challenge', methods=['POST'])
def generate_server():
	global evote_manager

	if evote_manager.has_voted(request.remote_addr):
		return 'You have already voted', 403

	if len(evote_manager.server_table) > evote_manager.max_servers:
		return "DoS Alert!", 403

	server = evote_manager.new_server()
	challs = json.loads(server.export_challenges())['challenges']
	return json.dumps({'uuid':server.get_uuid(), 'candidates':evote_manager.num_candidates, 'challenges':challs})

@app.route('/api/vote', methods=['POST'])
def cast_vote():
	global evote_manager

	if evote_manager.has_voted(request.remote_addr):
		return 'You have already voted', 403

	data = request.get_json(silent=True)
	if data == None:
		return 'Query refused by API', 400

	if 'polynomial' not in data or 'vote' not in data:
		print('Invalid vote received!')
		print(data)
		return 'Invalid vote received', 400

	uuid = data['uuid']
	pol = data['polynomial']
	vote = data['vote']

	server = None
	try:
		server = evote_manager.find_server(uuid)
	except:
		print('Could not find server with uuid {0}'.format(uuid))
		return 'Invalid server', 400

	pol = ioplatform.list_to_pol(pol)
	vote = ioplatform.list_to_pol(vote)

	server.load_polynomial_raw(pol)
	vote_result = server.verify_vote_raw(vote)

	print("Vote result is")
	print(vote_result)

	print('Evaluation')
	print(server.evaluate())

	if(vote_result[0] == 1):
		evote_manager.count_vote(uuid, request.remote_addr, vote_result[1][0])
	else:
		print('Error, tried to cast multiple votes!')
		return 'Error, tried to cast multiple votes!', 400
	return json.dumps(evote_manager.vote_poll), 200

if __name__ == '__main__':
	app.run(host='0.0.0.0')
