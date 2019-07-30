import argparse
import datetime
# import getopt
import logging
import os
import re
from collections import deque

logging.basicConfig()
log = logging.getLogger(__name__)
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="input file", action="store",
                    type=str, required=True)
parser.add_argument("-o", "--output", help="output file", action="store",
                    type=str, required=False)
parser.add_argument('-d', '--cpp_directories', action='append',
                    help='list of path where c plus plus library files are located', required=False)
res = parser.parse_args()

class functional_Macro:
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
        self.params = functional_Macro.getparams(declaration)
        tokens = Preprocessor(expression).tokenize()

        for i in range(len(tokens)):
            if tokens[i] in self.params:
                tokens[i] = '{' + str(self.params.index(tokens[i])) + '}'

        self.expression = ''.join(tokens)

    @staticmethod
    def getparams(text):
        """
        :return: return the parameters of functional macros eg: func(a,b) -> ['a','b']
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
    """
    Preprocessor class
    Attributes
        self.text   stores the text file
        self.func   dictionary to store functional macros
        self.macros dictionary to store macros
        self.lib_path   list of path of cplusplus header files
    """

    separator = '\n\n'

    def __init__(self, text: str, dir=[]):

        self.text = text
        self.func = {}
        self.macros = {}
        self.__add_predefined_macros()
        self.lib_paths = dir
        path = os.path.realpath(__file__)
        path = list(path)

        while path[-1] != '/':
            path.pop()
        path = ''.join(path)



    def __add_predefined_macros(self):
        predefined_macro = dict()
        predefined_macro['__DATE__'] = '{} {} {}'.format(datetime.datetime.now().month, datetime.datetime.now().day,
                                                         datetime.datetime.now().year)
        predefined_macro['__TIME__'] = '{}:{}:{}'.format(datetime.datetime.now().hour, datetime.datetime.now().minute,
                                                         datetime.datetime.now().second)
        predefined_macro['__STDC__'] = "1"
        predefined_macro['__cplusplus'] = "201402"
        self.macros = {**self.macros, **predefined_macro}

    @staticmethod
    def read_file(filename: str) -> str:
        with open(filename, 'r') as cfile:
            return cfile.read()


    def tokenize(self) -> list:
        """
        Description: tokenize given text
        :return: list of tokens and preprocessor directive.
        """

        texts = deque(re.split('(\\n)', self.text))
        texts_n = []

        while texts:
            token = texts.popleft()
            if token and token[0] == '#':
                token = re.sub('#\s*', '#', token)
                texts_n += [token]
            else:
                texts_n += re.split('([\s=;{}\(\),><\+\-\*/\?\\n])', token)

        texts_n = [text for text in texts_n if text]
        return texts_n

    def remove_comment(self) -> str:
        """

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
            elif char == '/' and quote is False:
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

    def get_lib_path(self, filename):
        for dir in self.lib_paths:
            if filename in os.listdir(dir):
                return dir + filename
        raise Exception('{} not found'.format(filename))

    def preprocess(self) -> str:
        """
        Description: This function preprocess given code stored in class attribute self.text
        :return: preprocessed text
        """
        self.text = self.text.replace('\\\n', '')
        self.text = self.remove_comment()

        texts = deque(self.tokenize())

        new_text = deque()

        while texts:
            text = texts.popleft()

            # preprocessor directives
            if self.__is_preprocessor_directive(text):
                type = self.__check_directive_type(text)

                if type == 'MACROS':
                    textl = re.split(' ', text)
                    try:
                        self.macros[textl[1]] = textl[2]
                    except IndexError:
                        self.macros[textl[1]] = None

                elif type == 'UNDEF':
                    textl = re.split(' ', text)
                    if textl[1] in self.macros.keys():
                        del (self.macros[textl[1]])
                    elif textl[1] in self.func.keys():
                        del (self.func[textl[1]])
                    else:
                        raise Exception('keyword {} not defined'.format(textl[1]))

                elif type in ('FILEINCL', 'STDLIB'):
                    if type == 'FILEINCL':
                        search = re.search('["\'].+["\']', text)
                        filename = text[search.start() + 1:search.end() - 1]
                        nfile = Preprocessor.read_file(filename)
                    else:
                        search = re.search('<\S*>', text)
                        filename = text[search.start() + 1:search.end() - 1]
                        nfile = Preprocessor.read_file(self.get_lib_path(filename))
                    log.debug('loading:' + filename)
                    processed_newfile = Preprocessor(nfile, self.lib_paths)

                    processed_newtext = processed_newfile.preprocess()
                    self.macros = {**self.macros, **processed_newfile.macros}
                    self.func = {**self.func, **processed_newfile.func}
                    log.debug('exiting:' + filename)
                    new_text.appendleft(processed_newtext)

                elif type == 'FUNC':

                    textl = re.split(' ', text)
                    fmacro = functional_Macro(textl[1], textl[2])
                    key = fmacro.name
                    self.func[textl[1][:textl[1].index('(')]] = fmacro

                elif type in ('IF', 'ELIF', 'IFDEF', 'IFNDEF'):
                    text = text[1:]
                    if type == 'IF' or (type == 'ELIF' and condition is True):
                        condition = self.eval_if_condition(text)
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

                    block = ['', '']  # if and else block
                    cur_block = 0
                    count = 0
                    while not (count == 1):
                        block[cur_block] += texts.popleft()
                        if not texts:
                            break
                        if self.__is_preprocessor_directive(texts[0]):
                            if self.__check_directive_type(texts[0]) in ("IF", "IFDEF", "IFNDEF"):
                                count -= 1
                            elif self.__check_directive_type(texts[0]) in ("ENDIF", "ELIF"):
                                count += 1
                            elif self.__check_directive_type(texts[0]) == "ELSE" and count == 0:
                                cur_block = 1


                    if condition:
                        preprocessor_obj = Preprocessor(block[0], self.lib_paths)
                        preprocessor_obj.macros, preprocessor_obj.func = (self.macros, self.func)
                        new_text.append(preprocessor_obj.preprocess())
                        self.macros, self.func = (preprocessor_obj.macros, preprocessor_obj.func)
                    else:

                        preprocessor_obj = Preprocessor(block[1], self.lib_paths)
                        preprocessor_obj.macros, preprocessor_obj.func = (self.macros, self.func)
                        new_text.append(preprocessor_obj.preprocess())
                        self.macros, self.func = (preprocessor_obj.macros, preprocessor_obj.func)
                elif type is 'ENDIF':
                    continue
                else:
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
        new_text = [textt for textt in new_text if textt]
        return ''.join(list(new_text))

    def eval_if_condition(self, text) -> bool:

        """

        :param text: condition statement
        :return: True or False after evaluating the condition
        """
        def_statements = re.findall('defined\s*\S*', text)

        sub = {"||": " or ", "&&": " and ", "!": " not "}

        for cond in def_statements:
            keyword = re.findall('[\s\(][\w_]+', cond)[0][1:]



            if keyword in self.macros.keys() or keyword in self.func.keys():
                sub[cond] = 'True'
            else:
                sub[cond] = 'False'

        for key in sub.keys():
            text = text.replace(key, sub[key])
        for key in self.macros.keys():

            if self.macros[key]:
                text = text.replace(key, self.macros[key])
        try:
            return eval(text[2:])
        except SyntaxError:
            return eval(text[2:-1])


    def replace_func_macros(self, text) -> str:
        """

        :param text:
        :return: It replaces the functional macros with the function expression.
        """
        fmacros: functional_Macro = self.check_func_macros(text)
        if fmacros:
            params = functional_Macro.getparams(text)
            params = [self.replace_func_macros(param) for param in params]
            return fmacros.replace_macro(params)

        return text

    def check_func_macros(self, text):
        """

        :param text:
        :return: Check whether functional macros is present in text If present return the name or else False
        """

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
        if text[0] == '#':
            return True
        return False

    @staticmethod
    def __check_directive_type(text) -> str:
        """

        :param text:
        :return: returns the type of preprocessor directive present in text.
        """

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
        if texts[0] == '#ifndef':
            return 'IFNDEF'


if __name__ == "__main__":
    for dir in res.cpp_directories:
        print(dir)

    input_file, output_file = (res.input, res.output)

    file = open(input_file, 'r')

    content = file.read()

    Preprocessor_obj = Preprocessor(content, res.cpp_directories)
    res = Preprocessor_obj.preprocess()

    write_file = open(output_file, 'w')
    write_file.write(res)
    write_file.close()
    print(os.path.realpath(__file__))
