import xml.etree.ElementTree as ETree
import networkx as nx
import matplotlib.pyplot as plt
import re
import json
__metaclass__ = type


class WordProb:
    def __init__(self, file_dir, prob_idx):
        self.prob_idx = prob_idx
        self.tree = ETree.parse(file_dir+'question-'+prob_idx+".xml")
        self.sentences = []
        self.corefs = []
        sentence_nodes = self.tree.findall(".//sentences/*")
        for n, sentence in enumerate(sentence_nodes):#should not tree.findall(".//sentence"), since "sentence" as a tag appears in "coreference" section
            if __name__ == '__main__': print 'sentence: %d' % n
            if n+1 == len(sentence_nodes):
                is_question_sentence = True
            else:
                is_question_sentence = False
            self.sentences.append(Sentence(sentence, is_question_sentence))

        for coref in self.tree.findall(".//coreference/coreference"):
            self.corefs.append(Coref(coref))

    def is_word_in_question_sentence(self, word):
        for sentence in self.sentences:
            if not sentence.is_question_sentence:
                continue
            for idx, token in enumerate(sentence.tokens):
                if word == token.lemma:
                    return True
        else:
            return False


class Sentence:
    def __init__(self, sentence_node, is_question_sentence):
        self.sentence_node = sentence_node
        self.tokens = []
        self.deps = []
        self.is_question_sentence = is_question_sentence

        for token in self.sentence_node.findall(".//token"):
            self.tokens.append(Token(token))

        for dep in self.sentence_node.find(".//dependencies[@type='collapsed-dependencies']"):
            self.deps.append(DepType(dep))

        if not is_question_sentence:
            self.is_question_sentence = self.contain_question_element()

        self.construct_dependency_graph()
        self.is_than_in_sentence, self.idx_of_than = self.is_contain_word('than')
        self.is_comp, self.idx_of_comp = self.get_comparative_nearby_than()

    def get_comparative_nearby_than(self):
        if not self.is_than_in_sentence:
            return False, None
        indexes = range(self.idx_of_than)
        indexes.reverse()
        for index in indexes:
            if self.tokens[index].POS in ['JJR', 'RBR']:
                return True, index
        else:
            return False, None


    def is_contain_pos(self, pos):
        for idx, token in enumerate(self.tokens):
            try:
                if token.POS in pos:
                    return True, idx
            except TypeError:
                if token.POS == pos:
                    return True, idx
        else:
            return False, None

    def is_contain_word(self, word):
        for idx, token in enumerate(self.tokens):
            if word == token.lemma or word == token.word:
                return True, idx
        else:
            return False, None

    def contain_question_element(self):
        if self.tokens[0].lemma.lower() == 'find':
            return True
        for token in self.tokens:
            if token.lemma.lower() in ['how', 'what']:
                return True
            if '?' in token.lemma:
                return True

    def construct_dependency_graph(self):
        self.dep_directed_graph = nx.DiGraph()
        for dep in self.deps:
            self.dep_directed_graph.add_weighted_edges_from([(dep.governor, dep.dependent, 1.0)], dep_type=dep.type)
        self.dep_undirected_graph = nx.Graph(self.dep_directed_graph)

    def get_path_info(self, path, include_dep_info=False):
        if len(path) < 2:
            return {}

        path_info = dict()
        path_info['path'] = path
        path_info['lemma'] = []
        path_info['POS'] = []
        path_info['dep_type'] = []
        for n, token_id in enumerate(path):
            if __name__ == '__main__': print self.tokens[token_id].lemma,
            if n != 0 and n+1 != len(path):
                path_info['lemma'].append(self.tokens[token_id].lemma)
            path_info['POS'].append(self.tokens[token_id].POS)
        if __name__ == '__main__': print '\n',
        if include_dep_info:
            for node1, node2 in zip(path[:-1], path[1:]):
                if __name__ == '__main__': print self.dep_undirected_graph[node1][node2]['dep_type']
                path_info['dep_type'].append(self.dep_undirected_graph[node1][node2]['dep_type'])

        return path_info

    def get_dep_shortest_path(self, s, t):
        if __name__ == '__main__': print self.tokens[s].lemma, '-->', self.tokens[t].lemma
        if s not in self.dep_directed_graph or t not in self.dep_directed_graph:
            return {}

        try:
            shortest_path = nx.shortest_path(self.dep_directed_graph, s, t)
        except nx.exception.NetworkXNoPath:
            shortest_path = nx.shortest_path(self.dep_undirected_graph, s, t)

        path_info = self.get_path_info(shortest_path, True)
        return path_info

    def get_raw_shortest_path(self, s, t):
        if s < 0 or s >= len(self.tokens):
            return {}

        if t < 0 or t >= len(self.tokens):
            return {}

        b = min(s, t)
        e = max(s, t)

        path_info = self.get_path_info(range(b, e+1))
        return path_info

    def get_word_dep_type(self, token_id, dir='double'):
        if token_id not in self.dep_directed_graph:
            return []
        if dir == 'out':
            edges = self.dep_directed_graph.out_edges(token_id, True)
        elif dir == 'in':
            edges = self.dep_directed_graph.in_edges(token_id, True)
        elif dir == 'double':
            edges = self.dep_undirected_graph.edges(token_id, True)
        else:
            print 'Bad dir parameter <', dir, '>'
            return []

        dep_type = []
        for edge in edges:
            dep_type.append(edge[-1]['dep_type'])
        return dep_type


