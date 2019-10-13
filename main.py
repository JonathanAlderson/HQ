[print("\n") for i in range(80)]
import urllib
from bs4 import BeautifulSoup
import requests
import webbrowser
import time
from PIL import ImageGrab
from PIL import Image
import time
import datetime
import os
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import time
import itertools
from string import punctuation
import re
from threading  import Thread
start = time.time()

question = "Who is the president of the USA?"
a = ["Obama","Bush","Trump"]


####
# taking screenShot
####


takeScreenshot = True
debug = True
if(takeScreenshot):

    pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract'


    # take screenShot
    img = ImageGrab.grab(bbox=((1920*0.5)-250,(1080*0.2),(1920*0.5)+250,(1080*0.65)))
    img.save("question.png")

    # do image processing and text finding
    image_file = Image.open("question.png") # open colour image
    gray = image_file.convert('L')
    bw = gray.point(lambda x: 0 if x<200 else 255, '1')
    bw.save("result_bw.png")
    bw.save('ppQuestion.png')
    print("\n\n\n\n")
    text = pytesseract.image_to_string(Image.open("ppQuestion.png"))
    text = text.split("\n\n")

    text[0] = text[0].replace("\n"," ")

    text[0] = text[0].replace("\\","")


    text = list(itertools.chain.from_iterable([ i.split("\n") for i in text]))

    if(len(text) > 4):
        question = (" ").join(text[:-3])
    else:
        question = text[0]
    #print("\n\n\n\nQuestion\n\n\n")
    #print(len(question))
    #print(question)
    # splits up a based on newlines
    a = text[1:]

    a = list(itertools.chain.from_iterable([ i.split("\n") for i in a]))

    if(len(a) > 3):
        a = a[-3:]

possibleAnswers = []


for word in a:
    possibleAnswers.append(word.split(" "))
correctAnswer = [0,0,0] # stores an array of how confident it is on each answer



if(debug):
    print("\n\nQuesion: ",question,"\nAnswers: ",possibleAnswers)



def googleThis(query,pageNumber):
    text = query
    text = urllib.parse.quote_plus(text)

    url = 'https://google.com/search?q=' + text + '&start=' + str(10*pageNumber)
    #headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
    response = requests.get(url)

    results = "" # empty string
    soup = BeautifulSoup(response.text, 'lxml')
    for g in soup.find_all(class_='g'):
        results = results + " " + (g.text)

    results = results.split(" ")
    return results

def allCombos(word):
   alphabet    = 'abcdefghijklmnopqrstuvwxyz'
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
   inserts    = [a + c + b     for a, b in splits for c in alphabet]
   return ([deletes,transposes,replaces,inserts])


def percentageChance(a,b,time,invert):
    sum = a[0] + a[1] + a[2]
    if(sum == 0):
        print("\n\nAnswers",a,"\n------------------\nnone\nnone\nnone")
        return
    if(invert):
        print("\n\nAnswers found in " +str(round(time,2))+" " + str(a) +  "\n------------------\n"
                + b[0] + " " + str(100 - round(((a[0]/sum)*100),2)) + "%\n"
                + b[1] + " " + str(100 - round(((a[1]/sum)*100),2)) + "%\n"
                + b[2] + " " + str(100 - round(((a[2]/sum)*100),2)) + "%\n------------------")
    else:
        print("\n\nAnswers found in " +str(round(time,2))+" " + str(a) + "\n------------------\n"
                + b[0] + " " + str(round(((a[0]/sum)*100),2)) + "%\n"
                + b[1] + " " + str(round(((a[1]/sum)*100),2)) + "%\n"
                + b[2] + " " + str(round(((a[2]/sum)*100),2)) + "%\n------------------")


def directMatches(results,possibleAnswers,correctAnswer):

    for word in results:
        for i in range(len(possibleAnswers)):
            for j in range(len(possibleAnswers[i])):
                if(possibleAnswers[i][j].lower() == word.lower()):
                    correctAnswer[i]+=1

                    if(word.lower() in similarWordsList or word.lower() == "the" or word.lower() == "a"):

                        correctAnswer[i]-=1
                    #print("Direct Match: ",i," = ",word,possibleAnswers[i][j]) # match
    return(correctAnswer)


def reversedMatches(results,question):

    matches = 0
    for word in results:
        if(word.lower() in question):
            matches+=1


    return(matches)



def wikipediaMatches(article,question):
    numberOfMatches = 0
    for word in article.split(" "):
        if(word.lower() in question.lower().split(" ")):
            print("\t"+word.lower() + " matched")
            numberOfMatches+=1
    return(numberOfMatches)


