
#include "WordProb.h"

void CWordProbTrain::error_info(string file, int line_no)
{
	cerr << "Format error in <" << file << " | " << line_no << ">" << endl;
}

string CWordProbTrain::get_line(istream &ifs, int &line_no)
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

size_t CWordProbTrain::read_samples_one_prob(const string &file, int max_idx,
	vector<vector<feature_node> > &samples,
	vector<int> &labels,
	vector<string> &sample_templates,
	string &corr_template,
	double bias)
{
	ifstream infile((m_input_dir+file).c_str());
	if (!infile)
	{
		cerr << "Can't open file :<" << m_input_dir+file << ">!" << endl;
		return 0;
	}

	string buffer;
	buffer.assign(istreambuf_iterator<char>(infile), istreambuf_iterator<char>());
	istringstream ifs(buffer);

	string line;
	int line_no = 0;
	
	line = get_line(ifs, line_no);

	if (ifs)
		corr_template = line;
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
			ft_node.index = index + 1;//start form one
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
		
		samples.push_back(sample);
	}

	infile.close();
	return samples.size();
}

int CWordProbTrain::read_samples_one_prob(const string &file, int max_idx)
{
	//ifstream infile((m_file_dir+file).c_str());
	ifstream ifs((m_input_dir + file).c_str());
	if (!ifs)
	{
		cerr << "Can't open file :<" << file << ">!" << endl;
		return 0;
	}

	//string buffer;
	//buffer.assign(istreambuf_iterator<char>(infile), istreambuf_iterator<char>());
	//istringstream ifs;
	//ifs.str(buffer);

	string line;
	int line_no = 0;

	//Read correct sample;
	line = get_line(ifs, line_no);
	if (ifs)
		m_corr_templates[file]=line;
	else
	{
		error_info(file, line_no);
		return 0;
	}

	int n = 0;
	int label = 0, index = 0;
	double value = 0;
	char c;
	struct feature_node ft_node;
	int ft_len = 0;
	vector<vector<struct feature_node> > pos;
	vector<int> neg_idx;
	istringstream iss(line);
	while (getline(ifs, line))
	{
		//Read sample template;
		line_no++;
		if (line.size() == 0)
			continue;
		m_sample_templates[file].push_back(line);

		//Read sample feature length;
		iss.clear();
		iss.str(get_line(ifs, line_no));
		iss.seekg(ios_base::beg);
		iss >> ft_len;
		if (!ifs || !iss)
		{
			error_info(file, line_no);
			break;
		}
		
		//Read sample label;
		iss.clear();
		iss.str(get_line(ifs, line_no));
		iss.seekg(ios_base::beg);
		iss >> label;
		if (!(ifs && iss && (label == NEGATIVE || label == POSITIVE)))
		{
			error_info(file, line_no);
			break;
		}		
		m_labels[file].push_back(label);

		//Read samples' features;
		vector<struct feature_node> sample;
		int i = 0;
		while (iss >> index >> c >> value)
		{
			ft_node.index = index+1;//start from one
			ft_node.value = value;
			
			if (index > m_max_index)
				m_max_index = index;
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

		complete_sample_vector(sample, m_max_index, m_prob.bias);

		m_sample_pool[file].push_back(sample);
		
				
		if (label == POSITIVE)
		{
			pos.push_back(sample);
			m_training_pool_bitmap[file].push_back(true);
		}
		else
		{
			neg_idx.push_back(n);
			m_training_pool_bitmap[file].push_back(false);
		}
			
		n++;
		/*if (n >= 50)
			break;*/
	}

	m_pos[file] = pos;
	//construct_training_sample(pos, neg);
	construct_training_pool(file,pos, neg_idx);
	
	ifs.close();
	return n;
}

string CWordProbTrain::get_sample_info()
{
	pair<int, int> neg_info = get_neg_cnt();
	ostringstream oss;
	oss << "training_neg_samples: " << neg_info.first<<"\n";
	oss << "total_neg_samples: " << neg_info.second<<"\n";
	return oss.str();
}

pair<int, int> CWordProbTrain::get_neg_cnt()
{
	map<string, vector<bool> >::iterator iter;
	int training_neg_cnt = 0;
	int total_neg_cnt = 0;
	for (iter = m_training_pool_bitmap.begin(); iter != m_training_pool_bitmap.end(); iter++)
	{
		vector<int> &labels = m_labels[iter->first];
		vector<bool> &samples = iter->second;
		for (size_t i = 0; i < labels.size(); i++)
		{
			if (labels[i] == NEGATIVE)
			{
				total_neg_cnt++;
				if (labels[i] == NEGATIVE && samples[i])
					training_neg_cnt++;
			}			
		}
	}
	return make_pair(training_neg_cnt, total_neg_cnt);

}

int CWordProbTrain::construct_training_pool(const string &file, vector<vector<feature_node> > &pos, vector<int> &neg_idxes)
{

	if (neg_idxes.size() > MAX_SAMPLES)
		random_shuffle(neg_idxes.begin(), neg_idxes.end());
	size_t neg_size = min(MAX_SAMPLES, (int)neg_idxes.size());
	feature_node ft_node;
	int offset = m_prob.bias >= 0 ? 2 : 1;
	vector<vector<struct feature_node> > neg;
	int neg_idx;
	for (size_t i = 0; i < neg_size; i++)
	{
		neg_idx = neg_idxes[i];
		if (!m_training_pool_bitmap[file][neg_idx])
		{ 
			neg.push_back(m_sample_pool[file][neg_idx]);
			m_training_pool_bitmap[file][neg_idx] = true;
		}
			
	}

	if (neg.empty())
		return 0;

	for (size_t i = 0; i < pos.size(); i++)
	{
		for (size_t j = 0; j < neg.size(); j++)
		{
			vector<feature_node> training_sample(pos[i]);
			training_sample.pop_back();
			for (int m = 0; m < (int)neg[j].size() - offset; m++)
			{
				vector<feature_node>::iterator iter = lower_bound(training_sample.begin(), training_sample.end(), neg[j][m]);

				ft_node.index = neg[j][m].index;
				ft_node.value = -neg[j][m].value;

				if (iter == training_sample.end() || iter->index != neg[j][m].index)
					training_sample.insert(iter, ft_node);
				else
					iter->value += ft_node.value;//ft_node.value is already negative

			}
			complete_sample_vector(training_sample, m_max_index, m_prob.bias);
			m_training_pool[file].push_back(training_sample);
		}
	}

	return neg.size();

}

//void CWordProbTrain::construct_training_pool(const string &file, vector<vector<feature_node> > &pos, vector<vector<feature_node> > &neg)
//{
//	
//	if (neg.size() > MAX_SAMPLES)
//		random_shuffle(neg.begin(), neg.end());
//	int neg_size = min(MAX_SAMPLES, (int)neg.size());
//	feature_node ft_node;
//	int offset = m_prob.bias >= 0 ? 2 : 1;
//	for (size_t i = 0; i < pos.size(); i++)
//	{
//		for (int j = 0; j < neg_size; j++)
//		{
//			vector<feature_node> training_sample(pos[i]);
//			training_sample.pop_back();
//			for (int m = 0; m < (int)neg[j].size() - offset; m++)
//			{
//				vector<feature_node>::iterator iter = lower_bound(training_sample.begin(), training_sample.end(), neg[j][m]);
//
//				ft_node.index = neg[j][m].index;
//				ft_node.value = -neg[j][m].value;
//
//				if (iter == training_sample.end() || iter->index != neg[j][m].index)
//					training_sample.insert(iter, ft_node);
//				else
//					iter->value += ft_node.value;//ft_node.value is already negative
//
//			}
//			complete_sample_vector(training_sample, m_max_index, m_prob.bias);
//			m_training_pool[file].push_back(training_sample);
//		}
//	}
//
//}

void CWordProbTrain::construct_training_sample(vector<vector<feature_node> > &pos, vector<vector<feature_node> > &neg)
{
	if (neg.size() > MAX_SAMPLES)
		random_shuffle(neg.begin(), neg.end());
	int neg_size = min(MAX_SAMPLES, (int)neg.size());
	feature_node ft_node;
	int offset = m_prob.bias >= 0 ? 2 : 1;
	for (size_t i = 0; i < pos.size(); i++)
	{
		for (int j = 0; j < neg_size; j++)
		{
			vector<feature_node> training_sample(pos[i].begin(),pos[i].end()-offset);
			for (int m = 0; m < (int)neg[j].size()-offset; m++)
			{
				vector<feature_node>::iterator iter = lower_bound(training_sample.begin(), training_sample.end(), neg[j][m]);
				
				ft_node.index = neg[j][m].index;
				ft_node.value = -neg[j][m].value;

				if (iter == training_sample.end() || iter->index != neg[j][m].index)
					training_sample.insert(iter, ft_node);
				else
					iter->value += ft_node.value;//ft_node.value is already negative
				
			}
			complete_sample_vector(training_sample,m_max_index,m_prob.bias);
			m_training_samples.push_back(training_sample);
		}
	}

}

void CWordProbTrain::correct_samples(map<string, vector<vector<struct feature_node> > > &data)
{
	map<string, vector<vector<struct feature_node> > >::iterator iter;
	for (iter = data.begin(); iter != data.end(); iter++)
	{
		vector<vector< struct feature_node> > &samples = iter->second;
		for (size_t i = 0; i < samples.size(); i++)
		{
			vector<struct feature_node> &sample = samples[i];
			sample[sample.size() - 2].index = m_max_index + 1;
		}
	}

}

vector<vector<feature_node> >& CWordProbTrain::read_sample_features(int max_idx)
{
	ifstream file_list_ifs((m_input_dir + m_file_names).c_str());
	string file_name;
	int i = 0;
	while (file_list_ifs >> file_name)
	{
		cout <<"<"<<i++<<">: "<< "Deal with <" << file_name << ">!" << endl;
		int n = read_samples_one_prob(file_name, max_idx);
		cout << "Read " << n << " samples!" << endl;
		m_file_list.push_back(file_name);
	}
	if (m_prob.bias >= 0)
	{
		correct_samples(m_pos);
		correct_samples(m_sample_pool);
		correct_samples(m_training_pool);
	}
	
	file_list_ifs.close();

	m_rand_file_list = m_file_list;
	random_shuffle(m_rand_file_list.begin(), m_rand_file_list.end());

	return m_training_samples;
}

void CWordProbTrain::init_problem(const vector<string> &file_list)
{
	size_t cnt = 0;
	for (size_t i = 0; i < file_list.size(); i++)
	{
		string file_name = file_list[i];
		cnt += m_training_pool[file_name].size();
	}

	m_prob.l = cnt;

	if (m_prob.bias >= 0)
		m_prob.n = m_max_index + 2;
	else
		m_prob.n = m_max_index + 1;

	cout << "Total samples <" << m_prob.l << ">!" << endl;
	cout << "Total features <" << m_prob.n << ">!" << endl;

	if (m_prob.x)
		delete[] m_prob.x;
	m_prob.x = new struct feature_node *[m_prob.l];

	if (m_prob.y)
		delete[] m_prob.y;
	m_prob.y = new double[m_prob.l]();

	size_t n = 0;
	for (size_t i = 0; i < file_list.size(); i++)
	{
		string file_name = file_list[i];
		vector<vector<struct feature_node> > &samples = m_training_pool[file_name];
		for (size_t j = 0; j < samples.size(); j++,n++)
		{
			m_prob.x[n] = &samples[j][0];
			m_prob.y[n] = 1;
		}
	}
	
}

void CWordProbTrain::init_problem(double bias)
{

	m_prob.l = m_training_samples.size();
	m_prob.bias = bias;
	if (m_prob.bias >= 0)
		m_prob.n = m_max_index+2;
	else
		m_prob.n = m_max_index+1;

	cout << "Total samples <" << m_prob.l << ">!" << endl;
	cout << "Total features <" << m_prob.n << ">!" << endl;

	if (m_prob.x)
		delete [] m_prob.x;
	m_prob.x = new struct feature_node *[m_prob.l];

	if (m_prob.y)
		delete[] m_prob.y;
	m_prob.y = new double[m_prob.l]();

	for (int i = 0; i < m_prob.l; i++)
	{
		m_prob.x[i] = &m_training_samples[i][0];
		m_prob.y[i] = 1;
	}
}
int CWordProbTrain::seek_bad_cases(int &bad_case_no)
{
	int i = 0, n = m_file_list.size(); //m_sample_pool.size();
	int corr_no = 0;
	int max_pos_index;
	string file_name;
	bad_case_no = 0;

	/*if (m_file_list.size() != m_sample_pool.size())
	{
		cout << "Size not equal" << endl;
		exit(-1);
	}*/

	
	for (size_t i = 0; i < m_file_list.size(); i++)
	{
		//cout << "<" << ++i << ">: " << "Deal with <" << file_name << ">!" << endl;
		vector<int > bad_cases_idxes;
		file_name = m_file_list[i];
		if (predict(file_name, bad_cases_idxes, max_pos_index))
			corr_no++;
		else
		{
			bad_case_no += construct_training_pool(file_name, m_pos[file_name], bad_cases_idxes);
			//construct_training_sample(m_pos[file_name], bad_cases);
			//construct_training_sample(vector<vector<feature_node> >(1,m_sample_pool[file_name][max_pos_index]), bad_cases);
		}
		
		//cout << "Accuracy: " << (double)corr_no/i << " (" << corr_no << "|" << i << ")" << endl;
	}
	
	return n - corr_no;
}

double CWordProbTrain::predict()
{
	ifstream file_list_ifs((m_input_dir + m_file_names).c_str());
	if (!file_list_ifs)
	{
		cerr << "Can't open file <" << m_input_dir + m_file_names << ">" << endl;
		return -1;
	}

	int n = m_sample_pool.size();
	int corr_no = 0;
	int max_pos_index;
	string file_name;
	vector<int > bad_case_idxes;
	while (file_list_ifs >> file_name)
	{
		if (predict(file_name, bad_case_idxes, max_pos_index))
			corr_no++;
	}
	double accuracy = (double)corr_no / n;
	cout << "Accuracy: " << accuracy << " (" << corr_no << "|" << n << ")" << endl;
	file_list_ifs.close();
	return accuracy;
}



void CWordProbTrain::complete_sample_vector(vector<feature_node> & sample, int max_idx, double bias)
{
	feature_node ft_node;
	if (bias >= 0)
	{
		ft_node.index = max_idx + 2;
		ft_node.value = bias;
		sample.push_back(ft_node);
	}
	ft_node.index = -1;
	sample.push_back(ft_node);

}

bool CWordProbTrain::predict(const string &file, vector<int> &bad_case_idxes, int &max_pos_idx)
{
	vector<vector<feature_node> > &samples = m_sample_pool[file];
	vector<int> &labels = m_labels[file];
	vector<string> &sample_templates = m_sample_templates[file];
	string corr_template = m_corr_templates[file];
	
	double max_value = 0, value;
	size_t max_index = 0;
	vector<double> values(samples.size());
	double max_pos_value = 0;
	bool bFirst = true;

	for (size_t i = 0; i < samples.size(); i++)
	{
		vector<feature_node> &sample = samples[i];
		//complete_sample_vector(sample, m_max_index, m_prob.bias);
		predict_values(m_model, &sample[0], &value);
		if (i == 0 || value > max_value)
		{
			max_value = value;
			max_index = i;
		}
		values[i] = value;

		if (labels[i] == POSITIVE)
		{
			if (bFirst || max_pos_value < value)
			{
				bFirst = false;
				max_pos_idx = i;
				max_pos_value = value;
			}
		}
	}

    //cout << file.c_str() << endl;
    //cout << "Size of label: " << labels.size() << endl;
    //cout << "Size of sample: " << samples.size() << endl;

	if (labels[max_index] != POSITIVE)
	{
		for (size_t i = 0; i < values.size(); i++)
		{
			if (values[i]>max_pos_value)
				bad_case_idxes.push_back(i);
		}
	}

	//cout << file << "-->" << boolalpha << (labels[max_index] == POSITIVE) << endl;
	return labels[max_index] == POSITIVE;

}

//bool CWordProbTrain::predict(const string &file, vector<vector<struct feature_node>> &bad_cases, int &max_pos_idx)
//{
//	vector<vector<feature_node> > &samples = m_sample_pool[file];
//	vector<int> &labels = m_labels[file];
//	vector<string> &sample_templates = m_sample_templates[file];
//	string corr_template = m_corr_templates[file];
//	//int max_idx = m_model->nr_feature - 1;
//	//read_samples_one_prob(file, max_idx, samples, labels, sample_templates, corr_template, m_model->bias);
//
//
//	double max_value = 0, value;
//	size_t max_index = 0;
//	vector<double> values(samples.size());
//	double max_pos_value = 0;
//	bool bFirst = true;
//
//	for (size_t i = 0; i < samples.size(); i++)
//	{
//		vector<feature_node> &sample = samples[i];
//		//complete_sample_vector(sample, m_max_index, m_prob.bias);
//		predict_values(m_model, &sample[0], &value);
//		if (i == 0 || value > max_value)
//		{
//			max_value = value;
//			max_index = i;
//		}
//		values[i] = value;
//
//		if (labels[i] == POSITIVE)
//		{
//			if (bFirst || max_pos_value < value)
//			{
//				bFirst = false;
//				max_pos_idx = i;
//				max_pos_value = value;
//			}
//		}			
//	}
//
//	if (labels[max_index] != POSITIVE)
//	{		
//		for (size_t i = 0; i < values.size();i++)
//		{
//			if (values[i]>max_pos_value)
//				bad_cases.push_back(samples[i]);
//		}
//	}
//
//	//cout << file << "-->" << boolalpha << (labels[max_index] == POSITIVE) << endl;
//	return labels[max_index] == POSITIVE;
//
//}

void CWordProbTrain::init_svm_param(double min_C, double max_C, double step)
{	
	struct parameter param;

	param.solver_type = L2R_L1LOSS_SVC_DUAL;
	//param.solver_type = L2R_L2LOSS_SVC_DUAL;
	//param.solver_type = L1R_L2LOSS_SVC;
	param.C = 1;
	param.eps = 0.001; // see setting below
	param.p = 0.1;
	param.nr_weight = 0;
	param.weight_label = NULL;
	param.weight = NULL;

	double C;

	for (C = min_C; C <= max_C; C *= step)
	{
		param.C = C;
		m_svm_params.push_back(param);
	}

	if (param.C != max_C )
	{
		param.C = max_C;
		m_svm_params.push_back(param);
	}
}

void CWordProbTrain::copy_model(struct model* src, struct model*& dst)
{
	if (!src)
		return;

	if (dst)
		free_and_destroy_model(&dst);

	dst = Malloc(model, 1);	
	*dst = *src;

	int nr_class = src->nr_class;
	int w_size = src->nr_feature;
	if (src->bias >= 0)
		w_size = w_size + 1;

	int nr_w;
	if (src->nr_class == 2 && src->param.solver_type != MCSVM_CS)
		nr_w = 1;
	else
		nr_w = src->nr_class;
	
	dst->w = Malloc(double, w_size*nr_w);
	for (int i = 0; i < w_size*nr_w; i++)
		dst->w[i] = src->w[i];
	//copy(src->w, src->w + w_size*nr_class, dst->w);

	
	dst->label = Malloc(int, nr_class);
	for (int i = 0; i < nr_class; i++)
		dst->label[i] = src->label[i];
	//copy(src->label, src->label + nr_class, dst->label);
}

double CWordProbTrain::predict(vector<string> &test_file_list)
{

	int corr = 0;
	vector<int > bad_cases_idxes;
	int max_pos_index;
	for (size_t i = 0; i < test_file_list.size(); i++)
	{
		
		if (predict(test_file_list[i], bad_cases_idxes, max_pos_index))
			corr++;
		/*string file_name = test_file_list[j];
		vector<vector<struct feature_node> > &samples = m_training_pool[file_name];
		bool bCorr = true;
		for (size_t k = 0; k < samples.size(); k++)
		{
			predict_values(m_model, &samples[k][0], &value);
			if (value < 0)
			{
				bCorr = false;
				break;
			}
		}
		if (bCorr)
			corr += 1;*/
	}

	double accuracy = (double)corr / test_file_list.size();
	return accuracy;
}

double CWordProbTrain::cross_validation(int nfold)
{
	double max_accuracy = 0;
	struct model* best_model = NULL;
	for (size_t i = 0; i < m_svm_params.size(); i++)
	{
		if (m_model)
		{
			free_and_destroy_model(&m_model);
			m_model = NULL;
		}			
		
		double accuracy = do_cross_validation(nfold,m_svm_params[i]);
		if (max_accuracy < accuracy)
		{
			max_accuracy = accuracy;
			copy_model(m_model, best_model);
		}
	}
	copy_model(best_model, m_model);
	free_and_destroy_model(&best_model);
	return max_accuracy;
}

double CWordProbTrain::do_cross_validation(int nfold, struct parameter &param)
{
	if (nfold == 1)
	{
		init_problem(m_file_list);
		m_model = ::train(&m_prob, &param);
		return predict(m_file_list);
	}

	double max_accuracy = 0;
	vector<string> file_list(m_rand_file_list);
	//random_shuffle(file_list.begin(), file_list.end());
	size_t cnt = file_list.size() / nfold;
	double accuracy = 0;

	for (int i = 0; i < nfold; i++)
	{
		vector<string> train_file_list(file_list);
		vector<string>::iterator beg = train_file_list.begin() + i*cnt;
		vector<string>::iterator end = i + 1 == nfold ? train_file_list.end() : train_file_list.begin() + (i + 1)*cnt;
		vector<string> test_file_list(beg, end);
		train_file_list.erase(beg, end);						

		init_problem(train_file_list);
		m_model = ::train(&m_prob, &param);	
		accuracy += predict(test_file_list);	
		free_and_destroy_model(&m_model);
	}
	
	init_problem(m_file_list);
	m_model = ::train(&m_prob, &param);

	return accuracy / nfold;
}

//void CWordProbTrain::cross_validation()
//{
//	double max_accuracy = 0;
//	struct model* best_model = NULL;
//	for (size_t i = 0; i<m_svm_params.size();i++)
//	{
//		if (m_model)
//			free_and_destroy_model(&m_model);			
//		m_model = ::train(&m_prob, &m_svm_params[i]);
//		cout << "C=" << m_svm_params[i].C << " "<<flush;
//		double accuracy = predict();
//
//		if (max_accuracy < accuracy)
//		{
//			max_accuracy = accuracy;
//			copy_model(m_model, best_model);
//		}		
//	}
//	copy_model(best_model, m_model);
//	free_and_destroy_model(&best_model);
//	cout << "/***********************************************/"<<endl 
//		 <<"Best C : " << m_model->param.C << " Best Accuracy : " << max_accuracy<< endl
//		 << "/***********************************************/"<< endl;
//	return;
//}

void CWordProbTrain::train(double bias)
{
	read_sample_features(INT_MAX);
	
	int n = 0;
	int previous_error_no = m_sample_pool.size();
	int curr_error_no, bad_case_no;
	while (true)
	{
		//init_problem(bias);
		double cv_accuracy=cross_validation(5);

		cout << "/***********************************************/" << endl;
				
		curr_error_no = seek_bad_cases(bad_case_no);
		cout << "Training Accuracy: " << (double)(m_file_list.size() - curr_error_no) / m_file_list.size()
			 << " (" << m_file_list.size() - curr_error_no << "|" << m_file_list.size() << ")" << endl
			 << "Add Negative Samples: " << bad_case_no << endl
		     << "#Iter: " << n << " Done ---> [" << previous_error_no - curr_error_no << "|" << MIN_THRESHOLD << "]" << endl;		
			
		int diff = curr_error_no - previous_error_no;
		if (diff > 0 || curr_error_no == 0 )
		{
			break;
		}	

		if (m_max_cv_accuracy <= cv_accuracy)
			m_max_cv_accuracy = cv_accuracy;
		else
		{
			break;
		}			

		ostringstream oss;
		oss << m_output_dir <<"word_prob_model_" << n++ << ".model";
		cout << "Save " << oss.str() << endl;
		save_model(oss.str().c_str(), m_model);
		
        if (abs(diff) <= MIN_THRESHOLD || bad_case_no == 0)
		{
			cout << "Optimization Finished\n";
			cout << "/***********************************************/" << endl;
			break;
		}
		previous_error_no = curr_error_no;
	}	
		
	m_sample_pool.clear(); // Delete the memory for the further operation

}

bool CWordProbTrain::save_word_prob_model(const string &in_idx2ftr_file, const string &out_word_prob_model_file)
{
	ifstream ifs(in_idx2ftr_file.c_str());
	if (!ifs)
	{
		cout << "Can't open file <" << in_idx2ftr_file << ">!" << endl;
		return false;
	}

	ofstream ofs(out_word_prob_model_file.c_str());
	if (!ofs)
	{
		cout << "Can't open file <" << out_word_prob_model_file << ">!" << endl;
		return false;
	}

	string line;
	int idx = 0;
	while (getline(ifs,line))
	{
		if (line.empty())
			continue;
		if (idx >= m_model->nr_feature)
			break;
		ofs << line << "  " << m_model->w[idx]<<endl;
		idx++;
	}	

	ofs.close();
	ifs.close();

	return true;
}

