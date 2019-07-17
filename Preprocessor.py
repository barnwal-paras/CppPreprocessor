import getopt
import logging
import re
import sys
from collections import deque

logging.basicConfig()
log = logging.getLogger(__name__)
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)


class funcMacro:
    """
    This class stores functional macros

    Attributes
        name        name of function
        params      list of parameters
        expression  function expression with parameter in the form of {i} in string
    """

    def __init__(self, declaration: str, expression: str):
        """
        Description:
        Initialize class to store functional macros
        :param declaration: function declaration passed in the form of string eg. "add(a,b)"
        :param expression:  example: "a+b"
        """

        self.name = declaration[:declaration.index('(')]

        self.params = funcMacro.getparams(declaration)

        tokens = Preprocessor(expression).tokenize()

        log.debug(expression)
        for i in range(len(tokens)):
            if tokens[i] in self.params:
                tokens[i] = '{' + str(self.params.index(tokens[i])) + '}'

        self.expression = ''.join(tokens)
        log.debug(self.expression)

    @staticmethod
    def getparams(text):
        """
        Description: extract text from document
        :param text:
        :return:
        """

        paramtext = text[text.index('('):]

        param = []
        word = ''
        paramtext = deque(paramtext)
        count = 0

        while len(paramtext):

            if paramtext[0] == '(':
                count += 1
                if count > 1:
                    word += paramtext.popleft()
                else:
                    paramtext.popleft()
            elif paramtext[0] == ')':
                count -= 1
                if count:
                    word += paramtext.popleft()
                else:
                    param += [word]
                    break
            elif count == 1 and paramtext[0] == ',':
                paramtext.popleft()
                param += [word]
                word = ''
            else:
                word += paramtext.popleft()
        else:
            raise Exception("not a functional macro expression" + " " + text)
        return param

    def replace_macro(self, params):
        """

        :param params: custom parameter to replace the parameter in the original expression
        :return: new expression
        """

        return self.expression.format(*params)


