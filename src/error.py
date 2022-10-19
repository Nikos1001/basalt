
class Source:

    src = ''
    path = ''
    line_start = {}

    def __init__(self, src, path):
        self.src = src
        self.path = path
        line = 1
        self.line_start[1] = 0
        for i in range(len(src)):
            if src[i] == '\n':
                line += 1
                self.line_start[line] = i + 1
        self.line_start[line + 1] = len(src) + 1

class Error:

    def __init__(self):
        self.err_parts = []

    def msg(self, msg):
        self.err_parts.append(('msg', msg))
        return self
    
    def src_ref(self, token_begin, token_end):
        self.err_parts.append(('src_ref', token_begin, token_end))
        return self
    
    def ast_ref(self, ast):
        return self.src_ref(ast.list.begin_token, ast.list.end_token)
    
    def print(self):

        for part in self.err_parts:

            if part[0] == 'msg':
                _, msg = part
                print(msg)
            elif part[0] == 'src_ref':
                _, begin_token, end_token = part
                src = begin_token.source
                begin_line = begin_token.line
                end_line = end_token.line

                print(src.path + ':')

                start_char = src.line_start[begin_line]
                end_char = src.line_start[end_line + 1] - 1
                segment = src.src[start_char:end_char]
                segment_lines = segment.split('\n')
                for i in range(begin_line, end_line + 1):
                    line_num_str = str(i)
                    print(' ' * (4 - len(line_num_str)) + line_num_str + ' | ' + segment_lines[i - begin_line])
                
                if begin_token.line == end_token.line:
                    offset = begin_token.start - start_char
                    segment_len = end_token.end - begin_token.start

                    # account for \t being 4 spaces wide
                    space_chars = 7 + offset
                    for i in range(start_char, begin_token.start):
                        if begin_token.source.src[i] == '\t':
                            space_chars += 3

                    print(' ' * (7 + offset) + '^' + '~' * (segment_len - 1))
        
        print()

