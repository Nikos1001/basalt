
from error import Error

curr_ast_id = 0
class Ast:

    list = None
    id = -1

    def __init__(self, list):
        global curr_ast_id
        self.id = curr_ast_id
        curr_ast_id += 1
        self.list = list

# Expr ASTs

class Int(Ast):

    val = 0

    def __init__(self, list, val):
        super().__init__(list)
        self.val = val
    
    def dump(self, offset=0):
        print('\t' * offset + str(self.val))

class Var(Ast):

    sym = ''

    def __init__(self, list, sym):
        super().__init__(list)
        self.sym = sym
    
    def dump(self, offset=0):
        print('\t' * offset + self.sym)

class VarDecl(Ast):

    name = ''
    type = None
    val = None

    def __init__(self, list, name, type, val):
        super().__init__(list)
        self.name = name
        self.type = type
        self.val = val
    
    def dump(self, offset=0):
        print('\t' * offset + 'var decl ' + self.name)
        if self.type != None:
            self.type.dump(offset + 1)
        if self.val != None:
            self.val.dump(offset + 1)

class Seq(Ast):

    exprs = []

    def __init__(self, list, exprs):
        super().__init__(list)
        self.exprs = exprs
    
    def dump(self, offset=0):
        print('\t' * offset + 'seq')
        for expr in self.exprs:
            expr.dump(offset + 1)

class FnDecl(Ast):

    fn_name = None
    params = []
    body = None
    name_token = None

    def __init__(self, list, fn_name, params, body, name_token):
        super().__init__(list)
        self.fn_name = fn_name
        self.params = params
        self.body = body
        self.name_token = name_token
    
    def dump(self, offset=0):
        print('\t' * offset + 'fn ' + self.fn_name)
        for param in self.params:
            print('\t' * (offset + 1) + 'param ' + param[0])
            if param[1] != None:
                param[1].dump(offset + 2)
            else:
                print('\t' * (offset + 2) + 'ANY TYPE')
        self.body.dump(offset + 1)

class Call(Ast):

    fn_name = None
    args = None

    def __init__(self, list, fn_name, args):
        super().__init__(list)
        self.fn_name = fn_name
        self.args = args
    
    def dump(self, offset=0):
        print('\t' * offset + 'call ' + self.fn_name)
        for arg in self.args:
            arg.dump(offset + 1)


# Type ASTs

class SimpleType(Ast):

    type = ''

    def __init__(self, list, type):
        super().__init__(list)
        self.type = type
    
    def dump(self, offset=0):
        print('\t' * offset + self.type)
    
    def match(self, t):
        import compiler
        if type(t) != compiler.SimpleType:
            return -1
        if t.type != 'int':
            return -1
        return 2

    def __eq__(self, o):
        return type(o) == SimpleType and self.type == o.type


def parse_type(list, errs):

    if list.match('int'):
        return SimpleType(list, list.sym)

    errs.append(Error().msg('Expected type.').src_ref(list.begin_token, list.end_token))
    return None

def parse(list, errs):

    if list.match('##ANYINT##'):
        return Int(list, list.val) 
    
    if list.match('##ANYSYM##'):
        return Var(list, list.sym)
    
    if len(list) > 0 and list[0].match('let'):
        if len(list) < 2:
            errs.append(Error().msg('Expected variable name.').src_ref(list.begin_token, list.end_token))
            return None

        name = None
        type = None 
        val = None

        if list[1].match('##ANYSYM##'):
            name = list[1].sym
        elif list[1].match(('##ANYSYM##', '##ANY##')):
            name = list[1][0].sym
            type = parse_type(list[1][1], errs)
        else:
            errs.append(Error().msg('Expected variable name.').src_ref(list[1].begin_token, list[1].end_token))
        
        if len(list) > 2:
            val = parse(list[2], errs)
        
        if len(list) > 3:
            errs.append(Error().msg('Unexpected values.').src_ref(list[3].begin_token, list[-1].end_token))

        return VarDecl(list, name, type, val)

    if len(list) > 0 and list[0].match('seq'):
        exprs = [parse(expr, errs) for expr in list[1:]]
        return Seq(list, exprs)

    if len(list) > 0 and list[0].match('fn'):
        if len(list) < 2 or not list[1].match('##ANYSYM##'):
            errs.append(Error().msg('Expected function name.').src_ref(list.begin_token, list.end_token))
        elif len(list) < 3 or not list[2].match('##ANYLIST##'):
            errs.append(Error().msg('Expected parameter list.').src_ref(list.begin_token, list.end_token))
        elif len(list) < 4:
            errs.append(Error().msg('Expected function body.').src_ref(list.begin_token, list.end_token))
        
        if len(list) > 4:
            errs.append(Error().msg('Unexpected values.').src_ref(list[4].begin_token, list[-1].begin_token))

        if len(errs) > 0:
            return None 

        args = []
        for arg in list[2]:
            if arg.match('##ANYSYM##'):
                args.append((arg.sym, None))
            elif arg.match(('##ANYSYM##', '##ANY##')):
                arg_type = parse_type(arg[1], errs)
                args.append((arg[0].sym, arg_type))
            else:
                errs.append(Error().msg('Expected parameter.').src_ref(arg.begin_token, arg.end_token))

        body_ast = parse(list[3], errs)
        func = FnDecl(list, list[1].sym, args, body_ast, list[1].begin_token)

        return func 
    
    if len(list) > 0 and list[0].match('##ANYSYM##'):
        args = [parse(expr, errs) for expr in list[1:]]
    
        return Call(list, list[0].sym, args)

    errs.append(Error().msg('Expected expression.').src_ref(list.begin_token, list.end_token))
    return None 
