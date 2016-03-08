from __future__ import division
from WordProbParser import *
from sympy.solvers import solve
from sympy import symbols
from math import log
from WordProbModel import *
from time import time
from Number import *
import EquationSolution
import re
import sys
import os

__metaclass__ = type
class WordProbFeature:
    permutations = {}

    def __init__(self, sol_info, parser_rlt, ngram_model):
        #self.index = index
        self.sol_info = sol_info
        self.parser_rlt = parser_rlt
        self.nums = []
        self.start_var = 'a'
        self.var_num = self.get_var_num(sol_info.equ_template, self.start_var)
        self.word_window_size = 5
        self.get_nums()
        self.ngram_model = ngram_model
        self.max_nearby_dist = 5
        self.cache = {}
        self.semi_supervised = None
        self.use_equation_feature = False
        self.use_sub_equ_feature = False
        self.use_solution_feature = True
        self.use_single_slot_feature = True
        self.use_double_slots_feature = True

    def get_nums(self):
        valid_nums = []
        for sentence_id, sentence in enumerate(self.parser_rlt.sentences):
            nums_in_sentence = []
            for token in sentence.tokens:
                if token.is_number:
                    if not sentence.is_question_sentence:
                        # self.nums.append(Number(token.num, token.id, sentence_id, sentence, False))
                        nums_in_sentence.append(Number(token.num, token.id, sentence_id, sentence, False))
                        valid_nums.append(token.num)
                    else:
                        q_num = Number(token.num, token.id, sentence_id, sentence, True)
                        for num in self.nums:
                            if num.num == q_num.num and num.nearby_noun == q_num.nearby_noun:
                                break
                        else:
                            # self.nums.append(q_num)
                            nums_in_sentence.append(q_num)
                            valid_nums.append(token.num)
            if sentence.is_than_in_sentence and nums_in_sentence:
                num_nearby_than_idx = None
                if len(nums_in_sentence) == 1:
                    num_nearby_than_idx = 0
                else:
                    min_dis_to_than = len(sentence.tokens)
                    for idx, num in enumerate(nums_in_sentence):
                        if 0 < num.dis_to_than < min_dis_to_than:
                            min_dis_to_than = num.dis_to_than
                            num_nearby_than_idx = idx
                nums_in_sentence[num_nearby_than_idx].is_nearby_than = True

            self.nums.extend(nums_in_sentence)

    @staticmethod
    def get_var_num(equ, start_var):
        n = 0
        while True:
            if equ.find(start_var) == -1:
                return n
            else:
                start_var = chr(ord(start_var)+1)
                n = n+1

    @staticmethod
    def permutate(data, n):
        if len(data) < n or n <= 0:
            return []

        permutations = []
        for index, item in enumerate(data):
            if n == 1:
                # yield [item]
                permutations.append([item])
            else:
                _data = data[:]
                del _data[index]
                for sub_seq in WordProbFeature.permutate(_data, n-1):
                    # yield [data[index]]+sub_seq
                    permutations.append([data[index]]+sub_seq)
        return permutations

    def get_num_alignments(self, m):
        n = len(self.nums)
        if n not in WordProbFeature.permutations:
            WordProbFeature.permutations[n] = {}
        if m not in WordProbFeature.permutations[n]:
            WordProbFeature.permutations[n][m] = WordProbFeature.permutate(range(n), m)

        num_alignments = []
        permutations = WordProbFeature.permutations[n][m]
        for permutation in permutations:
            num_alignment = []
            for idx in permutation:
                num_alignment.append(self.nums[idx])
            num_alignments.append(num_alignment)

        return num_alignments


    def construct_equation(self, num_permutation, equ_template):
        equation = equ_template
        for index, num in enumerate(num_permutation):
            var = chr(ord(self.start_var)+index)
            equation = equation.replace(var, str(num.num))
        return equation

    @staticmethod
    def is_correct_numerically(correct_ans_element, calculated_ans):
        for calculated_ans_element in calculated_ans:
            if calculated_ans_element == correct_ans_element:
                return True

        for calculated_ans_element in calculated_ans:
            if correct_ans_element == 0:
                if abs(calculated_ans_element) < 0.000001:
                    return True
            else:
                if abs(calculated_ans_element-correct_ans_element) < 0.000001:
                      return True
        else:
            return False

    @staticmethod
    def get_solution(equation):
        equation = equation.strip(' ,')
        equation = equation.replace('= 0', '')
        m, n = symbols('m n')
        equation = 'solve([' + equation + ']' + ',[m,n])'
        _result = eval(equation)
        result = []
        # print _result
        if _result:
            for value in _result.values():
                try:
                    result.append(float(value))
                except TypeError:
                    continue
        return result

    def is_correct_alignment(self, num_alignment, equ_template):
        #equation = self.construct_equation(num_alignment, equ_template)
        #solution = self.get_solution(equation)
        nums = []
        for num in num_alignment:
            nums.append(num.num)
        solution = EquationSolution.calc_word_prob[equ_template](*nums)
        for ans_element in self.sol_info.ans:
            if not self.is_correct_numerically(ans_element, solution):
                return False
        else:
            return True

    def validate_num_alignment(self):
        n = 0
        for num_alignment in self.permutate(self.nums, self.var_num):
            if self.is_correct_alignment(num_alignment, self.sol_info.equ_template):
                # print "Find correct alignment"
                print "<", n, ">", self.construct_equation(num_alignment, self.sol_info.equ_template)
                nums = []
                for num in num_alignment:
                    nums.append(num.num)
                print EquationSolution.calc_word_prob[self.sol_info.equ_template](*nums)
                n = n+1
                find_correct_alignment = True
                # return True
            # else:
            #     yield False, num_alignment
        if n == 0:
            fp = open('error_num_alignment.txt', 'a')
            print >>fp, self.parser_rlt.prob_idx
            fp.close()
            raise Exception

    def get_word_feature(self, signature, word, feature_map):
        idf = self.ngram_model.get_word_fudge(word)
        if idf != self.ngram_model.invalid_word:
            feature = signature + "::" + word
            feature_map[feature] = idf
            return True
        else:
            return False

    def get_equation_feature(self, equ_template):
        if not self.use_equation_feature:
            return {}
        ngram_feature = {}
        for word in self.ngram_model.get_words_in_prob(self.parser_rlt):
            self.get_word_feature(equ_template, word, ngram_feature)
        ngram_feature[equ_template+'::sentence_size'] = len(self.parser_rlt.sentences)
        return ngram_feature

    def get_word_env(self, signature, sentence, token_id):
        word_env = {}
        word_env['POS'] = {}
        word_env['DepType'] = {}
        word_env['lemma'] = {}
        start = max(0, token_id - self.word_window_size)
        end = min(token_id + self.word_window_size, len(sentence.tokens)-1)
        for n in range(start, end+1):
            if n == token_id:
                continue
            if sentence.tokens[n].lemma in self.ngram_model.stop_words:
                continue
            self.get_word_feature(signature, sentence.tokens[n].lemma, word_env['lemma'])
            feature = signature+"::"+sentence.tokens[n].POS
            word_env['POS'].setdefault(feature, 0)
            word_env['POS'][feature] += 1
            for dep_type in sentence.get_word_dep_type(n):
                feature = signature+"::"+dep_type
                word_env['DepType'].setdefault(feature, 0)
                word_env['DepType'][feature] += 1
        return word_env

    def get_solution_feature(self, equ_template, solution):
        if not self.use_solution_feature:
            return {}

        if not solution:
            return {}

        solution_feature = {}
        bPos = True
        bPosInteger = True
        bPosLessThanOne = True
        for x in solution:
            if x < 0:
                bPos = False
                bPosInteger = False
                bPosLessThanOne = False
            if abs(int(x) - x) > 0.00001:
                bPosInteger = False
            if x > 1:
                bPosLessThanOne = False

        if bPos:
            solution_feature[equ_template+"::pos_solution"] = 1

        if bPosInteger:
            solution_feature[equ_template+"::pos_integer_solution"] = 1

        if bPosLessThanOne:
            solution_feature[equ_template+"::pos_less_than_one_solution"] = 1

        return solution_feature

    def get_cached_feature(self, slot_signature, prefix_feature_signature, feature):
        if slot_signature in self.cache:
            for postfix_feature_signature, value in self.cache[slot_signature].items():
                feature[prefix_feature_signature+postfix_feature_signature] = value
            return True
        else:
            return False

    def set_and_cache_feature(self, slot_signature, prefix_feature_signature, postfix_feature_signature, feature, value):
        feature[prefix_feature_signature+postfix_feature_signature] = value
        if slot_signature in self.cache:
            self.cache[slot_signature][postfix_feature_signature] = value
        else:
            self.cache[slot_signature] = dict()
            self.cache[slot_signature][postfix_feature_signature] = value

    def get_single_slot_comparison_feature(self, num, slot_signature, feature_prefix, single_slot_feature):
        if not num.is_than_in_sentence:
            return

        if num.is_nearby_than:
            #single_slot_feature[feature_prefix+"::nearby_than"] = 1
            self.set_and_cache_feature(slot_signature, feature_prefix, "::nearby_than", single_slot_feature, 1)
            return

        sentence = self.parser_rlt.sentences[num.sentence_id]
        comp_word = "than"
        if sentence.is_comp:
            comp_word = sentence.tokens[sentence.idx_of_comp].lemma

        if num.is_multiplier:
            if num.token_id - sentence.idx_of_than < 0:
                #single_slot_feature[feature_prefix+"::num_left_to_"+comp_word] = 1
                self.set_and_cache_feature(slot_signature, feature_prefix, "::num_left_to_"+comp_word, single_slot_feature, 1)
            else:
                #single_slot_feature[feature_prefix+"::num_right_to_"+comp_word] = 1
                self.set_and_cache_feature(slot_signature, feature_prefix, "::num_right_to_"+comp_word, single_slot_feature, 1)

    def get_single_slot_context_feature(self, num, slot_signature, feature_prefix, single_slot_feature):
        # Features for the num itself.
        sentence = self.parser_rlt.sentences[num.sentence_id]
        num_token = sentence.tokens[num.token_id]
        if num_token.POS != 'CD' or num_token.NER != 'NUMBER':
            if num.nearby_noun:
                self.set_and_cache_feature(slot_signature, feature_prefix, "::num_lemma::"+num.nearby_noun, single_slot_feature, 1)
                self.set_and_cache_feature(slot_signature, feature_prefix, "::num_POS::"+num_token.POS, single_slot_feature, 1)
                self.set_and_cache_feature(slot_signature, feature_prefix, "::num_NER::"+num_token.NER, single_slot_feature, 1)

                for dep_type in sentence.get_word_dep_type(num.token_id):
                    self.set_and_cache_feature(slot_signature, feature_prefix, "::num_dep_type::"+dep_type, single_slot_feature, 1)

        # Features for the surrounding words
        word_env = self.get_word_env("", sentence, num.token_id)
        for feature_tag, values in word_env.items():
            for postfix_feature_signature, value in values.items():
                self.set_and_cache_feature(slot_signature, feature_prefix, postfix_feature_signature, single_slot_feature, value)
                # single_slot_feature.update(feature)


    def get_single_slot_feature(self, equ_template, num_alignment):
        if not self.use_single_slot_feature:
            return {}
        single_slot_feature = {}
        for idx, num in enumerate(num_alignment):
            signature = equ_template+"::"+chr(ord(self.start_var)+idx)
            slot_signature =num.to_string()

            sentence = self.parser_rlt.sentences[num.sentence_id]
            num_token = sentence.tokens[num.token_id]

            if num_token.num in [1, 2]:
                if not num.is_multiplier:
                    single_slot_feature["num_is_one_or_two"] = 1

            if self.get_cached_feature(slot_signature, signature, single_slot_feature):
                continue

            set_and_cache_single_slot_feature = lambda postfix_feature_signature, value: self.set_and_cache_feature(slot_signature, signature, postfix_feature_signature, single_slot_feature, value)

            if 0 < num.num < 1:
                set_and_cache_single_slot_feature("::between_0_and_1", 1)

            if num.is_multiplier:
                self.set_and_cache_feature(slot_signature, signature, "::is_multiplier", single_slot_feature, 1)

            if num.is_in_question_sentence:
                self.set_and_cache_feature(slot_signature, signature, "::question_num", single_slot_feature, 1)
                # single_slot_feature[signature+"::question_num"] = 1

            if num.nearby_noun and self.parser_rlt.is_word_in_question_sentence(num.nearby_noun):
                self.set_and_cache_feature(slot_signature, signature, "::max_relation_to_question", single_slot_feature, 1)
                # single_slot_feature[signature+"::nearby_num_in_question"] = 1
            elif num.noun_list:
                for position, noun in enumerate(num.noun_list):
                    if self.parser_rlt.is_word_in_question_sentence(noun):
                        set_and_cache_single_slot_feature("::relation_to_question", 1./(position+1))
                        break

            self.get_single_slot_context_feature(num, slot_signature, signature, single_slot_feature)
            self.get_single_slot_comparison_feature(num, slot_signature, signature, single_slot_feature)

        return single_slot_feature

    @staticmethod
    def get_word_env_similarity(word_env1, word_env2):
        similarity = {}
        for key, value in word_env1.items():
            set1 = set(value.keys())
            set2 = set(word_env2[key].keys())
            similarity[key+"_sim"] = float(len(set1 & set2))/float(len(set1 | set2))
        return similarity

    def has_coref_relation(self, sentence_id1, sentence_id2):
        for coref in self.parser_rlt.corefs:
            coref_sentence_ids = []
            for mention in coref.coref:
                coref_sentence_ids.append(mention.sentence)
            if sentence_id1 in coref_sentence_ids and sentence_id2 in coref_sentence_ids:
                return True
        else:
            return False

    def set_path_info(self, path_info, slot_signature, prefix_feature_signature, post_feature_signature, feature):
        for key, value in path_info.items():
            if key != 'path':
                for item in value:
                    feature_signature = post_feature_signature+"::"+key+"::"+item
                    self.set_and_cache_feature(slot_signature, prefix_feature_signature, feature_signature, feature, 1)
                    # double_slots_feature[signature+"::path::"+key+"::"+item] = 1

    def get_matched_noun_score(self, num1, num2):
        max_pair_score = 0
        matched_noun = None
        if (not num1.noun_list) or (not num2.noun_list):
            return 0
        for idx1, token1 in enumerate(num1.noun_list):
            noun1 = token1[0].lemma
            for idx2, token2 in enumerate(num2.noun_list):
                noun2 = token2[0].lemma
                if noun1 == noun2:
                    pair_score = 2.0/(idx1+1+idx2+1)
                    if max_pair_score < pair_score:
                        max_pair_score = pair_score
                        matched_noun = noun1
        return max_pair_score

    def get_two_number_relation_feature(self, num1, num2, double_slots_signature, feature_prefix, double_slots_feature):
        set_and_cache_double_slot_feature = lambda postfix_feature_signature, value: self.set_and_cache_feature(double_slots_signature, feature_prefix, postfix_feature_signature, double_slots_feature, value)
        if num1.nearby_noun == num2.nearby_noun:
            set_and_cache_double_slot_feature("::same_nearby_noun", 1)
            #self.set_and_cache_feature(double_slots_signature, feature_prefix, "::same_nearby_noun", double_slots_feature, 1)
            # double_slots_feature[signature+"::same_nearby_noun"] = 1
        else:
            noun_pair_score = self.get_matched_noun_score(num1, num2)
            if noun_pair_score:
                set_and_cache_double_slot_feature("::noun_relationship", noun_pair_score)
                # self.set_and_cache_feature(double_slots_signature, signature, "::noun_relationship", double_slots_feature, noun_pair_score)

    def get_double_slot_feature(self, equ_template, num_alignment, variables=None):
        if not self.use_double_slots_feature:
            return {}
        double_slots_feature = {}
        n = len(num_alignment)

        for i in range(n):
            num1 = num_alignment[i]
            var1 = chr(ord(self.start_var)+i)
            if variables:
                var1 = variables[i]

            word_env1 = self.get_word_env("", self.parser_rlt.sentences[num1.sentence_id], num1.token_id)
            for j in range(i+1, n):
                num2 = num_alignment[j]
                var2 = chr(ord(self.start_var)+j)
                if variables:
                    var2 = variables[j]
                signature = equ_template+"::"+var1+"::"+var2
                double_slots_signature =num1.to_string() + "->" + num2.to_string()

                # self.get_double_slots_comparison_feature(num1, num2, signature, double_slots_feature)

                set_and_cache_double_slot_feature = lambda postfix_feature_signature, value: self.set_and_cache_feature(double_slots_signature, signature, postfix_feature_signature, double_slots_feature, value)

                if self.get_cached_feature(double_slots_signature, signature, double_slots_feature):
                    continue

                word_env2 = self.get_word_env("", self.parser_rlt.sentences[num2.sentence_id], num2.token_id)
                word_env_sim = self.get_word_env_similarity(word_env1, word_env2)

                for key, value in word_env_sim.items():
                    set_and_cache_double_slot_feature("::"+key, value)
                    # self.set_and_cache_feature(double_slots_signature, signature, "::"+key, double_slots_feature, value)

                if self.has_coref_relation(num1.sentence_id, num2.sentence_id):
                    set_and_cache_double_slot_feature("::coref_relation", 1)
                    # self.set_and_cache_feature(double_slots_signature, signature, "::coref_relation", double_slots_feature, 1)

                if num1.is_multiplier and num2.is_multiplier:
                    set_and_cache_double_slot_feature("::connect_two_multiplier", 1)

                self.get_two_number_relation_feature(num1, num2, double_slots_signature, signature, double_slots_feature)

                if num1.num >= num2.num:
                    set_and_cache_double_slot_feature("::num1_greater_than_num2", 1)
                    #self.set_and_cache_feature(double_slots_signature, signature, "::num1_greater_than_num2", double_slots_feature, 1)
                    # double_slots_feature[signature+"::num1_greater_than_num2"] = 1
                else:
                    set_and_cache_double_slot_feature("::num2_greater_than_num1", 1)
                    #self.set_and_cache_feature(double_slots_signature, signature, "::num2_greater_than_num1", double_slots_feature, 1)
                    # double_slots_feature[signature+"::num2_greater_than_num1"] = 1

                if num1.sentence_id == num2.sentence_id:
                    set_and_cache_double_slot_feature("::in_same_sentence", 1)
                    # self.set_and_cache_feature(double_slots_signature, signature, "::in_same_sentence", double_slots_feature, 1)
                    # double_slots_feature[signature+"::in_same_sentence"] = 1
                # else:
                #     self.set_and_cache_feature(double_slots_signature, signature, "::in_different_sentence", double_slots_feature, 1)

                if abs(num1.sentence_id - num2.sentence_id) == 1:
                    set_and_cache_double_slot_feature("::in_continue_sentences", 1)
                    # self.set_and_cache_feature(double_slots_signature, signature, "::in_continue_sentences", double_slots_feature, 1)
                # else:
                #     self.set_and_cache_feature(double_slots_signature, signature, "::in_discontinue_sentences", double_slots_feature, 1)

                # Raw path and dependency path information
                if num1.sentence_id == num2.sentence_id:
                    dep_path_info = self.parser_rlt.sentences[num1.sentence_id].get_dep_shortest_path(num1.token_id, num2.token_id)
                    self.set_path_info(dep_path_info, double_slots_signature, signature, "::dep_path", double_slots_feature)
                    if len(dep_path_info['dep_type']) == 1:
                        set_and_cache_double_slot_feature("::dep_type_between_two_number::"+dep_path_info['dep_type'][0], 1)
                        # self.set_and_cache_feature(double_slots_signature, signature, "::dep_type_between_two_number::"+dep_path_info['dep_type'][0], double_slots_feature, 1)

                    raw_path_info = self.parser_rlt.sentences[num1.sentence_id].get_raw_shortest_path(num1.token_id, num2.token_id)
                    self.set_path_info(raw_path_info, double_slots_signature, signature, "::raw_path", double_slots_feature)
                    if len(raw_path_info['lemma']) == 1:
                        set_and_cache_double_slot_feature("::"+"::".join(raw_path_info['POS']), 1)
                        set_and_cache_double_slot_feature("::two_numbers_connected_by_"+raw_path_info['lemma'][0], 1)
                        # self.set_and_cache_feature(double_slots_signature, signature, "::"+"::".join(raw_path_info['POS']), double_slots_feature, 1)
                        # self.set_and_cache_feature(double_slots_signature, signature, "::two_numbers_connected_by_"+raw_path_info['lemma'][0], double_slots_feature, 1)
                    elif abs(num1.token_id - num2.token_id) <= self.max_nearby_dist:
                        set_and_cache_double_slot_feature("::two_numbers_nearby_each_other", 1)
                        # self.set_and_cache_feature(double_slots_signature, signature, "::two_numbers_nearby_each_other", double_slots_feature, 1)
                        # double_slots_feature[signature+"::two_numbers_nearby_each_other"] = 1
                    elif "and" in raw_path_info['lemma']:
                        set_and_cache_double_slot_feature("::path_between_two_numbers_has_and", 1)
                        #self.set_and_cache_feature(double_slots_signature, signature, "::path_between_two_numbers_has_and", double_slots_feature, 1)
                    # elif "than" in raw_path_info['lemma']:
                    #     set_and_cache_double_slot_feature("::path_between_two_numbers_has_than", 1)


        return double_slots_feature

    # def ngram_feauture(self, equ_template, word_prob_model, flag):
    #     ngram_feature = {}
    #     for feature, idf in self.get_ngram_feature(equ_template):
    #         if flag == 'set':
    #             id, fudge = word_prob_model.set_feature(feature, idf)
    #         elif flag == 'get':
    #             id, fudge = word_prob_model.get_feature(feature)
    #         else:
    #             raise Exception('flag is unknown')
    #         if id != word_prob_model.invalid_feaure:
    #             ngram_feature[id] = fudge
    #     return ngram_feature

    def get_feature_for_one_template(self, equ_template):
        features = []
        num_alignments = []
        ngram_feature = self.get_equation_feature(equ_template)
        var_num = self.get_var_num(equ_template, self.start_var)
        for num_alignment in self.get_num_alignments(var_num):
        # for num_alignment in self.permutate(self.nums, self.get_var_num(equ_template, self.start_var)):
            if var_num != len(num_alignment):
                raise Exception
            nums = []
            for num in num_alignment:
                nums.append(num.num)
            solution = EquationSolution.calc_word_prob[equ_template](*nums)
            if not solution:
                continue

            solution_feature = self.get_solution_feature(equ_template, solution)
            #sub_equ_feature = self.get_sub_equ_feature(equ_template, num_alignment)
            single_slot_feature = self.get_single_slot_feature(equ_template, num_alignment)
            double_slot_feature = self.get_double_slot_feature(equ_template, num_alignment)
            feature = {}
            feature.update(ngram_feature)
            feature.update(solution_feature)
            #feature.update(sub_equ_feature)
            feature.update(single_slot_feature)
            feature.update(double_slot_feature)
            num_alignments.append(num_alignment)
            features.append(feature)
        return features, num_alignments

    def feature_map_for_one_template(self, equ_template, word_prob_model, flag):
        features, num_alignments = self.get_feature_for_one_template(equ_template)
        feature_maps = []
        for feature, num_alignment in zip(features, num_alignments):
            feature_map = {}
            for feature_key, value in feature.items():
                if flag == 'get':
                    word_prob_model.get_feature(feature_key, value, feature_map)
                elif flag == 'set':
                    feature_idx = word_prob_model.set_feature(feature_key)
                    feature_map[feature_idx] = value
                else:
                    raise Exception('flag = [set | get]')
            #yield feature_map, num_alignment
            feature_maps.append(feature_map)
        return feature_maps, num_alignments

    def get_feature_map(self, equ_templates, word_prob_model):
        for equ_template in equ_templates:
            feature_maps, num_alignments = self.feature_map_for_one_template(equ_template, word_prob_model, 'get')
            for feature_map, num_alignment in zip(feature_maps, num_alignments):
                yield feature_map, num_alignment, equ_template

    def save_feature_map_for_one_template(self, fp, equ_template, word_prob_model, check_solution, flag):
        find_correct_alignment = False
        feature_maps, num_alignments = self.feature_map_for_one_template(equ_template, word_prob_model, flag)
        n = 0
        for feature_map, num_alignment in zip(feature_maps, num_alignments):
            equation = self.construct_equation(num_alignment, equ_template)
            n += 1
            # print '\t', n, '['+equ_template+']-->['+equation+']'
            print >>fp, '['+equ_template+']-->['+equation+']'
            print >>fp, len(feature_map)
            is_correct_alignment = False
            if check_solution and self.is_correct_alignment(num_alignment, equ_template):
                is_correct_alignment = True
                find_correct_alignment = True
                print '\t['+equ_template+']-->['+equation+']'
                print >>fp, 1,
            if not is_correct_alignment:
                print >>fp, -1,
            for feature_idx, value in feature_map.items():
                print >>fp, feature_idx, ":", value,
            print >>fp, '\n',

        if check_solution and not find_correct_alignment and not self.semi_supervised:
            raise Exception

        return n

    def save_feature_map_supervised(self, file_name, equ_templates, word_prob_model, flag):
        fp = open(file_name, 'w')
        print >>fp, "["+self.sol_info.equ_template+"]-->["+self.sol_info.equation+"]"
        print self.sol_info.equ_template
        n = self.save_feature_map_for_one_template(fp, self.sol_info.equ_template, word_prob_model, True, flag)

        other_templates = equ_templates[:]
        other_templates.remove(self.sol_info.equ_template)

        for equ_template in other_templates:
            print equ_template
            n += self.save_feature_map_for_one_template(fp, equ_template, word_prob_model, False, flag)
        fp.close()
        return n

    def save_feature_map_semi_supervised(self, file_name, equ_templates, word_prob_model, flag):
        fp = open(file_name, 'w')
        print >>fp, "["+self.sol_info.equ_template+"]-->["+self.sol_info.equation+"]"
        n = 0
        for equ_template in equ_templates:
            print equ_template
            n += self.save_feature_map_for_one_template(fp, equ_template, word_prob_model, True, flag)
        fp.close()
        return n

    def construct_word_prob_model_and_save_training_feature(self, file_name, equ_templates, word_prob_model, semi_supervised):
        n = 0
        if semi_supervised:
            self.semi_supervised = True
            n = self.save_feature_map_semi_supervised(file_name, equ_templates, word_prob_model, 'set')
        else:
            self.semi_supervised = False
            n = self.save_feature_map_supervised(file_name, equ_templates, word_prob_model, 'set')
        return n


