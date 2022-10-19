
(fn main () (seq
    (fn test () 444)
    (fn test (x) 5)
    (print (test))
    (print (test 9))
    (seq
        (fn test () 999)
        (print (test))
        (print (test 9)))))

