
#include "WordProb.h"





int main(int argc, char** argv)
{
	for (int idx = 0; idx <= 4; idx++)
	{
		bool semi_supervised = false;

		string output_dir_template("./result/result_%d/");    //the output dir of the model
		string file_list_template("train_index/train_%d.txt");	   //the index file of the training data

		string input_dir("../../word_prob_ftr/");	     //the directory of the training data
		string idx2ftr_file("../../model/idx2ftr.txt");

		if (semi_supervised)
		{
			output_dir_template = "./result/result_semi_%d/";
			input_dir = "../../word_prob_ftr_semi/";
			idx2ftr_file = "../../model_semi/idx2ftr.txt";
            file_list_template = "train_index/train_%d.txt";
		}

		const int buffer_size = 100;
		char output_dir[buffer_size];
		char file_list[buffer_size];
		snprintf(output_dir, sizeof(output_dir), output_dir_template.c_str(), idx);
		snprintf(file_list, sizeof(file_list), file_list_template.c_str(), idx);

		string word_prob_model_file = string(output_dir) + "word_prob_model_info.txt";     //the output dir of the information of the model

		double bias = -1;
		CWordProbTrain WordProb(input_dir, file_list, output_dir, 0.01, 0.01);
		time_t start_t = time(NULL);
		WordProb.train(bias);
		time_t end_t = time(NULL);
		double time_cost = difftime(end_t, start_t);
		WordProb.save_word_prob_model(idx2ftr_file, word_prob_model_file);	

		string time_and_neg_cnt_file = string(output_dir) + "time_and_neg_cnt.txt";
		ofstream ofs(time_and_neg_cnt_file.c_str());
		ofs<<"time: " << time_cost << endl;
		ofs << WordProb.get_sample_info() << endl;
		ofs << "Set Size: " << MAX_SAMPLES << endl;
		ofs.close();
	}
	

}
