
from error import Error
import parser

name_idx = 0
all_blocks = []

# note: we have 2 stacks
# var stack, and val stack
# val stack -> args 0 1 (aka 4 5)
# var stack -> args 2 3 (aka 6 7) 
class Block:


    def __init__(self):
        global name_idx, all_blocks
        all_blocks.append(self)
        self.name = ''
        name_idx += 1
        x = name_idx
        while x > 0:
            self.name += 'abcdefghijklmnopqrstuvwxyz'[x % 26]
            x //= 26
        self.src =  'copy=cvv 2\n' + \
                    'sconst 13\n' + \
                    'spop 2\n' + \
                    'speek 2\n' + \
                    'smov 4\n' + \
                    'sprintn 2\n' + \
                    '\n' + \
                    self.name + ' 4\n' + \
                    ':\n' + \
                    '\tcopy=cvv 4 0\n' + \
                    '\tcopy=cvv 5 1\n' + \
                    '\tcopy=cvv 6 2\n' + \
                    '\tcopy=cvv 7 3\n'
        self.ext_blocks = []
    
    def const(self, val, var_stack=False):
        parts = []
        v = val 
        while v > 0:
            parts.append(v % 64)
            v //= 64
        parts += [0] * (11 - len(parts))
        self.src += '\tsconst 6 7 ' if var_stack else '\tsconst 4 5 '
        for i in range(len(parts)): 
            self.src += str(parts[len(parts) - i - 1]) + ' '
        self.src += '\n'
    
    def pop(self, var=False):
        self.src += '\tspop 6 7\n' if var else '\tspop 4 5\n'
    
    def peek(self, var_stack=False):
        self.src += '\tspeek 6 7\n' if var_stack else '\tspeek 4 5\n'
    
    def mov_data_to_var(self):
        self.src += '\tsmov 4 5 6 7\n'

    def mov_var_to_data(self):
        self.src += '\tsmov 6 7 4 5\n'

    def call(self, block):
        self.src = block.name + ' 4\n' + self.src
        self.src += '\tcopy=*[+]c 0 4 0\n'
        self.src += '\tcopy=*[+]c 1 6 0\n'
        self.src += '\t' + block.name + ' 4 5 6 7\n'
        self.src += '\tcopy= 2 0\n'
        self.src += '\tcopy*[+v]=v 4 2 0\n'
        self.src += '\tcopy*[+v]=v 6 2 0\n'
    
    def printn(self):
        self.src += '\tsprintn 4 5\n'
    
    def close(self):
        for ext_block in self.ext_blocks:
            self.src = ext_block.name + ' 4\n'
        self.src += ':\n'
        with open('build/' + self.name + '.cio', 'w') as f:
            f.write(self.src)

def close_all_blocks():
    for blk in all_blocks:
        blk.close()

class Type:
    
    marks = None 
    
    def __init__(self):
        self.marks = []

    def __str__(self):
        return ''

    def size(self):
        return 0

class SimpleType(Type):

    type = '' 

    def __init__(self, t):
        super().__init__()
        self.type = t
    
    def __str__(self):
        return super().__str__() + self.type
    
    def size(self):
        if self.type == 'int':
            return 1
        if self.type == 'void':
            return 0
        
    def __eq__(self, o):
        return type(o) == SimpleType and o.type == self.type

class Function:

    specs = None
    native_specs = None
    incar = None
    name = '' 

    def __init__(self, name):
        self.specs = []
        self.incar = []
        self.name = name
        self.native_specs = []
    
    def add_spec(self, ast, errs):
        self.specs = self.specs + [FnSpecialization(ast)]

    def get_incarnation(self, arg_types, comp, errs):
        for spec in self.native_specs:
            if spec.match(arg_types):
                return spec

        for incar_types, incar in self.incar:
            if len(incar_types) == len(arg_types):
                all_same = True 
                for i in range(len(incar_types)):
                    if incar_types[i] != arg_types[i]:
                        all_same = False
                if all_same:
                    return incar
        
        best_score = 0
        best_score_specs = []


        for spec in self.specs:
            spec_score = spec.match(arg_types)
            if spec_score > best_score:
                best_score = spec_score
                best_score_specs = [spec]
            elif spec_score == best_score:
                best_score_specs.append(spec)

        if len(best_score_specs) > 1:
            error = Error().msg('Multiple function definitions for function \'' + self.name + '\' match arguments (' + ' '.join(map(lambda x: str(x), arg_types)) + ').')
            for spec in best_score_specs:
                error.src_ref(spec.ast.name_token, spec.ast.name_token)
            errs.append(error)
        
        if len(best_score_specs) == 0:
            return None

        spec = best_score_specs[0]
        incar = spec.make_incarnation()
        self.incar.append((arg_types, incar))
        incar.compile(comp, arg_types, errs)
        return incar

