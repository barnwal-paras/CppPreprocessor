import re

import io
import sys

class Preprocessor:

    separator='\n'
    __libpath=None



    def __init__(self,text):
        self.text=text

        if(not Preprocessor.__libpath):
            if(sys.platform=='darwin'):
                Preprocessor.__libpath='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/include/c++/v1/'
            elif(sys.platform=='win32'):
                Preprocessor.__libpath="C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community\\VC\\Tools\\MSVC\\14.21.27702\\include\\"
            else:
                raise Exception('{} systems are not supported yet'.format(sys.platform))





    @staticmethod
    def read_file(filename,lib=False):
        if(not lib):
            return open(filename,'r').read()
        else:
            return open(Preprocessor.__libpath+filename,'r').read()

    
    
    @classmethod
    def changeSeparator(separator):
        Preprocessor.separator=separator



    def tokenize(self):
        return re.split('( )|(".*")|(=)|'
                        '(;)|(<)|(>)|({)|(})|([)|(])'
                        '|(,)|(>>)|(<<)|(\n)|(<.*>)', self.text)



    def preprocess(self):
        self.text = re.sub("//.*\n", " \n", self.text)
        texts=re.split('(".*")|(\'.*\')|(/\*.*/\*)',self.text)
        for i in range(len(texts)):
            if(re.search('^/\*.*\*/$',str(texts[i]))):
                texts[i]=''
            if not texts[i]:
                texts[i]=''
        self.text=''.join(texts)



        self.text = re.sub("//*(.|\n)*//*", "\n", self.text)

        texts = self.tokenize()
        texts = self.checkheader(texts)
        texts = Preprocessor.checkmacros(texts)
        return ''.join(texts)




    def checkheader(self,texts):
        for i in range(len(texts)):
            if (texts[i] == '#include'):
                index = []
                index.append(i)
                i += 1
                while (texts[i] not in ('"', "<", "'")):
                    index.append(i)
                    i += 1

                index.append(i)

                i += 1
                while (not texts[i]):
                    i += 1
                if(texts[index[-1]]=='<'):
                    headfile = Preprocessor(Preprocessor.read_file(texts[i],True))
                    Preprocessor.count+=1
                elif(texts[index[-1]]=='"' or texts[index[-1]]=='\''):
                    headfile=Preprocessor(Preprocessor.read_file(texts[i]))
                else:
                    raise Exception("error in line"+texts[i])
                texts[i] =headfile.preprocess()

                i += 1
                for k in index:
                    texts[k] = None
                while (not texts[i]):
                    i += 1
                texts[i] = Preprocessor.separator

        return texts




    @staticmethod
    def checkmacros(texts):
        macros = {}
        libfile=False
        for i in range(len(texts)):
            # check macros
            if (texts[i] == '#define'):
                '''index = []
                index.append(i)'''
                texts[i]=None
                i += 1

                while (texts[i] in (None, ' ')):
                    texts[i]=None
                    i += 1

                key = texts[i]
                texts[i]=None

                i += 1
                while (texts[i] in (None, ' ')):
                    i += 1
                index.append(i)
                value = texts[i]
                for p in index:
                    texts[p] = None
                macros[key] = value
            # check if macros matches
            elif (texts[i] in macros.keys()):
                texts[i] = macros[texts[i]]
            # check if undef is there

            elif (texts[i] == '#undef'):
                index = []
                index.append(i)
                i += 1
                while (texts[i] in (None, ' ')):
                    i += 1
                key = texts[i]
                index.append(i)
                for k in index:
                    texts[k] = None
                del macros[key]

        texts = [i for i in texts if i]

        return texts



if (__name__=="__main__"):
    file=open('test.cpp','r')
    text=file.read()
    preprcs=Preprocessor(text)
    res=preprcs.preprocess()
    print(res)

