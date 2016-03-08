from __future__ import division
__author__ = 'zhoulipu'
# ax = b
def linear_equation_v1o1(a,b):
    if a == 0:
        return []
    else:
        return [b/a]
# a1x+b1y=c1
# a2x+b2y=c2
def linear_equation_v2o1(a1, b1, c1, a2, b2, c2):

    t1 = a1*b2 - b1*a2
    if t1 == 0:
        return []

    t2 = c1*b2 - b1*c2
    t3 = a1*c2 - c1*a2

    return t2/t1, t3/t1

calc_word_prob = {}
calc_word_prob['(a*m)+(b*n)+-c = 0, (-d*m)+n = 0'] = lambda a, b, c, d: linear_equation_v2o1(a, b, c, -d, 1, 0)
calc_word_prob['(a*m)+(b*m)+-c = 0'] = lambda a, b, c: linear_equation_v1o1(a+b, c)
calc_word_prob['(a*m)+(b*n)+-c = 0, (d*n)+(b*m)+-e = 0'] = lambda a, b, c, d, e: linear_equation_v2o1(a, b, c, b, d, e)
calc_word_prob['(a*0.01*m)+(b*0.01*n)+-c = 0, -d+m+n = 0'] = lambda a, b, c, d: linear_equation_v2o1(a*0.01, b*0.01, c, 1, 1, d)
calc_word_prob['-a+-m+n = 0, -b+m+n = 0'] = lambda a, b: linear_equation_v2o1(-1, 1, a, 1, 1, b)
calc_word_prob['(a*m)+-b+-c = 0'] = lambda a, b, c: linear_equation_v1o1(a, b+c)
calc_word_prob['(a*m)+-b = 0'] = lambda a, b: linear_equation_v1o1(a, b)
calc_word_prob['(a*m)+(b*n)+(-c*d) = 0, -d+m+n = 0'] = lambda a, b, c, d: linear_equation_v2o1(a, b, c*d, 1, 1, d)
calc_word_prob['(a*m)+-b+-n = 0, -c+m+n = 0'] = lambda a, b, c: linear_equation_v2o1(a, -1, b, 1, 1, c)
calc_word_prob['a+-b+(-c*0.01*m) = 0'] = lambda a, b, c: linear_equation_v1o1(-c*0.01, b-a)
calc_word_prob['(a*(-m+n))+-b = 0, (c*(m+n))+-b = 0'] = lambda a, b, c: linear_equation_v2o1(-a, a, b, c, c, b)
calc_word_prob['(a*m)+-b+(-c*n) = 0, -d+m+n = 0'] = lambda a, b, c, d: linear_equation_v2o1(a, -c, b, 1, 1, d)
calc_word_prob['(a*0.01*m)+(b*0.01*n)+(-c*d*0.01) = 0, -d+m+n = 0'] = lambda a, b, c, d: linear_equation_v2o1(0.01*a, 0.01*b, 0.01*c*d, 1, 1, d)
calc_word_prob['(a*m)+(-b*n) = 0, -c+m+n = 0'] = lambda a, b, c: linear_equation_v2o1(a, -b, 0, 1, 1, c)
calc_word_prob['(a*m)+-b+(-c*m) = 0'] = lambda a, b, c: linear_equation_v1o1(a-c, b)
calc_word_prob['a+(b*m)+-c+(-d*m) = 0'] = lambda a, b, c, d: linear_equation_v1o1(b-d, c-a)
calc_word_prob['a+-b+(-c*m) = 0'] = lambda a, b, c: linear_equation_v1o1(-c, b-a)
calc_word_prob['(-a/b)+m = 0'] = lambda a, b: linear_equation_v1o1(1, a/b)
calc_word_prob['(a*m)+(b*n)+-c = 0, (d*m)+(e*n)+-f = 0'] = lambda a, b, c, d, e, f: linear_equation_v2o1(a, b, c, d, e, f)
calc_word_prob['a+-b+m = 0'] = lambda a, b: linear_equation_v1o1(1, b-a)
calc_word_prob['(0.05*m)+(0.1*n)+-a = 0, -b+m+n = 0'] = lambda a, b: linear_equation_v2o1(0.05, 0.1, a, 1, 1, b)
calc_word_prob['(a*m)+(b*n)+-c = 0, -d+-m+n = 0'] = lambda a, b, c, d: linear_equation_v2o1(a, b, c, -1, 1, d)
calc_word_prob['(a*m)+-b = 0, (-c*m)+n = 0'] = lambda a, b, c: linear_equation_v2o1(a, 0, b, -c, 1, 0)
calc_word_prob['-a+(-b*m)+n = 0, -c+m+n = 0'] = lambda a, b, c: linear_equation_v2o1(-b, 1, a, 1, 1, c)
calc_word_prob['(2.0*m)+(4.0*n)+-a = 0, -b+m+n = 0'] = lambda a, b: linear_equation_v2o1(2, 4, a, 1, 1, b)
calc_word_prob['(a*m)+(b*n)+-c = 0, -d+m+n = 0'] = lambda a, b, c, d: linear_equation_v2o1(a, b, c, 1, 1, d)
calc_word_prob['-a+m+n = 0, (-b*m)+n = 0'] = lambda a, b: linear_equation_v2o1(1, 1, a, -b, 1, 0)
calc_word_prob['(a*m)+(a*n)+-b = 0, -c+-m+n = 0'] = lambda a, b, c: linear_equation_v2o1(a, a, b, -1, 1, c)

if __name__ == '__main__':
    print linear_equation_v2o1(3, 2, 6, 6, 4, 12)
    print linear_equation_v2o1(3, -5, 0, 1, 1, 24)
    print calc_word_prob['(a*m)+(b*n)+-c = 0, (-d*m)+n = 0'](*[1, 1, 177, 2])
    print calc_word_prob['(a*m)+(b*n)+-c = 0, (d*n)+(b*m)+-e = 0'](*[4, 2, 1, 3, 0.7])