# to run: python compression.py
# to use different files, modify the INPUT_FILENAME variable

import os
import struct
from subprocess import check_output
from collections import defaultdict
import heapq
import json

# Note: change this to run on different ascii art text files
INPUT_FILENAME = "data.txt" 

RUNLENGTH_PREFIX = "runlength_"
RUNLENGTH_MARKER = "R"
HUFFMAN_PREFIX = "huffman_"
HUFFMAN_MARKER = "H"
ENCODED_PREFIX = "encoded_"
DECODED_PREFIX = "decoded_"
EOF = -1

########## UTILITY FUNCTIONS ##########

# https://stackoverflow.com/questions/9590382/forcing-python-json-module-to-work-with-ascii
def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii')
    return dict(map(ascii_encode, pair) for pair in data.items())

# an end to end test that diffs the original input from the final 
# decoded output
def diff_decoding(original, decoding):
	diff_result = check_output(["diff", original, decoding])
	if len(diff_result) == 0:
		print "Diff: original and decoding match completely!"
	else: 
		print "Diff: "
		print diff_result

# bit reading utility function taken from the following stackoverflow post:
# https://stackoverflow.com/questions/2576712/using-python-how-can-i-read-the-bits-in-a-byte
def read_bits(f):
	bytes = (ord(b) for b in f.read())
	counter_g = 0

	for b in bytes:
		counter_g += 1
		# note that adding reversed gets us the higher order bits first
		for i in reversed(xrange(8)): 
			yield (b >> i) & 1

# takes in 8 bits in string form and returns the character translation
# eg. '01000000' -> '@'
def eight_bits_to_char(bits):
	return chr(int(bits, 2))


def percentageOfOriginal(size):
	original_size = float(os.stat(INPUT_FILENAME).st_size)
	return str((size / original_size) * 100) + "% of original size"

def remove_worse_compression(filename):
	huffman_stats = os.stat(HUFFMAN_PREFIX + filename)
	huffman_size = huffman_stats.st_size
	runlength_stats = os.stat(RUNLENGTH_PREFIX + filename)
	runlength_size = runlength_stats.st_size
	print "ENCODE: Huffman encoding - " + percentageOfOriginal(huffman_size)
	print "ENCODE: Run length encoding - " + percentageOfOriginal(runlength_size)
	if huffman_size < runlength_size:
		print "ENCODE: Huffman compression saved."
		os.remove(RUNLENGTH_PREFIX + filename)
		os.rename(HUFFMAN_PREFIX + filename, ENCODED_PREFIX + filename)
	else:
		print "ENCODE: Run length compression saved."
		os.remove(HUFFMAN_PREFIX + filename)
		os.rename(RUNLENGTH_PREFIX + filename, ENCODED_PREFIX + filename)

def decode(filename):
	#read first byte to determine compression type (note that we only need a bit, but that
	#would just involve an annoying one off bit manipulation)
	f = open(ENCODED_PREFIX + filename, "r")
	compression_type = f.read(1)
	decoded_result = ''

	if compression_type == 'R': #run length encoding
		print 'DECODE: Run length encoding found'
		decoded_result = decode_run_length(f)
	elif compression_type == 'H': #huffman encoding
		print 'DECODE: Huffman encoding found'
		decoded_result = decode_huffman(f)
	else:
		print 'DECODE: encoding type not recognized! abort.'
		return

	f = open(DECODED_PREFIX + filename, "w")
	f.write(decoded_result)
	f.close()
	print 'DECODE: Decoding complete!'

########## HUFFMAN FUNCTIONS ##########

class Node:
	def __init__(self, content, count, leftChild = None, rightChild = None):
		self.content = content
		self.count = count
		self.leftChild = leftChild
		self.rightChild = rightChild
	def isLeaf(self):
		return self.content != None

def build_frequency_table(f):
	frequency_counts = defaultdict(int)
	while True:
		letter = f.read(1)
		if not letter:
			frequency_counts[EOF] += 1
			break
		else:
			frequency_counts[letter] += 1
	return frequency_counts

