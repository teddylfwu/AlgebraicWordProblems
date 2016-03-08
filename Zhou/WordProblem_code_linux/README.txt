1. Get into the directory GetWordProblemFeature, and use 
		python WordProbFeature.py
   to extract the features and generate the data for training and testing.
   You may need to modify the input and output path in the main function if the script doesn't run properly.

2. The directory model/model, model/model_semi, result/word_prob_ftr and result/word_prob_ftr_semi will be used in the following steps, you can move them to the WordProbSolver directory.

3. Get into the directory WordProbSolver/src/WordProbTrain, use 
		make
   to compile the code.
 
4. Use
		nohup ./train & > nohup.out
   to train the model. It will take quite a while.

5. Get into the directory WordProbSolver/src/WordProbPredict, use 
		make
   to compile the code.

6. Use 
		./wordprobpredict > result 
   to get the final result. The final 5-fold cv accuracy can be found in the last line.