class FnSpecialization:

    ast = None
    param_types = None
    return_asts = None

    def __init__(self, ast): 
        self.ast = ast 
        self.param_types = list(map(lambda x: x[1], ast.params))
        self.return_asts = []
        self.find_return_asts(ast.body)
    
    def find_return_asts(self, ast):
        if type(ast) == parser.Int or type(ast) == parser.Var or type(ast) == parser.Call:
            self.return_asts.append(ast)
        elif type(ast) == parser.Seq:
            self.find_return_asts(ast.exprs[-1])
        elif type(ast) == parser.VarDecl:
            if ast.val != None:
                self.find_return_asts(ast.val)

    def match(self, arg_types):
        if len(arg_types) != len(self.param_types):
            return -1

        score = 0
        for i in range(len(arg_types)):
            if self.param_types[i] == None:
                score += 1
                continue
            subscore = self.param_types[i].match(arg_types[i])
            if subscore == -1:
                return -1
            score += subscore
        return score
    
    def make_incarnation(self):
        block = Block()
        incarnation = FnIncarnation(block, self) 
        incarnation.ret_type = None
        return incarnation 

class FnNativeSpec:

    match_fn = None
    ret_type_fn = None 
    compile_fn = None

    def __init__(self, match, ret_type, compile):
        self.match_fn = match 
        self.ret_type_fn = ret_type
        self.compile_fn = compile

    def match(self, arg_types):
        return self.match_fn(arg_types) 
    
    def ret_type(self, arg_types):
        return self.ret_type_fn(arg_types) 
    
    def compile(self, block, arg_types):
        self.compile_fn(block, arg_types) 

class FnIncarnation:

    block = None
    ret_type = None
    arg_types = None
    spec = 'unknown' 

    def __init__(self, block, spec):
        self.block = block
        self.spec = spec

    def compile(self, comp, arg_types, errs):
        subcomp = Compiler(self, comp)
        self.arg_types = arg_types
        subcomp.typecheck_args()
        subcomp.typecheck(self.spec.ast.body, errs)
        self.ret_type = 'unknown'
        for ast in self.spec.return_asts:
            t = subcomp.typecheck(ast, errs)
            if t != 'unknown' and t != None:
                self.ret_type = t 
        if self.ret_type == 'unknown': 
            errs.append(Error().msg('Function return type could not be inferred.').src_ref(self.spec.ast.name_token, self.spec.ast.name_token))
        subcomp.typecheck(self.spec.ast.body, errs)
        subcomp.compile_fn_init()
        subcomp.compile(self.spec.ast.body, self.block, errs)

class Variable:
    
    decl = None
    t = None
    offset = 0

    def __init__(self, decl):
        self.decl = decl

