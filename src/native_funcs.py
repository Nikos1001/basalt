
import compiler

def print_match(args):
    if len(args) > 1:
        return False

    if type(args[0]) == compiler.SimpleType and args[0].type == 'int' or type(args[0]) == compiler.PointerType:
        return True

    return False

def print_ret_type(args):
    return compiler.SimpleType('void')

def print_compile(block, args):
    block.printn()
    
print_spec = compiler.FnNativeSpec(print_match, print_ret_type, print_compile)

def idx_match(args):
    if len(args) >= 1 and len(args) <= 3:
        if type(args[0]) != compiler.PointerType:
            return False
        if len(args) >= 2 and (type(args[1]) != compiler.SimpleType and args[1].type != 'int'):
            return False 
        if len(args) >= 3 and args[2] != args[0].type:
            return False 
        return True
    return False

def idx_ret_type(args):
    return args[0].type

def idx_compile(block, args):
    arg_size = sum([arg.size() for arg in args])
    for i in range(arg_size):
        block.const(arg_size - i)
        block.peek()
        block.mov_data_to_var() 
    for i in range(arg_size):
        block.pop()
    size = args[0].type.size()
    for i in range(size):

        block.const(arg_size, True)
        block.peek(True)
        block.const(size - 1 - i, True)
        block.add(True)
        if len(args) >= 2:
            block.const(arg_size, True)
            block.peek(True)
            block.const(size * 8, True)
            block.mul(True)
            block.add(True)

        if len(args) == 3:
            block.const(arg_size - 1 - i, True)
            block.peek(True)
            block.const(1, True)
            block.peek(True)
            block.mov_var_to_data()
            block.store(True)
        else:
            block.deref(True)
            block.mov_var_to_data()
    for i in range(arg_size):
        block.pop(True)

idx_spec = compiler.FnNativeSpec(idx_match, idx_ret_type, idx_compile)
