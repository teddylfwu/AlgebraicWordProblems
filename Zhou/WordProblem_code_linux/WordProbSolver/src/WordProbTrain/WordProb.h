#pragma  once

#include <iostream>
#include <fstream>
#include <string>
#include <cstring>
#include <sstream>
#include <iomanip>
#include <vector>
#include "linear.h"
#include <algorithm>
#include <map>
#include <iterator>
#include <iomanip>
#include <ctime>
#include <limits.h>
using namespace std;

#define NEGATIVE -1
#define POSITIVE 1
#define MAX_SAMPLES 300
//#define MAX_BAD_SMAPLES_EACH_ITER 100
#define MIN_THRESHOLD 2

#define Malloc(type,n) (type *)malloc((n)*sizeof(type))

#define INF HUGE_VAL

inline bool operator< (const struct feature_node & ft_node1, const struct feature_node &ft_node2)
{
	return ft_node1.index < ft_node2.index;
}
class CWordProbTrain
{
public:
	CWordProbTrain(const string &input_dir, const string &file_list, const string &output_dir, double min_C = 0.01, double max_C = 100, double step = 1.2) :m_input_dir(input_dir), m_file_names(file_list), m_output_dir(output_dir)
	{ 
		m_prob.bias = -1;
		m_prob.l = m_prob.n = 0;
		m_prob.x = NULL;
		m_prob.y = NULL;
		m_model = NULL;
		init_svm_param(min_C, max_C, step); 
		m_max_cv_accuracy = 0;
		
	}

    ~CWordProbTrain() {
        if (m_prob.x) {
            delete m_prob.x;
            m_prob.x = NULL;
        }

        if (m_prob.y) {
            delete m_prob.y;
            m_prob.y = NULL;
        }

        if (m_model) {
            if (m_model->w) {
                delete m_model->w;
                m_model->w = NULL;
            }

            if (m_model->label) {
                delete m_model->label;
                m_model->label = NULL;
            }

            delete m_model;
            m_model = NULL;
        }
    }

	void train(double bias = -1);	
	bool save_word_prob_model(const string &in_idx2ftr_file, const string &out_word_prob_model_file);
	string get_sample_info();
	
private:
	string m_input_dir;
	string m_output_dir;
	string m_file_names;

	int m_max_index;

	map<string,vector<int> > m_labels;
	map<string,string> m_corr_templates;
	map<string,vector<string> > m_sample_templates;
	map<string, vector<vector<struct feature_node> > > m_sample_pool;
	map<string, vector<vector<struct feature_node> > > m_pos;
	map<string, vector<vector<struct feature_node> > > m_neg;
	map<string, vector<vector<struct feature_node> > > m_training_pool;
	map < string, vector < bool>  > m_training_pool_bitmap;

	vector<string> m_file_list;
	vector<string> m_rand_file_list;

	vector<vector<struct feature_node> > m_training_samples;
	struct problem m_prob;
	vector<struct parameter> m_svm_params;
	model *m_model;

	double m_max_cv_accuracy;

private:
	vector<vector<struct feature_node> >& read_sample_features(int max_idx = INT_MAX);
	int read_samples_one_prob(const string &file, int max_idx = -1);
	void error_info(string file, int line_no);
	string get_line(istream &ifs, int &line_no);
	
	size_t read_samples_one_prob(const string &file, int max_idx,
		vector<vector<feature_node> > &samples,
		vector<int> &labels,
		vector<string> &sample_templates,
		string &corr_template,
		double bias);
	void complete_sample_vector(vector<feature_node> & sample,  int max_idx, double bias);
	int construct_training_pool(const string &file, vector<vector<feature_node> > &pos, vector<int> &neg_idx);
	//void construct_training_pool(const string &file, vector<vector<feature_node> > &pos, vector<vector<feature_node> > &neg);
	void construct_training_sample(vector<vector<feature_node> > &pos, vector<vector<feature_node> > &neg);
	void init_svm_param(double min_C=0.01, double max_C=100, double step=1.2);
	void init_problem(double bias);
	void init_problem(const vector<string> &file_list);
	int seek_bad_cases(int &bad_case_no);
	void cross_validation();
	double cross_validation(int nfold);
	double do_cross_validation(int nfold, struct parameter &param);
	double predict();
	bool predict(const string &file, vector<int> &bad_case_idxes, int &max_pos_idx);
	//bool predict(const string &file, vector<vector<feature_node> > &bad_cases, int &max_pos_idx);
	double predict(vector<string> &file_list);
	void copy_model(struct model* src, struct model*& dst);	
	void correct_samples(map<string, vector<vector<struct feature_node> > > &data);
	pair<int, int> get_neg_cnt();
	
};
