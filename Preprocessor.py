import re

from collections import deque


class funcMacro:

    def __init__(self, declaration, expression):

        split_string = re.split('(\(.*\))', text)
        self.name = split_string[0]
        self.parameters = split_string[1][1:-1].split(',')
        tokens = funcMacro.tokenize_text(expression)
        for i in range(len(tokens)):
            if (tokens[i] in self.parameters):
                tokens[i] = '{' + str(self.parameters.index(tokens[i])) + '}'
        self.expression = ''.join(tokens)

    @staticmethod
    def tokenize_text(text):
        texts = deque(re.split('(\\n)', text))
        texts_n = []

        while (texts):
            token = texts.popleft()
            if token and token[0] == '#':
                texts_n += [token]
                texts_n += ['\n']
            else:
                texts_n += re.split('( )|(=)|'
                                    '(;)|({)|(})|([)|(])'
                                    '|(,)|(>>)|(<<)|(\n)|(<)|(>)', token)

        texts_n = [text for entry in texts_n if entry]
        return texts_n


class Preprocessor:
    separator = '\n\n'
    __libpath = None

    def __init__(self, text):
        self.text = text
        if not Preprocessor.__libpath:
            with open('config.txt', 'r') as conf_file:
                Preprocessor.__libpath = conf_file.read()

    @staticmethod
    def read_file(filename):
        with open(filename, 'r') as cfile:
            return cfile.read()

    def tokenize(self):
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

    def removeComment(self):
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

        '''
        self.text = re.sub("//.*\n", " \n", self.text)
        texts = re.split('(".*")|(\'.*\')|(/\*(.|\\n)*\*/)', self.text, flags=re.DOTALL)

        for i in range(len(texts)):
            if (re.match('^/\*.*\*/$', str(texts[i]), flags=re.DOTALL)):
                texts[i] = ''

            if not texts[i]:
                texts[i] = ''
        self.text = ''.join(texts)
        return self.text
        
        '''

    def preprocess(self):

        self.text = self.removeComment()

        texts = deque(self.tokenize())
        macros = {}
        newtext = deque()
        func = {}

        while (texts):
            text = texts.popleft()

            # preprocessor directives
            if (self.__isPreprocessorDirective(text)):
                type = self.__checkDirType(text)

                if (type == 'MACROS'):
                    textl = re.split(' ', text)
                    macros[textl[1]] = textl[2]

                elif (type == 'UNDEF'):
                    textl = re.split(' ', text)
                    del (macros[textl[1]])

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
                    func[key] = funcMacro

            else:
                if (text in macros.keys()):
                    text = macros[text]
                newtext.append(text)

                '''
                elif(text in func.keys()):
                    next=texts.popleft()
                    if(next=='('):
                        count=1
                        while(count):
                            n_next=texts.popleft()
                            if(n_next=='('):
                                count+=1


                    else:
                        texts.appendleft(next)
                        

                '''

        return ''.join(list(newtext))

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