def indirectMatches(results,possibleAnswers,correctAnswer):
    for word in results:
        allVersionsOfWord = allCombos(word)
        for i in range(3):
            for j in range(4):
                for mangledWord in (allVersionsOfWord[j]):
                    for k in range(len(possibleAnswers[i])):
                        if(possibleAnswers[i][k] in mangledWord):
                            correctAnswer[i]+=0.01
    return(correctAnswer)


def removePunctuation(a):
    b = []
    for word in a.split(" "):
        b.append(re.sub(r'[^\w\s]','',word))
    return b



def removeCommonWords(query):
    updatedAnswer = []
    query = query.split(" ")
    textFile = open("commonWords.txt","r").read().split("\n")
    for word in query:

        flag = False
        for line in textFile:
            if(line.lower() == word.lower()):
                flag = True
                break
        if(flag == False):
            updatedAnswer.append(word)
    return((" ").join(updatedAnswer))


def removeSimilarWords(possibleAnswers):
    # look at every word compared to every other word. If they
    # are the same or similar, remove them
    # a = [[1,2],[1,4],[6,1]]
    newPossibleAnswers = [[],[],[]]
    for i in range(3):
        for j in range(len(possibleAnswers[i])):

            flag = True
            for k in range(3):
                for m in range(len(possibleAnswers[k])):
                    if(not (i == k and j == m)):
                        if(possibleAnswers[i][j] in possibleAnswers[k][m] or possibleAnswers[k][m] in possibleAnswers[i][j]):
                            flag = False
                            break

            if(flag == True):
                newPossibleAnswers[i].append(possibleAnswers[i][j])
    return(newPossibleAnswers)

def removeSimilarWords(possibleAnswers):
    similarWordsThatDontCount = []
    for i in range(3):
        for j in range(len(possibleAnswers[i])):

            flag = True
            if(possibleAnswers[i][j] in possibleAnswers[(i+1)%3] and possibleAnswers[i][j] in possibleAnswers[(i+2)%3]):
                flag = False



            if(flag == False):
                similarWordsThatDontCount.append(possibleAnswers[i][j])
    return(similarWordsThatDontCount)


def wikipediaIt(thing):

    try:
        text = thing
        text = urllib.parse.quote_plus(text)

        url = 'https://en.wikipedia.org/wiki/' + text
        #headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
        response = requests.get(url)

        results = "" # empty string
        soup = BeautifulSoup(response.text, 'lxml')
        main_tag = soup.findAll('div',{'id':'mw-content-text'})[0]

        headers = main_tag.find_all('h3')
        ui_list = main_tag.find_all('ul')
        for i in range(len(headers)):
            results = results + (headers[i].span.get_text())
            results = results + ('\n -'.join(ui_list[i].get_text().split('\n')))
        return(results)
    except IndexError:
        return("")




#Notes, when there is a 'not' in the question, pick the lowest scoring nAnswers
#      when there is things like 'Mr ___' 'Mr ____' and 'Mr ____' answer will look similar


doInvert = False


pageNumber = 0

results = googleThis(question,pageNumber)

similarWordsList = (removeSimilarWords(possibleAnswers))
correctAnswer = directMatches(results,possibleAnswers,correctAnswer)
percentageChance(correctAnswer,a,time.time()-start,doInvert)
correctAnswer = indirectMatches(results,possibleAnswers,correctAnswer)
percentageChance(correctAnswer,a,time.time()-start,doInvert)

question = removeCommonWords(question)
results = googleThis(question,pageNumber)
correctAnswer = directMatches(results,possibleAnswers,correctAnswer)
percentageChance(correctAnswer,a,time.time()-start,doInvert)
correctAnswer = indirectMatches(results,possibleAnswers,correctAnswer)
percentageChance(correctAnswer,a,time.time()-start,doInvert)

def doReveredAnswers():
    printout = ("\n\nReverse\n")
    for answer in possibleAnswers:
        printout = printout + str(answer)
        printout = printout + " got "
        printout = printout + str(reversedMatches(googleThis(" ".join(answer),pageNumber),removePunctuation(removeCommonWords(question))))
        printout = printout +" matches\n"
        #printout = printout + (answer, "got ",reversedMatches(googleThis(" ".join(answer),pageNumber),removePunctuation(removeCommonWords(question)))," matches\n")
    print(printout + "\n\n")

def doWikipediaAnswers():
    printout = ("\n\nWikipedia\n")
    for answer in possibleAnswers:
        printout = printout + str(answer)
        printout = printout + " got "
        printout = printout + str(wikipediaMatches(wikipediaIt(("_").join(answer)),removeCommonWords(question)))
        printout = printout +  " matches\n"

        #printout = printout + (answer," got ",wikipediaMatches(wikipediaIt(("_").join(answer)),removeCommonWords(question))," matches\n")
    print(printout + "\n\n")

Thread(target = doReveredAnswers).start()
Thread(target = doWikipediaAnswers).start()
