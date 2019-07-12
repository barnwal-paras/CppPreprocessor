import logging
import re
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
        split_string = re.split('(\(.*\))', declaration)
        self.name = text[:text.index('(')]

        self.params = funcMacro.getparams(declaration)

        tokens = Preprocessor(expression).tokenize()

        log.debug(expression)
        for i in range(len(tokens)):
            if (tokens[i] in self.params):
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

        while (len(paramtext)):

            if (paramtext[0] == '('):
                count += 1
                if (count > 1):
                    word += paramtext.popleft()
                else:
                    paramtext.popleft()
            elif (paramtext[0] == ')'):
                count -= 1
                if (count):
                    word += paramtext.popleft()
                else:
                    param += [word]
                    break
            elif (count == 1 and paramtext[0] == ','):
                paramtext.popleft()
                param += [word]
                word = ''
            else:
                word += paramtext.popleft()
        else:
            raise Exception("not a functional macro expression" + " " + text)
        return param

    def replacemacro(self, params):
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

        while (texts):
            token = texts.popleft()
            if token and token[0] == '#':
                texts_n += [token]
            else:
                texts_n += re.split('( )|(=)|'
                                    '(;)|({)|(})|([)|(])'
                                    '|(,)|(>>)|(<<)|(\\n)|(<)|(>)|'
                                    '(\+)|(-)|(\*)|(/)', token)

        texts_n = [text for text in texts_n if text]
        return texts_n

    def removeComment(self) -> list:
        """
        Description: remove comments from text
        :return: text without comments
        """
        text = deque(self.text)
        quote = False
        newtext = ''
        while (text):
            char = text.popleft()
            if (char == '"'):
                quote = not quote
                newtext += char
            elif (char == '\n'):
                quote = False
                newtext += char
            elif (char == '/' and quote == False):
                next = text.popleft()
                if (next == '/'):
                    while (text.popleft() != '\n'):
                        continue
                    else:
                        newtext += '\n'
                elif (next == '*'):

                    while (text.popleft() != '*' or text[0] != '/'):
                        continue
                    else:
                        text.popleft()
                else:
                    newtext += char
                    newtext += next
            else:
                newtext += char

        return newtext

    def preprocess(self) -> str:

        self.text = self.removeComment()

        texts = deque(self.tokenize())

        newtext = deque()


        while (texts):
            text = texts.popleft()

            # preprocessor directives
            if (self.__isPreprocessorDirective(text)):
                type = self.__checkDirType(text)

                if (type == 'MACROS'):
                    textl = re.split(' ', text)
                    self.macros[textl[1]] = textl[2]

                elif (type == 'UNDEF'):
                    textl = re.split(' ', text)
                    del (self.macros[textl[1]])

                elif (type in ('FILEINCL', 'STDLIB')):
                    search = re.search('(".*")|(\'.*\')', text)
                    filename = text[search.start() + 1:search.end() - 1]
                    if (type == 'FILEINCL'):
                        nfile = Preprocessor.read_file(filename)
                    else:
                        nfile = Preprocessor.read_file(Preprocessor.__libpath + filename)
                    processed_nfile = Preprocessor(nfile).preprocess()
                    newtext.appendleft(processed_nfile)

                elif (type == 'FUNC'):

                    textl = re.split(' ', text)

                    fmacro = funcMacro(textl[1], textl[2])
                    key = fmacro.name
                    self.func[textl[1][:textl[1].index('(')]] = fmacro


            else:
                if (text in self.macros.keys()):
                    text = self.macros[text]
                    newtext.append(text)



                elif (text in self.func.keys() and texts[0] == '('):
                    count = 1

                    next = texts.popleft()
                    while (texts):
                        if (texts[0] == '('):
                            count += 1
                        elif (texts[0] == ')'):
                            count -= 1
                        next += texts.popleft()
                        if (not count):
                            break
                    newtext.append(self.replacefuncmacros(text + next))
                else:
                    newtext.append(text)



                        


        return ''.join(list(newtext))

    def replacefuncmacros(self, text) -> str:

        fmacros = self.checkfuncmacros(text)
        if (fmacros):
            params = funcMacro.getparams(text)
            params = [self.replacefuncmacros(param) for param in params]
            return fmacros.replacemacro(params)

        return text

    def checkfuncmacros(self, text):

        if (re.match('^.+\(.+\)$', text) and text[:text.index('(')] in self.func.keys()):
            return self.func[text[:text.index('(')]]

        return False


    def __isPreprocessorDirective(self, text):
        """
        Description:
        :param text:
        :return:
        """
        if (text[0] == '#'):
            return True
        return False

    def __checkDirType(self, text):

        texts = re.split(' ', text)

        if (texts[0] == '#define'):
            if ('(' in texts[1]):
                return 'FUNC'
            return 'MACROS'

        if (texts[0] == '#undef'):
            return 'UNDEF'

        if (re.match('^#include( )*<.*>', text)):
            return 'STDLIB'

        if (re.match('^#include( )*(".*")|(\'.*\')', text)):
            return 'FILEINCL'


if (__name__ == "__main__"):
    file = open('test.cpp', 'r')

    text = file.read()

    preprcs = Preprocessor(text)
    res = preprcs.preprocess()
    print(res)