def build_huffman_tree(frequency_counts):
	pq = []
	for tup in frequency_counts.iteritems():
		heapq.heappush(pq, (tup[1], Node(tup[0], tup[1])))

	while len(pq) > 1:
		node1 = heapq.heappop(pq)[1]
		node2 = heapq.heappop(pq)[1]
		new_node = Node(None, node1.count + node2.count, node1, node2)
		heapq.heappush(pq, (new_node.count, new_node))
	return heapq.heappop(pq)[1]

def get_huffman_encodings(huffman_node, curr_path, encodings):
	if huffman_node.isLeaf():
		encodings[huffman_node.content] = curr_path
	else:
		get_huffman_encodings(huffman_node.leftChild, curr_path + "0", encodings)
		get_huffman_encodings(huffman_node.rightChild, curr_path + "1", encodings)

def encode_huffman(filename):
	f = open(filename, "r")
	frequency_counts = build_frequency_table(f)
	f.close()
	huffman_root = build_huffman_tree(frequency_counts)
	encodings = dict()
	huffman_encodings = get_huffman_encodings(huffman_root, "", encodings)
	result = ''
	f = open(filename, "r")
	while True:
		letter = f.read(1)
		if not letter:
			break
		else:
			result += encodings[letter]
	result += encodings[EOF]
	padding = '0' * (8-(len(result) % 8))
	result += padding
	split_bits = [result[i:i+8] for i in range(0, len(result), 8)]

	output_file = open(HUFFMAN_PREFIX + filename, "w")
	output_file.write(HUFFMAN_MARKER)
	encoding_map_len = len(json.dumps(encodings))
	output_file.write(struct.pack('h', encoding_map_len))
	output_file.write(json.dumps(encodings))
	for eight_bits in split_bits:
		output_file.write(eight_bits_to_char(eight_bits))
	output_file.flush()
	output_file.close()

def decode_huffman(f):
	encoding_map_len = struct.unpack('h', f.read(2))[0]
	encodings = json.loads(f.read(encoding_map_len), object_hook=ascii_encode_dict)
	reverse_encodings = {value: key for key, value in encodings.iteritems()}
	result = ''
	curr_encoding = ''

	for b in read_bits(f):
		curr_encoding += str(b)
		if curr_encoding in reverse_encodings:
			if reverse_encodings[curr_encoding] == str(EOF):
				break
			else:
				result += reverse_encodings[curr_encoding]
				curr_encoding = ''
		
	return result

########## RUN LENGTH FUNCTIONS ##########

def encode_run_length(filename):
	output_file = open(RUNLENGTH_PREFIX + filename, "w")
	output_file.write(RUNLENGTH_MARKER)

	bits = ''
	curr_letter = None
	num_repetitions = 0

	for b in read_bits(open(filename, 'r')):
		bits += str(b)
		if len(bits) == 8:
			new_letter = eight_bits_to_char(bits)
			if curr_letter == None:
				curr_letter = new_letter
				num_repetitions = 1
			elif curr_letter == new_letter:
				num_repetitions += 1
			else:
				output_file.write(curr_letter)
				output_file.write(struct.pack('h', num_repetitions))
				curr_letter = new_letter
				num_repetitions = 1
			bits = ''
	#fencepost condition to get last set of consecutive letters
	output_file.write(curr_letter)
	output_file.write(struct.pack('h', num_repetitions))
	output_file.flush()
	output_file.close()

def decodeRLUnit(f):
	letter = f.read(1)
	if not letter:
		return None
	num_reps = struct.unpack('h', f.read(2))[0]
	return letter * num_reps

def decode_run_length(f):
	RLUnit = decodeRLUnit(f)
	result = ''
	while (RLUnit):
		result += RLUnit 
		RLUnit = decodeRLUnit(f)
	return result

def main(): 
	print "-----------------------------"
	encode_huffman(INPUT_FILENAME)
	encode_run_length(INPUT_FILENAME)
	remove_worse_compression(INPUT_FILENAME)

	print "-----------------------------"
	decode(INPUT_FILENAME)

	print "-----------------------------"
	diff_decoding(INPUT_FILENAME, DECODED_PREFIX + INPUT_FILENAME)

main()
