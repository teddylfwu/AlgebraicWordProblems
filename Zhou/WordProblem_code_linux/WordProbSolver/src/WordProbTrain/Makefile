CXX ?= g++
CC ?= g++
CFLAGS = -Wall -Wconversion  -fPIC -m64 -g
LIBS = blas/blas.a
SHVER = 2 
OS = $(shell uname)
#LIBS = -lblas
VPATH = blas

HEADERS = blas.h blasp.h
OBJS = dnrm2.o daxpy.o ddot.o dscal.o 


all: train 

lib: linear.o tron.o blas/blas.a
	if [ "$(OS)" = "Darwin" ]; then \
		SHARED_LIB_FLAG="-dynamiclib -Wl,-install_name,liblinear.so.$(SHVER)"; \
	else \
		SHARED_LIB_FLAG="-shared -Wl,-soname,liblinear.so.$(SHVER)"; \
	fi; \
	$(CXX) $${SHARED_LIB_FLAG} linear.o tron.o blas/blas.a -o liblinear.so.$(SHVER)

train: tron.o linear.o WordProb.o main.o $(OBJS)
	$(CXX) $(CFLAGS) -o train WordProb.o main.o tron.o linear.o $(OBJS)


tron.o: tron.cpp tron.h
	$(CXX) $(CFLAGS) -c -o tron.o tron.cpp

linear.o: linear.cpp linear.h
	$(CXX) $(CFLAGS) -c -o linear.o linear.cpp


WordProb.o : WordProb.cpp WordProb.h 
	$(CXX) $(CFLAGS) -c WordProb.cpp -o WordProb.o

main.o : main.cpp WordProb.h
	$(CXX) $(CFLAGS) -c main.cpp -o main.o

#blas/blas.a: blas/*.c blas/*.h
#	make -C blas OPTFLAGS='$(CFLAGS)' CC='$(CC)';

$(OBJS): %.o : %.c
	$(CXX) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o
	rm -f train