class WordProbSolutionInfo:
    def __init__(self, equ_template, equation, ans):
        self.equ_template = self.formulate_equ_template(equ_template)
        self.equation = self.formulate_equ_template(equation)
        try:
            self.ans = eval(ans)
        except TypeError:
            self.ans = ans
        self.sub_equs = self.get_sub_equation(equ_template)
        print self.equ_template, self.ans

    @staticmethod
    def formulate_equ_template(equ_template):
        equ_template = equ_template.strip()
        equ_template = equ_template.strip(' ,')
        return equ_template

    @staticmethod
    def get_sub_equation(equ_template):
        equ_template = WordProbSolutionInfo.formulate_equ_template(equ_template)
        sub_equs = []
        for sub_equ in equ_template.split(','):
            if sub_equ:
                sub_equs.append(sub_equ.strip())
        return sub_equs

def read_word_prob_info(parse_rlt_dir, solution_file):
    fp = open(solution_file, 'r')
    sol_infos = {}
    word_probs = {}
    indexes = []
    equ_templates = {}

    while True:
        index = fp.readline().strip()
        equ_template = WordProbSolutionInfo.formulate_equ_template(fp.readline().strip())
        equation = WordProbSolutionInfo.formulate_equ_template(fp.readline().strip())
        ans = fp.readline().strip()
        if not ans:
            break
        print index

        sol_infos[index] = WordProbSolutionInfo(equ_template, equation, ans)
        word_probs[index] = WordProb(parse_rlt_dir, str(index))
        indexes.append(index)
        equ_templates.setdefault(equ_template, [])
        equ_templates[equ_template].append(index)

    fp.close()

    # if word_problem_file and json_word_prob_file:
    #     fp = open(word_problem_file+".txt", 'w')
    #     fp_json = open(json_word_prob_file, 'r')
    #     json_word_probs = json.load(fp_json)
    #     word_prob_texts = {}
    #     for word_prob in json_word_probs:
    #         word_prob_texts[str(word_prob['iIndex'])] = word_prob['sQuestion'].strip()
    #
    #     word_prob_infos = {}
    #     for template, word_prob_indexes in equ_templates.items():
    #         if template not in word_prob_infos:
    #             word_prob_infos[template] = []
    #         print >>fp, template, len(word_prob_indexes)
    #         for idx in word_prob_indexes:
    #             word_prob_info = dict()
    #             word_prob_info['index'] = idx
    #             word_prob_info['question'] = word_prob_texts[idx]
    #             word_prob_info['equation'] = sol_infos[idx].equation
    #             word_prob_info['ans'] = sol_infos[idx].ans
    #             word_prob_infos[template].append(word_prob_info)
    #             print >>fp, '  [%s]  %s' % (idx, word_prob_texts[idx])
    #     fp.close()
    #     fp = open(word_problem_file+".json", 'w')
    #     json.dump(word_prob_infos, fp, indent=2, sort_keys=True)
    #     fp.close()
    #     fp_json.close()
    return word_probs, sol_infos, indexes, equ_templates

