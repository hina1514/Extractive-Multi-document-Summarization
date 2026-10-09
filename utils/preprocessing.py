import os
import re
from underthesea import sent_tokenize,word_tokenize
from utils.sentence import Sentence

class Preprocessing(object):
	def __init__(self):
		pass

	def processFilev2(self, file_path_and_name):
		try:

			with open(file_path_and_name, 'r', encoding='utf-8') as f:
				text = f.read()
				
			#Chỉ lấy nội dung 
			text_0 = text.split("Content:", 1)[1].strip()
			
			lines = sent_tokenize(text_0.strip())
        
			sentences = []

			for sent in lines:
				sent = sent.strip()
				OG_sent = sent[:]
				sent = sent.lower()
				line = word_tokenize(sent, format="text")

				if isinstance(line, str):
					processed_sentence = line.split()
				elif isinstance(line, list):
					processed_sentence = line
				else:
					continue
				
				processed_sentence = line.split()
				processed_sentence = [
                    word for word in processed_sentence
                    if word not in [
                        '.', ',', ';', ':', '!', '?',
                        '(', ')', '`', '_', '--',
                        '``', "''", "'s"
                    ]
                    and '&' not in word
                ]
				
				if (len(processed_sentence) <= 4):
					continue

				if processed_sentence:
					sentences.append(Sentence(file_path_and_name, processed_sentence, OG_sent))

			return sentences


		except IOError:
			print('Oops! File not found', file_path_and_name)
			return [Sentence(file_path_and_name, [], [])]

	def get_file_path(self, file_name):
		for root, dirs, files in os.walk(os.getcwd()):
			for name in files:
				if name == file_name:
					return os.path.join(root, name)
		print("Error! file was not found!!")
		return ""

	def get_all_files(self, path=None):
		retval = []

		if path == None:
			path = os.getcwd()

		for root, dirs, files in os.walk(path):
			for name in files:
				retval.append(os.path.join(root, name))
		return retval


	def openDirectory(self, directory):
		sentences = []
		last_indexs = []

		file_paths = []

		for root, dirs, files in os.walk(directory):
			dirs[:] = [d for d in dirs if not d.startswith(".")]

			for filename in files:
				if filename.lower().endswith(".txt"):
					file_paths.append(os.path.join(root, filename))

		file_paths.sort()

		for file_path in file_paths:
			last_indexs.append(len(sentences))

			file_sentences = self.processFilev2(file_path)

			file_sentences = [
				s for s in file_sentences
				if s.getProcessedWords()
			]

			sentences.extend(file_sentences)

		return sentences, last_indexs
