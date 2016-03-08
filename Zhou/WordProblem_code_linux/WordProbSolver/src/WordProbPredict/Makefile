
INC = ../liblinear-1.96

wordprobpredict: main.cpp
	g++ -o wordprobpredict main.cpp -I$(INC) -L$(INC) -llinear -O3 

clean:
	rm -f *.o
	rm -f wordprobpredict