def is_correct_template(prob, nums, template):
    n = WordProbFeature.get_var_num(template, 'a')

    correct_ans = prob['ans']
    permutations = WordProbFeature.permutate(nums, n)

    for permutation in permutations:
        calculated_ans = EquationSolution.calc_word_prob[template](*permutation)
        for ans in correct_ans:
            if not WordProbFeature.is_correct_numerically(ans, calculated_ans):
                break
        else:
            return True

    return False

def is_equvalent_template(probs, equ_num, template1, template2):
    num_pattern = r'[0-9]+\.?[0-9]*'
    # Template has special numbers. They will be different.
    if re.search(num_pattern, template1.replace('= 0', '')) or re.search(num_pattern, template2.replace('= 0', '')):
        return False

    for prob in probs:
        if not is_correct_template(prob, equ_num[prob['index']], template2):
            return False
    return True


# raw_word_prob_file is input file
# word_prob_info_file is output file
def normalize_equation_template(raw_word_prob_file, word_prob_info_file):
    fp = open(raw_word_prob_file)
    word_prob_data = json.load(fp)
    word_prob_raw_groups = {}
    word_prob_groups = {}
    word_prob_equ_number = {}
    # number_pattern = re.compile('-?[0-9]+(?:\.?[0-9]*)')
    number_pattern = r'(-?[0-9]+\.?[0-9]*)'
    for word_prob in word_prob_data:
        equ = word_prob['equation']
        ans = WordProbFeature.get_solution(equ)
        word_prob['ans'] = ans

        template = word_prob['template']
        n = WordProbFeature.get_var_num(template, 'a')
        template_pattern = re.escape(template)
        for idx in range(n):
            template_pattern = template_pattern.replace(chr(ord('a')+idx), number_pattern)

        # equ = equ.replace('= 0', '')
        # word_prob['number'] = list(re.findall(template_pattern, equ)[0])
        prob_index = word_prob['index']
        word_prob_equ_number[prob_index] = list(re.findall(template_pattern, equ)[0])
        for idx, num in enumerate(word_prob_equ_number[prob_index]):
            word_prob_equ_number[prob_index][idx] = float(word_prob_equ_number[prob_index][idx])
        # print word_prob_equ_number[word_prob['index']]
        # if not is_correct_template(word_prob, word_prob_equ_number[prob_index], template):
        #     raise Exception("Bad number extraction")

        del word_prob['template']
        word_prob_raw_groups.setdefault(template, [])
        word_prob_raw_groups[template].append(word_prob)

    templates = word_prob_raw_groups.keys()

    for index, template1 in enumerate(templates):
        probs = word_prob_raw_groups[template1]
        equvalent_template = None
        for template2 in templates[index+1:]:
            if is_equvalent_template(probs, word_prob_equ_number, template1, template2):
                word_prob_raw_groups[template2].extend(word_prob_raw_groups[template1])
                equvalent_template = template2
                break

        if not equvalent_template:
            word_prob_groups[template1] = word_prob_raw_groups[template1]
        else:
            print template1, template2

    fp = open(word_prob_info_file, 'w')
    json.dump(word_prob_groups, fp, indent = 2)
    fp.close()

