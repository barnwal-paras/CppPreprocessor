import re
import tokenize
from cpp_tokenizer  import Tokenizer
import io
def initpreprocess(filename):
    file = open(filename, 'r')
    text = file.read()
    '''
    texts=re.split('"(.|\n)*"',text)
    texts=re.find

    for i in range(1,len(texts),2):
        texts[i]=texts[i].replace("//","<slsl>")
        texts[i]=texts[i].replace('/*',"<sls>")
        texts[i]=texts[i].replace('*/', "<ssl>")

    text='"'.join(texts)
    '''

    text= re.sub("//.*\n"," \n",text)
    text=re.sub("//*(.|\n)*//*","\n",text)
    #text=re.sub("/\/\n"," ",text)
    '''
    text=text.replace("<slsl>","//" )
    text=text.replace("<sls>",'/*' )
    text=text.replace("<ssl>",'*/')
    '''
   

tokenize.NUMBER
print(initpreprocess("test.cpp"))
