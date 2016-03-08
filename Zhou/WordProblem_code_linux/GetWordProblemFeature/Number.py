from WordProbParser import *
__author__ = 'zhoulipu'

__metaclass__ = type
class Number:
    def __init__(self, num, token_id, sentence_id, sentence, is_in_question_sentence):
        self.num = num
        self.token_id = token_id
        self.sentence_id = sentence_id
        self.is_in_question_sentence = is_in_question_sentence
        self.nearby_noun = self.get_nearby_noun(sentence)
        self.is_multiplier = self.check_multiplier(sentence)
        self.is_than_in_sentence = sentence.is_than_in_sentence
        self.dis_to_than = None
        self.is_nearby_than = False
        self.noun_list = self.get_noun_list(sentence)
        if self.is_than_in_sentence:
            self.dis_to_than = sentence.idx_of_than - token_id
        print "number: <%g>" % num
        print "nearby noun: %s" % self.nearby_noun

    def get_noun_list(self, sentence):
        nouns = []
        for token in sentence.tokens:
            if 'NN' in token.POS and token.id != self.token_id:
                nouns.append(token)

        if len(nouns) == 0:
            return None

        noun_list = []
        for noun in nouns:
            num_to_noun_path = sentence.get_dep_shortest_path(self.token_id, noun.id)
            if num_to_noun_path:
                noun_list.append((noun, len(num_to_noun_path['path'])))

        if noun_list:
            noun_list.sort(key=lambda item: item[1])
        return noun_list

    def get_nearby_noun(self, sentence):
        if sentence.tokens[self.token_id].POS == "JJ":
            words = sentence.tokens[self.token_id].lemma.split('-')
            nearby_noun = ''
            for word in words:
                word = word.strip()
                num_match = re.search(Token.number_pattern, word)
                if not num_match:
                    nearby_noun += word.lower()
            return nearby_noun

        for edge in sentence.dep_directed_graph.in_edges(self.token_id, False):
            idx = edge[0]
            if 'NN' in sentence.tokens[idx].POS:
                return sentence.tokens[idx].lemma

        nouns = []
        for token in sentence.tokens:
            if 'NN' in token.POS and token.id != self.token_id:
                nouns.append(token)

        if len(nouns) == 0:
            return None

        nearby_noun = None
        shorted_path = None
        for noun in nouns:
            num_to_noun_path = sentence.get_dep_shortest_path(self.token_id, noun.id)
            if not nearby_noun or (num_to_noun_path and len(num_to_noun_path['path']) < shorted_path):
                shorted_path = len(num_to_noun_path['path'])
                nearby_noun = noun.lemma

        return nearby_noun

        # n = 1
        # while True:
        #     idx = self.token_id + n
        #     complete_search = True
        #     if idx < len(sentence.tokens):
        #         complete_search = False
        #         if "NN" in sentence.tokens[idx].POS:
        #             return sentence.tokens[idx].lemma
        #
        #     idx = self.token_id - n
        #     if idx >= 0:
        #         complete_search = False
        #         if "NN" in sentence.tokens[idx].POS:
        #             return sentence.tokens[idx].lemma
        #
        #     if complete_search:
        #         break
        #     n += 1

    def to_string(self):
        num_str = str(self.sentence_id) + "::" + str(self.token_id) + "::" + str(self.num)
        return num_str

    def check_multiplier(self, sentence):
        num_token = sentence.tokens[self.token_id]
        if num_token.lemma in Token.multipliers or num_token.lemma in ['time', 'product'] or abs(self.num) < 1:
            return True

        if self.token_id+1 < len(sentence.tokens):
            next_token = sentence.tokens[self.token_id+1]
            if next_token.lemma in ['time']:
                return True

            if next_token.lemma == 'of' and abs(self.num) < 1:
                return True

        return False
