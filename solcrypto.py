from fastecdsa.curve import secp256k1
from fastecdsa.point import Point
import hashlib
import base64
import secrets
import binascii
import json
import copy
from gmpy2 import invert

MAX_ITER         = 10**8
VOTE_TOKEN_START = b'X'

def hash(m):
	return hashlib.sha256(m).digest()

def inverse_exponent(e):
	return invert(e, secp256k1.q)

def generate_key():
	E = secp256k1
	G = E.G

	# Generate private nonce
	nonce = secrets.randbits(255)

	# Derive public key from curve generator
	Q = G * nonce

	return (Q, nonce)

def encrypt_message(key, m):
	if(len(m) > 31):
		raise Exception('Message is too long to be encrypted')

	msg = int(binascii.hexlify(m), 16)

	# Generate private nonce
	nonce = secrets.randbits(255)

	c1 = ((nonce * key).x + msg) % secp256k1.p
	c2 = nonce * secp256k1.G

	return (c1, c2)

def decrypt_message(pkey, c):
	c1 = c[0]
	c2 = c[1]

	decrypted = (c1 - (pkey * c2).x) % secp256k1.p
	return decrypted.to_bytes(32, byteorder='big')

def derive_shared_key(pkey, dkey):
	shared_key = hash(((pkey * dkey).x).to_bytes(32, byteorder='big'))
	return shared_key

def hmac_create(key, m):
	return hashlib.sha256(key + (key + m)).digest()

def hmac_verify(key, m, hmac):
	if hmac_create(key, m) == hmac:
		return True
	return False

def generate_zksnarks_challenges(num_challenges):
	s = int(secrets.randbits(255).to_bytes(32, byteorder='big').hex(), 16)

	j = 1
	secrets_array = []

	for i in range(num_challenges):
		secrets_array += [secp256k1.G * pow(s, j)]
		j += 1
	return (s, secrets_array)

def generate_zksnarks_vote_polynomial(num_challenges):
	coefficients = []

	for i in range(num_challenges):
		s = int(secrets.randbits(255).to_bytes(32, byteorder='big').hex(), 16)
		coefficients += [s]

	coefficients_encrypted = []
	for coeff in coefficients:
		coefficients_encrypted += [coeff * secp256k1.G]

	return (coefficients, coefficients_encrypted)

def create_vote(coefficients, secret, vote_candidate):
	vote_polynomial = copy.deepcopy(coefficients)
	rand_nonce = secrets.randbelow(secp256k1.p)

	for i in range(len(coefficients)):
		if i == vote_candidate:
			vote_polynomial[i] *= secret[i] * rand_nonce
		else:
			vote_polynomial[i] *= secret[i]

	return vote_polynomial

def client_evaluate_polynomial(pol, secret):
	evaluation = 0
	i = 0

	for result in pol:
		evaluation += (result * secret[i]).x
		i += 1
	return evaluation % secp256k1.p

def server_evaluate_shares(coefficients, secret):
	evaluation = 0
	i = 1
	for coeff in coefficients:
		evaluation += (pow(secret, i) * coeff).x
		i += 1
	return evaluation % secp256k1.p

def verify_vote_polynomial(vote_pol, secret_key, original_polynomial):
	vote_polynomial = vote_pol
	votes = 0
	i = 0
	voted_candidates = []
	tmp_vote = 0
	dkey = inverse_exponent(secret_key)

	for vote in vote_polynomial:
		tmp_vote = vote
		for j in range(i + 1):
			tmp_vote *= dkey

		if tmp_vote != original_polynomial[i]:
			voted_candidates += [i]
			votes += 1
		i += 1

	if votes != 1:
		print('Invalid number of votes received, dropped request')

	return (votes, voted_candidates)

def export_point(pt):
	return json.dumps({'x':pt.x, 'y':pt.y})

def export_challenges(challs):
	challenges = [(i.x, i.y) for i in challs]
	return json.dumps({'challenges':challenges})

def export_polynomial(pol):
	polynomial = [(i.x, i.y) for i in pol]
	return json.dumps({'polynomial':polynomial})

def export_vote(vote):
	vote = [(i.x, i.y) for i in vote]
	return json.dumps({'vote':vote})

def load_polynomial(vv):
	return [Point(pt[0], pt[1], curve=secp256k1) for pt in vv]
'''
# SERVER

challs = generate_zksnarks_challenges(10)

# CLIENT

pol = generate_zksnarks_vote_polynomial(10)
coefficients = pol[0]

print('Polynomial:\n' + repr(pol[0]))
vote = create_vote(coefficients, challs[1], 2)
print('Vote polynomial:\n' + repr(vote))
print(coefficients)
#######################################################33

# server gets polynomial and sends the challenges
# client evaluates

evaluation = client_evaluate_polynomial(coefficients, challs[1])
print('\nClient Evaluation:\n' + repr(evaluation))

server_eval = server_evaluate_shares(pol[1], challs[0])
print('\nServer Evaluation:\n' + repr(server_eval))

print('\nVerified vote:\n')
print(verify_vote_polynomial(vote, challs[0], pol[1]))

'''