class Token:
    multipliers = {'half': 0.5, 'twice': 2, 'double': 2, 'triple': 3, 'thrice': 3}
    str_numbers = {'two': 2, 'three': 3, 'four': 4, 'five': 5}
    numbers = {}
    numbers.update(str_numbers)
    numbers.update(multipliers)
    number_bases = {'million': 1000000}
    number_pattern = re.compile(r'-?[0-9]+((,[0-9]{3})*)?(\.[0-9]+)?')

    def __init__(self, token_node):
        self.token_node = token_node
        self.id = int(token_node.attrib['id'])-1

        for item in self.token_node:
            if item.text:
                # exec "self."+item.tag+"='"+item.text+"'"
                exec "self."+item.tag+'=item.text' # This line is used to deal with 's in the item.text which will cause error in the last line.
                if __name__ == "__main__": exec "print item.tag, self."+item.tag
            # exec "self."+eval("item.tag")+"='"+eval("item.text")+"'"
        # self.num is assigned in find_num
        self.num = None
        self.is_number = self.find_num()
        if self.is_number: print "<%g>" % self.num

    def find_num(self):

        if self.NER in ['ORDINAL']:
                return False

        if self.lemma in self.numbers:
            self.num = self.numbers[self.lemma]
            return True

        if self.POS == 'JJ':
            for str_num in self.numbers.keys():
                if self.lemma.find(str_num) != -1:
                    self.num = self.numbers[str_num]
                    return True
            num_match = re.search(self.number_pattern, self.lemma)
            if num_match:
                self.num = float(num_match.group(0))
                return True

        if (self.POS == 'CD' or self.NER == 'NUMBER') and self.lemma not in self.number_bases:
            if __name__ == '__main__': print "lemma", self.lemma
            # if self.NER == "DURATION":
            #     num_cnt = len(re.findall(Token.number_pattern, self.lemma))
            #     if num_cnt != 1:
            #         return False
            try:
                self.num = float(self.num_formulate(self.lemma))
                return True
            except ValueError:
                pass
            # try:
            if not hasattr(self, 'NormalizedNER'):
                return False
            if __name__ == '__main__': print "NormalizedNER", self.NormalizedNER

            num_match = re.search(self.number_pattern, self.lemma)
            if not num_match:
                num_match = re.search(self.number_pattern, self.NormalizedNER)
            # if token.NER == "NUMBER":
            #     num_match = re.search(self.number_pattern, token.NormalizedNER)
            # else:
            #     num_match = re.search(self.number_pattern, token.lemma)

            if num_match:
                self.num = float(self.num_formulate(num_match.group(0)))
                return True
            # except ValueError:
            #     num = float(self.num_formulate(token.lemma))
            # except AttributeError:
            #     return False
        return False

    @staticmethod
    def num_formulate(str_num):
        list_num = []
        for c in str_num:
            if c == ',':
                continue
            else:
                list_num.append(c)
        return ''.join(list_num)


class DepType:
    def __init__(self, dep_node):
        self.dep_node = dep_node
        self.type = dep_node.attrib["type"]
        self.governor = int(dep_node.find("governor").attrib["idx"])-1
        self.dependent = int(dep_node.find("dependent").attrib["idx"])-1

class Coref:
    def __init__(self, coref_node):
        self.coref_node = coref_node
        self.coref = []
        for item in self.coref_node.findall("./mention"):
            self.coref.append(CorefItem(item))

class CorefItem:
    def __init__(self, mention_node):
        self.mention_node = mention_node
        for item in self.mention_node:
            exec "self." + item.tag + '''=item.text'''
            if __name__ == '__main__': exec "print item.tag, self."+item.tag

def parse_json_word_prob_data(json_word_prob_file, word_prob_text_file, prob_idx_file):
    fp_json = open(json_word_prob_file, 'r')
    fp_text = open(word_prob_text_file, 'w')
    fp_idx = open(prob_idx_file, 'w')
    json_word_prob = json.load(fp_json)

    for word_prob in json_word_prob:
        print >>fp_text, word_prob['sQuestion']
        print >>fp_idx, word_prob['iIndex']

    fp_json.close()
    fp_text.close()
    fp_idx.close()


if __name__ == '__main__':
    parse_json_word_prob_data('./data/questions.json', './data/prob_text.txt', './data/prob_idx.txt')
    word_prob = WordProb("./parses/", "6952")
    word_prob = WordProb("./parses/", "397")
    word_prob = WordProb("./parses/", "1997")
    word_prob = WordProb("./parses/", "920")
    word_prob = WordProb("./parses/", "2598")
    print word_prob.sentences[0].get_raw_shortest_path(11, 13)
    print word_prob.sentences[0].get_dep_shortest_path(11, 13)
    word_prob = WordProb("./parses/", "6027")
    print word_prob.sentences[0].dep_directed_graph.in_edges(0)
    word_prob = WordProb("./parses/", "15")
    word_prob = WordProb("./parses/", "2575")
    print word_prob.sentences[0].get_dep_shortest_path(7, 10)
    print word_prob.sentences[0].get_word_dep_type(8,'out')
    print word_prob.sentences[0].get_word_dep_type(8,'in')
    print word_prob.sentences[0].get_word_dep_type(8)
    nx.draw_networkx(word_prob.sentences[0].dep_directed_graph)
    plt.show()
    print "Done"
# tree = ETree.parse("./parses/question-7.xml")
# root = tree.getroot()
# for sentence in root.findall(".//token[@id='1']/word"):
#     print sentence.text

