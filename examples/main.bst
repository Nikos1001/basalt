
(fn main () (seq
    (let x 5)
    (let y 666)
    (print (var-ptr x))
    (print (var-ptr y))
    (seq
        (let z 9)
        (print (var-ptr z)))
    (let z 99)
    (print (var-ptr z))))