class Preprocessor:
    separator = '\n\n'
    __libpath = None


    def __init__(self, text: str):

        self.text = text
        self.func = {}
        self.macros = {}
        if not Preprocessor.__libpath:
            with open('config.txt', 'r') as conf_file:
                Preprocessor.__libpath = conf_file.read()

    @staticmethod
    def read_file(filename: str) -> str:
        with open(filename, 'r') as cfile:
            return cfile.read()

    def tokenize(self) -> list:

        texts = deque(re.split('(\\n)', self.text))
        texts_n = []

        while texts:
            token = texts.popleft()
            if token and token[0] == '#':
                texts_n += [token]
            else:
                texts_n += re.split('( )|(=)|'
                                    '(;)|({)|(})|([)|(])'
                                    '|(,)|(>>)|(<<)|(\\n)|(<)|(>)|'
                                    '(\+)|(-)|(\*)|(/)|(\?)', token)

        texts_n = [text for text in texts_n if text]
        return texts_n

    def remove_comment(self) -> str:
        """
        Description: remove comments from text
        :return: text without comments
        """

        text: deque[str] = deque(self.text)
        quote = False
        new_text = ''
        while text:
            char = text.popleft()
            if char == '"':
                quote = not quote
                new_text += char
            elif char == '\n':
                quote = False
                new_text += char
            elif char == '/' and quote == False:
                next = text.popleft()
                if next == '/':
                    while text.popleft() != '\n':
                        continue
                    else:
                        new_text += '\n'
                elif next == '*':

                    while text.popleft() != '*' or text[0] != '/':
                        continue
                    else:
                        text.popleft()
                else:
                    new_text += char
                    new_text += next
            else:
                new_text += char

        return new_text

    def preprocess(self) -> str:

        self.text = self.remove_comment()

        texts = deque(self.tokenize())

        new_text = deque()

        while texts:
            text = texts.popleft()

            # preprocessor directives
            if self.__is_preprocessor_directive(text):
                type = self.__check_dirtype(text)

                if type == 'MACROS':
                    textl = re.split(' ', text)
                    self.macros[textl[1]] = textl[2]

                elif type == 'UNDEF':
                    textl = re.split(' ', text)
                    del (self.macros[textl[1]])

                elif type in ('FILEINCL', 'STDLIB'):
                    search = re.search('(".*")|(\'.*\')', text)
                    filename = text[search.start() + 1:search.end() - 1]
                    if type == 'FILEINCL':
                        nfile = Preprocessor.read_file(filename)
                    else:
                        nfile = Preprocessor.read_file(Preprocessor.__libpath + filename)
                    processed_nfile = Preprocessor(nfile).preprocess()
                    new_text.appendleft(processed_nfile)

                elif type == 'FUNC':

                    textl = re.split(' ', text)

                    fmacro = funcMacro(textl[1], textl[2])
                    key = fmacro.name
                    self.func[textl[1][:textl[1].index('(')]] = fmacro

                elif type in ('IF', 'ELIF', 'IFDEF', 'IFNDEF'):
                    text = text[1:]
                    if type == 'IF' or (type == 'ELIF' and condition is True):
                        condition = self.eval_dir_cond(text)
                    elif type == 'IFDEF':
                        keyword = text.split(' ')[1]
                        if keyword in self.func.keys() or keyword in self.macros.keys():
                            condition = True
                        else:
                            condition = False
                    elif type == 'IFNDEF':
                        keyword = text.split(' ')[1]
                        if keyword in self.func.keys() or keyword in self.macros.keys():
                            condition = False
                        else:
                            condition = True

                    else:
                        condition = False
                    block = ''
                    count = 0
                    while not (count == 1) and texts:
                        block += texts.popleft()
                        if self.__is_preprocessor_directive(texts[0]):
                            if self.__check_dirtype(texts[0]) in ("IF", "IFDEF", "IFNDEF"):
                                count -= 1
                            elif self.__check_dirtype(texts[0]) in ("ELSE", "ENDIF", "ELIF"):
                                count += 1
                    if condition:
                        preprocessor_obj = Preprocessor(block)
                        preprocessor_obj.macros = self.macros
                        preprocessor_obj.func = self.func
                        new_text.append(preprocessor_obj.preprocess())
                        self.macros = preprocessor_obj.macros
                        self.func = preprocessor_obj.func
                elif type in 'ENDIF':
                    pass
            else:
                if text in self.macros.keys():
                    text = self.macros[text]
                    new_text.append(text)



                elif text in self.func.keys() and texts[0] == '(':
                    count = 1

                    next = texts.popleft()
                    while texts:
                        if texts[0] == '(':
                            count += 1
                        elif texts[0] == ')':
                            count -= 1
                        next += texts.popleft()
                        if not count:
                            break
                    new_text.append(self.replace_func_macros(text + next))
                else:
                    new_text.append(text)

        return ''.join(list(new_text))

    def eval_dir_cond(self, text) -> bool:
        def_statements = re.findall('defined\s*\S*', text)

        sub = {"\|\|": " or ", "\&&": " and ", "!": " not "}

        for cond in def_statements:
            keywords = cond.split(' ')
            keyword = re.sub('[()]', '', keywords[1])
            if keyword in self.macros.keys() or keyword in self.func.keys():
                sub[cond] = 'True'
            else:
                sub[cond] = 'False'

        for key in sub.keys():
            text = re.sub(key, sub[key], text)
        for key in self.macros.keys():
            text = re.sub(key, self.macros[key], text)

        return eval(text[2:])

    def replace_func_macros(self, text) -> str:

        fmacros = self.check_func_macros(text)
        if fmacros:
            params = funcMacro.getparams(text)
            params = [self.replace_func_macros(param) for param in params]
            return fmacros.replace_macro(params)

        return text

    def check_func_macros(self, text) -> bool:

        if re.match('^.+\(.+\)$', text) and text[:text.index('(')] in self.func.keys():
            return self.func[text[:text.index('(')]]

        return False

    @staticmethod
    def __is_preprocessor_directive(text) -> bool:
        """
        Description:
        :param text:
        :return:
        """
        if (text[0] == '#'):
            return True
        return False

    @staticmethod
    def __check_dirtype(text) -> str:

        texts = re.split(' ', text)

        if texts[0] == '#define':
            if '(' in texts[1]:
                return 'FUNC'
            return 'MACROS'

        if texts[0] == '#undef':
            return 'UNDEF'

        if re.match('^#include( )*<.*>', text):
            return 'STDLIB'

        if re.match('^#include( )*(".*")|(\'.*\')', text):
            return 'FILEINCL'
        if texts[0] == '#if':
            return 'IF'
        if texts[0] == '#ifdef':
            return 'IFDEF'
        if texts[0] == '#else':
            return 'ELSE'
        if texts[0] == '#endif':
            return 'ENDIF'




def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('Preprocessor.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('Preprocessor.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    return inputfile, outputfile


if __name__ == "__main__":
    input, output = main(sys.argv[1:])

    file = open(input, 'r')

    content = file.read()

    Preprocessor_obj = Preprocessor(content)
    res = Preprocessor_obj.preprocess()
    write_file = open(output, 'w')
    write_file.write(res)
    write_file.close()
