#include <iostream>
#include <fstream>
#include <string>
#include <cstring>
#include <sstream>
#include <iomanip>
#include <vector>
#include "linear.h"
#include <algorithm>
#include <cstdlib>
#include <map>
#include <float.h>

#define NEGATIVE -1
#define POSITIVE  1

using namespace std;

inline bool operator< (const struct feature_node & ft_node1, const struct feature_node &ft_node2)
{
	return ft_node1.index < ft_node2.index;
}

void error_info(string file, int line_no)
{
	cerr << "Format error in <" << file << " | " << line_no << ">" << endl;
}

string get_line(ifstream &ifs, int &line_no)
{
	string line;
	while (getline(ifs, line))
	{
		line_no++;
		if (line.size())
			break;
	}
	return line;
}

size_t read_samples_one_prob(const string &file, int max_idx, 
						  vector<vector<feature_node> > &samples, 
						  vector<int> &labels,
						  vector<string> &sample_templates,
						  string &corr_template,
						  double bias)
{
	ifstream ifs(file.c_str());
	if (!ifs)
	{
		cerr << "Can't open file :<" << file << ">!" << endl;
		return 0;
	}

	string line;
	int line_no = 0;
	line = get_line(ifs, line_no);

	if (ifs)
		corr_template=line;
	else
	{
		error_info(file, line_no);
		return 0;
	}


	int label = 0, index = 0;
	double value = 0;
	char c;
	struct feature_node ft_node;
	int ft_len = 0;
	vector<vector<struct feature_node> > pos, neg;
	istringstream iss(line);
	while (getline(ifs, line))
	{
		line_no++;
		if (line.size() == 0)
			continue;
		sample_templates.push_back(line);

		iss.clear();
		iss.str(get_line(ifs, line_no));
		iss.seekg(ios_base::beg);
		iss >> ft_len;
		if (!ifs || !iss)
		{
			error_info(file, line_no);
			break;
		}

		iss.clear();
		iss.str(get_line(ifs, line_no));
		iss.seekg(ios_base::beg);
		iss >> label;
		if (!(ifs && iss && (label == NEGATIVE || label == POSITIVE)))
		{
			error_info(file, line_no);
			break;
		}
		labels.push_back(label);

		vector<struct feature_node> sample;
		int i = 0;
		while (iss >> index >> c >> value)
		{
			ft_node.index = index + 1;//start from one
			ft_node.value = value;

			if (index <= max_idx)
				sample.push_back(ft_node);
			i++;
		}
		if (i != ft_len)
		{
			error_info(file, line_no);
			break;
		}

		sort(sample.begin(), sample.end());

		if (bias >= 0)
		{
			ft_node.index = max_idx + 2;
			ft_node.value = bias;
			sample.push_back(ft_node);
		}
		ft_node.index = -1;
		sample.push_back(ft_node);
		samples.push_back(sample);
	}
		
	ifs.close();
	return samples.size();
}

void rewrite_template(string &str)
{
	string temp;
	for (size_t i = 0; i < str.size();i++)
	{
		if (str[i] == '|')
		{
			temp.push_back('\n');
			continue;
		}
			
		if (str[i] == ' ')
			continue;

		temp.push_back(str[i]);
	}

	str = temp;
}



int main(int argc, char** argv)
{
	float total_accuracy = 0.0;
	bool semi_supervised = false;

	for(int test_idx = 0; test_idx <= 4; test_idx++) {
		int model_idx = 5;

		string model_file_template("../WordProbTrain/result/result_%d/word_prob_model_%d.model");
		string output_dir_template("./result/result_%d/");
		// string file_list_template("../../../python/GetWordProblemFeature_v1/result/word_prob_ftr/test_index/indexes-1-fold-%d.txt");
		string file_list_template("test_index/indexes-1-fold-%d.txt");
		
		string file_dir("../../word_prob_ftr/");

		if (semi_supervised)
		{
			model_file_template = "../WordProbTrain/result/result_semi_%d/word_prob_model_%d.model";
			output_dir_template = "./result/result_semi_%d/";
			file_dir = "../../word_prob_ftr_semi/";
            file_list_template = "test_index/indexes-1-fold-%d.txt";
		}

		const int buffer_size = 100;
		char model_file[buffer_size];	
		char output_dir[buffer_size];
		char file_list[buffer_size];

		snprintf(model_file, buffer_size, model_file_template.c_str(), test_idx, model_idx);
		snprintf(output_dir, buffer_size, output_dir_template.c_str(), test_idx);
		snprintf(file_list, buffer_size, file_list_template.c_str(), test_idx);

		ifstream ifs((file_dir + file_list).c_str());

		if (!ifs)
		{
			cout << "Can't open file <" << file_dir + file_list << endl;
			return EXIT_FAILURE;
		}

        model* model_ = NULL;
        while(!model_ && model_idx > 0) {
            model_idx--;
            snprintf(model_file, buffer_size, model_file_template.c_str(), test_idx, model_idx);
            model_ = load_model(model_file);
        }

        if (!model_) {
			cout << "Can't open <" << model_file << ">" << endl;
			return EXIT_FAILURE;
        }

		
		string output_file= string(output_dir) + "false_problem.txt";
		ofstream false_ofs(output_file.c_str());
		if (!false_ofs)
		{
			cout << "Can't open file <" << output_file << ">" << endl;
			return 0;
		}

		
		string file;
		int max_index =  model_->nr_feature - 1;
		double probs_no = 0, corr_no = 0, accuracy = 0;
		int n = 0;
		while (ifs >> file)
		{
			if (file.size() == 0)
				continue;
			
			vector<vector<feature_node> > samples;
			vector<int> labels;
			vector<string> sample_templates;
			string corr_template;
			
			file = file + ".txt";

			read_samples_one_prob(file_dir + file, max_index, samples, labels, sample_templates, corr_template, model_->bias);
			double max_value = -DBL_MAX, value;		
			size_t max_index = 0;
			for (size_t i = 0; i < samples.size(); i++)
			{
				predict_values(model_, &samples[i][0], &value);
				if (value > max_value)
				{
					max_value = value;
					max_index = i;
				}
			}

			n++;
			probs_no++;
			rewrite_template(corr_template);
			rewrite_template(sample_templates[max_index]);
			if (labels[max_index] == POSITIVE)
				corr_no++;
			
				
			accuracy = corr_no / probs_no;
			cout << n << " " << file << "-->" << boolalpha << (labels[max_index] == POSITIVE) << endl;
			cout << sample_templates[max_index] << endl;
			if (labels[max_index] != POSITIVE)
				cout << "Correct: \n"<<corr_template << endl;
			cout << "Accuracy: " << accuracy << " ("<<corr_no<<"|"<<probs_no<< ")" << endl;
		}

		total_accuracy += accuracy;
		false_ofs << "Accuracy: " << accuracy << " (" << corr_no << "|" << probs_no << ")" << endl;
		ifs.close();
		false_ofs.close();
       
        if(model_) {
            if(model_->w) {
                delete model_->w;
                model_->w = NULL;
            }

            if (model_->label) {
                delete model_->label;
                model_->label = NULL;
            }
        
            delete model_;
            model_ = NULL;
        }
	}

	cout << "Final 5-fold cross validation accuracy: " << (total_accuracy / 5) << endl;
}