def read_json_word_prob_info(parse_rlt_dir, word_prob_info_json_file):
    fp = open(word_prob_info_json_file)
    word_porb_infos = json.load(fp)
    equ_templates = word_porb_infos.keys()

    sol_infos = {}
    word_probs = {}
    indexes = []
    for equ_template, word_prob_subset in word_porb_infos.items():
        for word_prob in word_prob_subset:
            index = word_prob["index"]
            ans =word_prob["ans"]
            equation = word_prob["equation"]
            sol_infos[index] = WordProbSolutionInfo(equ_template, equation, ans)
            word_probs[index] = WordProb(parse_rlt_dir, str(index))
            indexes.append(index)
    fp.close()
    return word_probs, sol_infos, indexes, equ_templates

def get_train_and_test_samples_separately(parse_rlt_dir, word_problem_info_file, test_case_file, train_dir, test_dir, semi_supervised):

    word_probs, sol_infos, train_idxes, equ_templates = read_json_word_prob_info(parse_rlt_dir, word_problem_info_file)
    equ_templates = equ_templates
    test_idxes = []
    for idx in open(test_case_file, 'r'):
        idx = idx.strip()
        test_idxes.append(idx)
        train_idxes.remove(idx)

    ngram_model = NGram(word_probs.values())
    word_prob_model = WordProbModel()

    fp = open(train_dir+'file_names.txt', 'w')
    # train_idxes = ['6952', '5701', '5933', '5272', '2075' ]
    # train_idxes = ['1194']
    for idx in train_idxes:
        print 'train: <', train_idxes.index(idx), '-->', idx, '>'
        word_prob_ftr = WordProbFeature(sol_infos[idx], word_probs[idx], ngram_model)
        word_prob_ftr.construct_word_prob_model_and_save_training_feature(train_dir+idx+".txt", equ_templates, word_prob_model, semi_supervised)
        fp.write(idx+".txt"+"\n")
    fp.close()

    fp = open(test_dir+'file_names.txt', 'w')
    for idx in test_idxes:
        print 'test: <', test_idxes.index(idx), '-->', idx, '>'
        word_prob_ftr = WordProbFeature(sol_infos[idx], word_probs[idx], ngram_model)
        word_prob_ftr.save_feature_map_supervised(test_dir+idx+".txt", equ_templates, word_prob_model, 'get')
        fp.write(idx+".txt"+"\n")
    fp.close()

    return ngram_model, word_prob_model

