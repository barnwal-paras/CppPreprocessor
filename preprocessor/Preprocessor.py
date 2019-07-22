import datetime
import getopt
import logging
import re
import sys
from collections import deque


logging.basicConfig()
log = logging.getLogger(__name__)
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)


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
        __libpath   path of cplusplus header files
    """

    separator = '\n\n'
    __libpath = None

    def __init__(self, text: str):

        self.text = text
        self.func = {}
        self.macros = {}
        self.__add_predefined_macros()
        if not Preprocessor.__libpath:
            with open('config.txt', 'r') as conf_file:
                Preprocessor.__libpath = conf_file.read()

    def __add_predefined_macros(self):
        predefined_macro = dict()
        predefined_macro['__DATE__'] = '{} {} {}'.format(datetime.datetime.now().month, datetime.datetime.now().day,
                                                         datetime.datetime.now().year)
        predefined_macro['__TIME__'] = '{}:{}:{}'.format(datetime.datetime.now().hour, datetime.datetime.now().minute,
                                                         datetime.datetime.now().second)
        predefined_macro['__STDC__'] = "1"
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
                    del (self.macros[textl[1]])

                elif type in ('FILEINCL', 'STDLIB'):
                    if type == 'FILEINCL':
                        search = re.search('["\'].+["\']', text)
                        filename = text[search.start() + 1:search.end() - 1]
                        nfile = Preprocessor.read_file(filename)
                    else:
                        search = re.search('<\S*>', text)
                        filename = text[search.start() + 1:search.end() - 1]
                        nfile = Preprocessor.read_file(Preprocessor.__libpath + filename)
                    log.debug('loading:' + filename)
                    processed_newfile = Preprocessor(nfile)

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
                        preprocessor_obj = Preprocessor(block[0])
                        preprocessor_obj.macros = self.macros
                        preprocessor_obj.func = self.func
                        new_text.append(preprocessor_obj.preprocess())
                        self.macros = preprocessor_obj.macros
                        self.func = preprocessor_obj.func
                    else:

                        preprocessor_obj = Preprocessor(block[1])
                        preprocessor_obj.macros = self.macros
                        preprocessor_obj.func = self.func
                        new_text.append(preprocessor_obj.preprocess())
                        self.macros = preprocessor_obj.macros
                        self.func = preprocessor_obj.func
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

        return eval(text[2:])

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


def main(argv):
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
    input_file, output_file = main(sys.argv[1:])

    file = open(input_file, 'r')

    content = file.read()

    Preprocessor_obj = Preprocessor(content)
    res = Preprocessor_obj.preprocess()

    write_file = open(output_file, 'w')
    write_file.write(res)
    write_file.close()