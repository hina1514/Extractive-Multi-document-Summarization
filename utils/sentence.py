class Sentence(object):

	def __init__(self, docName, processedWords, OGwords):

		self.processedWords = processedWords
		self.docName = docName
		self.OGwords = OGwords
		self.wordFrequencies = self.sentenceWordFreqs()
		self.lexRankScore = None

	def getProcessedWords(self):
		return self.processedWords

	def getDocName(self):
		return self.docName

	def getOGwords(self):
		return self.OGwords

	def getWordFreqs(self):
		return self.wordFrequencies

	def getLexRankScore(self):
		return self.LexRankScore

	def setLexRankScore(self, score):
		self.LexRankScore = score

	def sentenceWordFreqs(self):
		wordFreqs = {}
		for word in self.processedWords:
			if word not in wordFreqs.keys():
				wordFreqs[word] = 1
			else:
				wordFreqs[word] = wordFreqs[word] + 1

		return wordFreqs