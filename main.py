from collections import deque


def initpreprocess(filename):
    file = open(filename, 'r')
    text = file.read()
    sentences = deque(text.split('\n'))
    newsent = []
    while (sentences):
        sent = sentences.popleft()
        try:
            if (sent[-1] == "\\" and sentences):
                sent = sent[:-1] + sentences.popleft()
        except IndexError:
            pass
        newsent.append(sent)

    sentences = commentchk(newsent)
    return sentences


def commentchk(sentences):
    sentences = deque(sentences)
    quote_num = 0
    cont_comment = False

    newsentences = []
    while (sentences):
        sentence = sentences.popleft()
        sentence = deque(sentence)
        newsentence = ''
        while sentence:
            char = sentence.popleft()
            if (cont_comment):
                if (char == "*" and sentence):
                    if (sentence.popleft() == '/'):
                        cont_comment = False
                        newsentence += ' '
            else:
                try:
                    if (char == '"'):
                        quote_num += 1
                        newsentence += char

                    elif (char == '/' and newsentence[-1] == '/'):
                        newsentence = newsentence[:-1]
                        break

                    elif (char == '*' and newsentence[-1] == '/'):
                        newsentence = newsentence[:-1]
                        cont_comment = True
                        newsentence += ' '
                    else:
                        newsentence += char
                except IndexError:
                    if (not cont_comment):
                        newsentence += char
                    pass

        newsentences.append(newsentence)
    return newsentences
for k in initpreprocess('test.cpp'):
    print(k)