def validate_num_alignment(parse_rlt_dir, solution_file):
    word_probs, sol_infos, idxes, equ_templates = read_json_word_prob_info(parse_rlt_dir, solution_file)
    ngram_model = NGram(word_probs.values())
    # idxes = ['1658']
    for idx in idxes:
        print idxes.index(idx), '-->', idx
        word_prob_ftr = WordProbFeature(sol_infos[idx], word_probs[idx], ngram_model)
        word_prob_ftr.validate_num_alignment()

def save_training_sample_list(idxes, output_dir):
    train_index_file_template = output_dir+"train_index/train_%d.txt"
    test_index_file_template = 'D:/WordProblem_code/WordProblem_code/python/GetWordProblemFeature_v1/data/indexes-1-fold-%d.txt'

    for n in range(5):
        train_idx_file = train_index_file_template % n
        test_idx_file = test_index_file_template % n

        train_idxes = idxes[:]
        for test_idx in open(test_idx_file, 'r'):
            train_idxes.remove(test_idx.strip())
        fp = open(train_idx_file, 'w')
        for train_idx in train_idxes:
            print >> fp, train_idx+".txt"
        fp.close()


def get_train_and_test_samples_totally(parse_rlt_dir, word_prob_info_file, output_dir, semi_supervised):
    word_probs, sol_infos, idxes, equ_templates = read_json_word_prob_info(parse_rlt_dir, word_prob_info_file)
    save_training_sample_list(idxes, output_dir)

    ngram_model = NGram(word_probs.values())
    word_prob_model = WordProbModel()

    fp = open(output_dir+'file_names.txt', 'w')
    # train_idxes = ['6952', '5701', '5933', '5272', '2075' ]
    # train_idxes = ['1194']
    total_n = 0.0
    for idx in idxes:
        print 'problem: <', idxes.index(idx), '-->', idx, '>'
        word_prob_ftr = WordProbFeature(sol_infos[idx], word_probs[idx], ngram_model)
        n = word_prob_ftr.construct_word_prob_model_and_save_training_feature(output_dir+idx+".txt", equ_templates, word_prob_model, semi_supervised)
        total_n += n
        fp.write(idx+".txt"+"\n")
        fp.write(str(n)+"\n")
    fp.close()

    fp = open(output_dir+'average_derivation.txt', 'w')
    fp.write(str(total_n/len(idxes))+"\n")
    fp.close()
    return ngram_model, word_prob_model


if __name__ == '__main__':

    t = time()
    raw_word_prob_file = "data/word_prob.json"
    word_prob_info_file = 'model/word_prob_info.json'
    normalize_equation_template(raw_word_prob_file, word_prob_info_file)

    test_case_file_template = 'data/indexes-1-fold-%d.txt'
    parse_rlt_dir = 'parses/'

    # Get all the training and test samples
    semi_supervised = False
    output_dir = "result/word_prob_ftr/"
    word_prob_model_dir = "model/model/"
    # output_dir = "./result/word_prob_ftr_n_a/"
    # word_prob_model_dir = "./model/model_n_a/"
    if semi_supervised:
        output_dir = "result/word_prob_ftr_semi/"
        word_prob_model_dir = "model/model_semi/"
    ngram_file = word_prob_model_dir+"ngram.txt"
    ngram_model, word_prob_model = get_train_and_test_samples_totally(parse_rlt_dir, word_prob_info_file, output_dir, semi_supervised)
    ngram_model.save(ngram_file)
    word_prob_model.save(word_prob_model_dir)
    print time() - t













