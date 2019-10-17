import json
import solcrypto
import base64
import secrets

class SmartServer:
	def __init__(self, num_challs):
		self.challenges = solcrypto.generate_zksnarks_challenges(num_challs)
		self.polynomial = None
		self.uuid = base64.b64encode(secrets.randbits(512).to_bytes(64, byteorder='big')).decode('utf-8')

	def get_uuid(self):
		return self.uuid

	def load_polynomial(self, json_input):
		pol = json.loads(json_input)

		if 'polynomial' not in pol:
			print('Invalid polynomial json!')
			pol = None
			return

		self.polynomial = solcrypto.load_polynomial(pol['polynomial'])

	def load_polynomial_raw(self, pol):
		self.polynomial = pol

	def export_challenges(self):
		if self.challenges != None:
			return solcrypto.export_challenges(self.challenges[1])
		return None

	def verify_vote(self, vote_json):
		if self.challenges == None or self.polynomial == None:
			return None

		vote = json.loads(vote_json)
		if 'vote' not in vote:
			print('Invalid vote json!')
			vote = None
			return

		return solcrypto.verify_vote_polynomial(solcrypto.load_polynomial(vote['vote']), self.challenges[0], self.polynomial)

	def verify_vote_raw(self, vote_raw):
		return solcrypto.verify_vote_polynomial(vote_raw, self.challenges[0], self.polynomial)

	def evaluate(self):
		if self.challenges == None or self.polynomial == None:
			return None

		return solcrypto.server_evaluate_shares(self.polynomial, self.challenges[0])

class SmartClient:
	def __init__(self, num_challs):
		self.challenges = None
		self.polynomial = solcrypto.generate_zksnarks_vote_polynomial(num_challs)

	def load_challenges(self, json_input):
		challs = json.loads(json_input)

		if 'challenges' not in challs:
			print('Invalid challenge json!')
			challs = None
			return

		self.challenges = solcrypto.load_polynomial(challs['challenges'])
		return self.challenges

	def load_challenges_raw(self, challs):
		self.challenges = challs
		return challs

	def export_polynomial(self):
		if self.polynomial != None:
			return solcrypto.export_polynomial(self.polynomial[1])
		return None

	def create_vote(self, option):
		if self.polynomial == None or self.challenges == None:
			return None

		vote = solcrypto.create_vote(self.polynomial[0], self.challenges, option)
		return solcrypto.export_vote(vote)

	def evaluate(self):
		if self.challenges == None or self.polynomial == None:
			return None

		return solcrypto.client_evaluate_polynomial(self.polynomial[0], self.challenges)

def list_to_pol(l):
	return solcrypto.load_polynomial(l)
