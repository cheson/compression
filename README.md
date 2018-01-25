# compression


To run, you can use "python compression.py". You can pass in different files
by changing the INPUT_FILENAME variable on line 12 of compression.py.



SUMMARY
The compression.py file contains code that takes in a filename as input and applies a compression algorithm to generate an encoded file. Two compressions are initially generated using both a Huffman encoding and a run-length encoding. They are differentiated using one character "R" or "H" inserted as the first byte of the encoding. The resulting encoding files are compared for size, and the smaller file is kept as the final compression of the input file. In reverse, each encoding can then be decoded as well by their respective algorithms.

RUN-LENGTH ENCODING
A run length encoding is an relatively naive algorithm that compresses text by replacing each sequence of consecutive characters with the character followed by its count. For example, "aaaabc" would be compressed to be "a4b1c1". It works best when there are long consecutive sequences of the same character because the entire sequence can be represented by just a character and a number. However, the tradeoff is single characters actually take up twice their original size in the encoding (eg "b" becomes "b1"). 
Interestingly, although run-length encoding is a lossless encoding, it is also incorporated into lossy compression algorithms like JPEG. 
Lastly, an interesting optimization I used for the number in this encoding is I outputted them as 2 byte shorts instead of the usual 4 byte int. I was able to do so because we know the bitmap sizes are limited to 100x100, or 10000 bytes. This means it is impossible to need more space than the SHORT_MAX of 65535. 

HUFFMAN ENCODING
source: https://en.wikipedia.org/wiki/Huffman_coding
source2: the class I TA for at school CS106B often uses Huffman encoding as one of their assignments to teach recursion, binary trees, and bit level manipulation so I was already familiar with this algorithm
Huffman encoding is a more complex algorithm that works by reassigning mappings to characters with a binary encoding. It takes advantage of the fact that each character is one byte, or 8 bits, but can be represented with less bits. For example, if we had the 8 byte input "ABABABAB", we could assign the bit 1 to A and the bit 0 to B and encode the input as "10101010", which we can save in 1 byte.
Specifically, this algorithm generates a huffman binary tree that places more frequent characters closer to the root and assigns less frequent characters farther from the root. The encoding of each character is then defined as the path from root to the leaf where the character is, using each left branch as 0 and each right branch as 1. Using this tree structure also guarantees the prefix property, meaning no character encoding will be the prefix of another character's encoding. If this were violated, there would be the following conflict: 
Assume A -> "0", B->"00", then when you are trying to decode "00", how would you know whether it was originally "AA" or "B"?
Anyway, this algorithm works well when frequent characters can be assigned short space saving encodings, and the less frequent characters can bear the cost of longer encodings. Feel free to email me at chesonatstanforddotedu or read the wikipedia article on Huffman encoding for more details. :)

COMPARISON
Note that compression.py takes the best of run-length encoding and Huffman encoding because different inputs have different properties, and each algorithm performs differently. As mentioned earlier, run-length performs exceptionally with long consecutive sequences of the same character, and huffman encoding works well if there is an even distribution of frequent and infrequent characters. 

TESTING
To test for functionality correctness, there is an end-to-end test performed. The original input file is compressed, then decoded, and the decoded result is diffed with the original input to check for correctness. 
