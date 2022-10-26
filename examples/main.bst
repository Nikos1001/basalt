
(fn main () (seq
    (let x 5)
    (let y 9)
    (idx (var-ptr x) 1 100)
    (print x)
    (print y)))
