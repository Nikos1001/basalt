
(fn sq ((x int))
    (* x x))

(fn sq-sum ((a (tuple)))
    0)

(fn sq-sum (a)
    (+ (sq (car a)) (sq-sum (cdr a)))) 

(fn main () (seq
    (print (sq-sum (tuple 1 2 3 4 5)))))

