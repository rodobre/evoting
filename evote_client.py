import ioplatform
import requests
import sys
import time
import json

class EVoteClient:
	def __init__(self, url):
		self.url = url
		self.instance = None
		self.server_uuid = None
		self.num_challenges = None
		self.challenges = None
		self.vote_pol = None

		fetch_challenge_url = url + 'api/challenge'
		req_data = requests.post(fetch_challenge_url, json={'timestamp':time.time()})

		if req_data.status_code != 200:
			print('Error, could not load server data! Error: {0}'.format(req_data.status_code))
			return

		data = req_data.json()

		if 'uuid' not in data or 'candidates' not in data or 'challenges' not in data:
			print('Invalid response received!')
			return

		self.server_uuid = data['uuid']
		self.num_challenges = data['candidates']
		challenges_json = ioplatform.list_to_pol(data['challenges'])

		self.instance = ioplatform.SmartClient(self.num_challenges)
		self.challenges = self.instance.load_challenges_raw(challenges_json)

	def submit_vote(self, option):
		if self.instance == None or self.challenges == None:
			print('Cannot submit vote when platform is not initialized!')
			return

		vote_url = self.url + 'api/vote'
		vote = json.loads(self.instance.create_vote(option))['vote']
		self.vote_pol = vote

		api_pol = json.loads(self.instance.export_polynomial())['polynomial']
		req_data = requests.post(vote_url, json={'uuid':self.server_uuid, 'polynomial':api_pol, 'vote':vote})

		if req_data.status_code == 200:
			print('Vote registered successfully')
		else:
			print('Vote could not be registered, error {0}'.format(req_data.status_code))

		print('Result:')
		print(req_data.text)

		print('Local evaluation:')
		print(self.instance.evaluate())

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('Error: Incorrect arguments. Syntax: {0} url candidate_id'.format(sys.argv[0]))
		sys.exit(0)

	url = sys.argv[1]
	candidate = int(sys.argv[2])

	if url[-1:] != '/':
		url = url + '/'

	evote = EVoteClient(url)
	evote.submit_vote(candidate)
