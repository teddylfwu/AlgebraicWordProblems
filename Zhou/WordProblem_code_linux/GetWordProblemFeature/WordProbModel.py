__author__ = 'zhoulipu'
from math import log

class WordProbModel:
    def __init__(self):
        self.feature_cnt = 0
        self.feature2idx = {}

        self.invalid_feaure = -1

    def set_feature(self, feature):
        if feature not in self.feature2idx:
            self.feature2idx[feature] = self.feature_cnt
            self.feature_cnt += 1
        return self.feature2idx[feature]

    def get_feature_idx(self, feature):
        return self.feature2idx.get(feature, self.invalid_feaure)

    def get_feature(self, feature, value, feature_map):
        idx = self.get_feature_idx(feature)
        if idx != self.invalid_feaure:
            feature_map[idx] = value

    def save(self, word_prob_model_dir):
        fp = open(word_prob_model_dir+"idx2ftr.txt", 'w')
        for feature_key, idx in sorted(self.feature2idx.items(), key=lambda x: x[-1]):
            print >>fp, idx, feature_key
        fp.close()

        fp = open(word_prob_model_dir+"ftr2idx.txt", 'w')
        for feature_key, idx in sorted(self.feature2idx.items(), key=lambda x: x[0]):
            print >>fp, feature_key, idx
        fp.close()


class NGram:
    stop_words = ['a', 'the', 'be', ',', '.','?']
    invalid_word = -1
    def __init__(self, word_probs):
        self.nGram = {}
        self.max_ngram = 1
        self.construct_ngram(word_probs)

    def construct_ngram(self, word_probs):
        for word_prob in word_probs:
            for word in self.get_words_in_prob(word_prob):
                self.nGram.setdefault(word, 0)
                self.nGram[word] += 1.0
        total = sum(self.nGram.values())
        for key, value in self.nGram.items():
            self.nGram[key] = 1.0
            # self.nGram[key] = log(total/value)
            # self.nGram[key] = 1.0/value

    def get_words_in_prob(self, word_prob):
        words = []
        for sentence in word_prob.sentences:
            for word in self.get_words_in_sentence(sentence):
                # yield word
                words.append(word)
        return words

    def get_words_in_sentence(self, sentence):
        words = []
        for index, token in enumerate(sentence.tokens):
            word = ''
            for n in range(self.max_ngram):
                if (index+n >= len(sentence.tokens)) or sentence.tokens[index+n].is_number or (sentence.tokens[index+n].lemma in self.stop_words):
                    break
                word += sentence.tokens[index+n].lemma
                # yield word
                words.append(word)
        return words

    def get_word_fudge(self, word):
        return self.nGram.get(word, self.invalid_word)

    def save(self, ngram_file):
        fp = open(ngram_file, 'w')
        for word, fudge in self.nGram.items():
            print >>fp, word, fudge
        fp.close()