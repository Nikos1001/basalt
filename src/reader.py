
from error import Error, Source

class Node:
    
    begin_token = None
    end_token = None

    def __init__(self, begin_token, end_token):
        self.begin_token = begin_token
        self.end_token = end_token

class Int(Node):

    val = 0

    def __init__(self, val, begin_token, end_token):
        super().__init__(begin_token, end_token)
        self.val = val
    
    def __str__(self):
        return str(self.val)

    def match(self, p):
        return p == self.val or p == '##ANY##' or p == '##ANYINT##'


class Sym(Node):

    sym = ''

    def __init__(self, val, begin_token, end_token):
        super().__init__(begin_token, end_token)
        self.sym = val
    
    def __str__(self):
        return self.sym
    
    def match(self, p):
        return p == self.sym or p == '##ANYSYM##' or p == '##ANY##'

class List(Node):

    elems = []

    def __init__(self, elems, begin_token, end_token):
        super().__init__(begin_token, end_token)
        self.elems = elems
    
    def __str__(self):
        res = '('
        for i in range(len(self.elems)):
            if i != 0:
                res += ' '
            res += str(self.elems[i])
        res += ')'
        return res

    def __getitem__(self, key):
        return self.elems[key]
    
    def match(self, p):
        if p == '##ANY##' or p == '##ANYLIST##':
            return True
        if type(p) != tuple:
            return False
        if len(p) != len(self.elems):
            return False
        for i in range(len(self.elems)):
            if not self.elems[i].match(p[i]):
                return False
        return True
    
    def __len__(self):
        return len(self.elems)

class Token:

    type = ''
    start = 0
    end = 0
    line = 0
    val = None
    source = None

    def __init__(self, type, start, end, val, line, source):
        self.type = type
        self.start = start
        self.end = end
        self.val = val
        self.line = line
        self.source = source
    
    def __str__(self):
        return self.type + '@' + str(self.start) + ':' + str(self.end) + ('' if self.val == None else '=' + str(self.val))

class Lexer:
    
    src = None 
    curr = 0
    start = 0
    line = 1
    c = ''

    curr_token = None

    def __init__(self, src):
        self.src = src 

    def advance(self):
        if self.curr < len(self.src.src):
            if self.src.src[self.curr] == '\n':
                self.line += 1
            self.curr += 1

        if self.curr < len(self.src.src):
            self.c = self.src.src[self.curr]
        else:
            self.c = ''

    def skip_whitespace(self):
        while self.curr < len(self.src.src) and self.src.src[self.curr] in ' \t\r\n':
            self.advance()
        self.start = self.curr

    def make_token(self, type, val=None):
        token = Token(type, self.start, self.curr, val, self.line, self.src)
        self.start = self.curr
        self.curr_token = token
        return token

    def scan(self):
        self.skip_whitespace()
        if self.start == len(self.src.src):
            return self.make_token('eof')
        
        if self.c in '()':
            t = self.c
            self.advance()
            return self.make_token(t)
        elif self.c in '1234567890':
            while self.c in '1234567890':
                self.advance()
            return self.make_token('int', int(self.src.src[self.start:self.curr])) 
        else:
            while self.c != '' and self.c not in '() \t\r\n':
                self.advance()
            sym = self.src.src[self.start:self.curr]
            return self.make_token('sym', sym)
 
def parse(lexer):

    if lexer.curr_token.type == 'int':
        token = lexer.curr_token
        val = lexer.curr_token.val
        lexer.scan()
        return ([], Int(val, token, token)) 
    elif lexer.curr_token.type == 'sym':
        token = lexer.curr_token
        val = lexer.curr_token.val
        lexer.scan()
        return ([], Sym(val, token, token))
    elif lexer.curr_token.type == '(':
        begin_token = lexer.curr_token
        lexer.scan()
        elems = []
        errs = []
        while lexer.curr_token.type != ')' and lexer.curr_token.type != 'eof':
            err, elem = parse(lexer)
            errs += err
            elems.append(elem)

        end_token = lexer.curr_token
        if lexer.curr_token.type == ')':
            lexer.scan()
        else:
            errs.append(Error().msg('Expected ).').src_ref(lexer.curr_token, lexer.curr_token).msg('Unmatched opening bracket here:').src_ref(begin_token, begin_token))

        return (errs, List(elems, begin_token, end_token))
    
    token = lexer.curr_token
    lexer.scan()
    return ([Error().msg('Unexpected token.').src_ref(token, token)], None)

    
def read_file(path):

    src_file = open(path, 'r')
    src = src_file.read()
    src_file.close()
    src_obj = Source(src, path)

    lexer = Lexer(src_obj)

    lexer.scan()
    
    errs = []
    asts = []

    while lexer.curr_token.type != 'eof':
        err, ast = parse(lexer)
        errs += err
        asts.append(ast)
    
    return (errs, asts)
