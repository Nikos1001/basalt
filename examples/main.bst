
(fn print-tuple (tup) (seq
    (let x 0)
    (let y tup)
    (print (idx (var-ptr x) 1))
    (print (idx (var-ptr x) 2))
    (print (idx (var-ptr x) 3))))

(fn main () (seq
    (let x (tuple 1 2 3))
    (print-tuple x)))

