
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