class Compiler:

    funcs = None 
    vars = None
    parent_comp = None
    var_decls = None
    callees = None
    expr_types = None
    incar = None
    curr_var_offset = 0
    var_offset = None

    def __init__(self, incar=None, parent=None):
        self.funcs = [{}] 
        self.vars = [{}]
        self.parent_comp = parent
        self.expr_types = {}
        self.var_decls = {}
        self.callees = {}
        self.incar = incar
        self.curr_var_offset = 0
        self.var_offset = {}

    def find_decls(self, ast_list, errs):
        for ast in ast_list:
            if type(ast) == parser.VarDecl:
                self.find_decls([ast.val], errs)
            if type(ast) == parser.Call:
                self.find_decls(ast.args, errs)
            if type(ast) == parser.FnDecl:
                if not ast.fn_name in self.funcs[-1]:
                    self.funcs[-1][ast.fn_name] = Function(ast.fn_name)
                self.funcs[-1][ast.fn_name].add_spec(ast, errs)
        
    def typecheck_helper(self, ast, errs):
        if type(ast) == parser.Int:
            return SimpleType('int')
        elif type(ast) == parser.FnDecl:
            return SimpleType('void')
        elif type(ast) == parser.Seq:
            res_type = None
            self.funcs.append({})
            self.find_decls(ast.exprs, errs)
            self.vars.append({})
            prev_offset = self.curr_var_offset
            for expr in ast.exprs:
                res_type = self.typecheck(expr, errs)
                if res_type == 'unknown':
                    return 'unknown'
            self.funcs.pop()
            self.vars.pop()
            self.curr_var_offset = prev_offset
            return res_type
        elif type(ast) == parser.Var:
            name = ast.sym
            var = None
            for i in range(len(self.vars)):
                if name in self.vars[-i]:
                    var = self.vars[-i][name]
                    break
            if var == None:
                errs.append(Error().msg('Variable \'' + name + '\' does not exist.').ast_ref(ast))
                return None
            self.var_decls[ast.id] = var
            return var.t 
        elif type(ast) == parser.VarDecl:
            name = ast.name
            if name in self.vars[-1]:
                errs.append(Error().msg('Variable redefinition.').ast_ref(ast).msg('Previous definition here:').ast_ref(self.vars[-1][name].decl))
                return self.typecheck(self.vars[-1][name].decl, errs)
            self.vars[-1][name] = Variable(ast) 
            if ast.val == None and ast.type == None:
                errs.append(Error().msg('Cannot infer type of variable.').ast_ref(ast).msg('Please provide an inital value or explicit type.'))
                return None
            if ast.val == None and ast.type != None:
                self.vars[-1][name].t = self.eval_type(ast.type, errs, None)
            if ast.val != None and ast.type == None:
                self.vars[-1][name].t = self.typecheck(ast.val, errs)
            if ast.val != None and ast.type != None:
                self.vars[-1][name].t = self.eval_type(ast.type, errs, ast.val) 
            self.vars[-1][name].offset = self.curr_var_offset
            self.curr_var_offset += self.vars[-1][name].t.size()
            return self.vars[-1][name].t
        elif type(ast) == parser.Call:
            arg_types = []
            for arg in ast.args:
                t = self.typecheck(arg, errs)
                if t == 'unknown':
                    self.callees[ast.id] = None
                    return 'unknown'
                arg_types.append(t)
                
            callee = self.get_incarn(ast.fn_name, arg_types, errs)
            self.callees[ast.id] = callee
            if callee == None:
                errs.append(Error().msg('Function \'' + ast.fn_name + '\' with arguments (' + ' '.join(map(lambda x: str(x), arg_types)) + ') does not exist.').ast_ref(ast))
                return None
            else:
                if type(callee) == FnNativeSpec:
                    return callee.ret_type(arg_types)
                if callee.ret_type == None:
                    return 'unknown'
                return callee.ret_type
        
        elif type(ast) == parser.SimpleType:
            return SimpleType(ast.type)
    
    def typecheck_args(self):
        for i in range(len(self.incar.arg_types)):
            arg_type = self.incar.arg_types[i]
            arg = self.incar.spec.ast.params[i]
            arg_name = arg[0]
            self.vars[-1][arg_name] = Variable(None)
            self.vars[-1][arg_name].t = arg_type
            self.vars[-1][arg_name].offset = self.curr_var_offset
            self.curr_var_offset += arg_type.size()
    
    def compile_fn_init(self):
        total_arg_size = sum([arg.size() for arg in self.incar.arg_types])
        for i in range(self.curr_var_offset):
            self.incar.block.const(self.curr_var_offset - i)
            self.incar.block.peek()
            self.incar.block.mov_data_to_var()

    def typecheck(self, ast, errs):

        if ast.id in self.expr_types and self.expr_types[ast.id] != 'unknown':
            return self.expr_types[ast.id]

        t = self.typecheck_helper(ast, errs)
        self.expr_types[ast.id] = t
        self.var_offset[ast.id] = self.curr_var_offset
        return t
    
    def eval_type(self, ast, errs, val):
        ref_type = None
        if val != None:
            ref_type = self.typecheck(val, errs)

        if type(ast) == parser.SimpleType:
            if ref_type != None:
                if type(ref_type) != SimpleType or ref_type.type != ast.type:
                    errs.append(Error().msg('Type mismatch.').ast_ref(ast).msg('Value here:').ast_ref(val))
            return SimpleType(ast.type)

    def compile(self, ast, block, errs):
        if type(ast) == parser.Int:
            block.const(ast.val) 
        elif type(ast) == parser.Seq:
            prev_size = 0
            for expr in ast.exprs:
                for i in range(prev_size):
                    block.pop()
                self.compile(expr, block, errs)
                t = self.typecheck(expr, errs)
                if isinstance(t, Type):
                    prev_size = t.size()
            for i in range(self.var_offset[ast.exprs[-1].id] - self.var_offset[ast.id]):
                block.pop(True)
        elif type(ast) == parser.Call:
            for arg in ast.args:
                self.compile(arg, block, errs)
            if not ast.id in self.callees:
                self.typecheck(ast, errs)
            callee = self.callees[ast.id]

            if callee != None:
                if type(callee) == FnNativeSpec:
                    callee.compile(block, [self.typecheck(arg, errs) for arg in ast.args])
                else:
                    block.call(callee.block)
        elif type(ast) == parser.Var:
            if not ast.id in self.var_decls:
                return
            var = self.var_decls[ast.id]
            t = var.t
            for i in range(t.size()):
                block.const(self.var_offset[ast.id] - var.offset - i, True)
                block.peek(True)
                block.mov_var_to_data()
        elif type(ast) == parser.VarDecl:
            if ast.val == None:
                for i in range(self.typecheck(ast, errs).size()):
                    block.const(0, True)
                    block.const(0, False)
            else:
                self.compile(ast.val, block, errs)
                size = self.typecheck(ast, errs).size()
                for i in range(size):
                    block.const(size - i)
                    block.peek()
                    block.mov_data_to_var()

    def get_incarn(self, fn_name, arg_types, errors):

        for i in range(len(self.funcs)):
            funcs = self.funcs[-i]
            if fn_name in funcs: 
                fn = funcs[fn_name]
                incar = fn.get_incarnation(arg_types, self, errors)
                if incar != None:
                    return incar

        if self.parent_comp != None:
            return self.parent_comp.get_incarn(fn_name, arg_types, errors)
        return None