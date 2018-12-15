import numpy as np
from itertools import groupby
import sys
import os.path
import struct
from bitarray import bitarray

class EncodingRules:
    def __init__(self, treeBits, symbols):
        #pvz jei yra 11110a0b11....., tai treeBits - bitukai; symbols - a,b
        self.treeBits = treeBits
        self.symbols = symbols
    def getTreeBits(self):
        return self.treeBits
    def getLetters(self):
        return self.symbols
class EncodedData:
    def __init__(self, encodedWord, suffixBits):
        self.encodedWord = encodedWord
        self.suffixBits = suffixBits
    def getEncodedWord(self):
        return self.encodedWord
    def getSuffixBits(self):
        return self.suffixBits
class Node:
    def __init__(self, letter):
        self.letter = letter
        self.leftChild = None
        self.rightChild = None
        
    def addLeftChild(self, child):
        self.leftChild = child
        
    def addLeftChild(self, child):
        self.rightChild = child
        
    def getLetter(self):
        return self.letter
        
    def setLetter(self, letter):
        self.letter = letter
        
class Coder:
    def __init__(self, word, codeWordLength):
        self.word = bitarray()
        self.word.frombytes(word)
        #print(self.word)
        self.codeWordLength = codeWordLength
        #Bitai kurie nebeiejo i raide. Pvz:. jei k = 4 ir turim žodį: 010110, tai 0101 bus viena raidė, o galune 10 nebesudarys raides
        self.suffixBits = bitarray()
        self.suffixBits, self.word = self.__getSuffixBits()
        #print(self.suffixBits)
        self.lettersDictionary = self.__getLettersDictionary()
    def __getSuffixBits(self):
        suffixBitsLength = len(self.word) % self.codeWordLength
        if suffixBitsLength == 0:
            return bitarray(), self.word
        #print(suffixBitsLength)
        suffixBits = self.word[len(self.word) - suffixBitsLength:len(self.word)]
        return suffixBits, self.word[:len(self.word)-suffixBitsLength]
    def getEncodingRules(self):
        rootNode = self.__createTree()
        treeStr = self.__getEncodingDecodingRules(rootNode)
        #print(treeStr)
        treeBits, letters = self.__separateTreeBitsAndLetters(treeStr)
        encodingRules = EncodingRules(treeBits, letters)
        return encodingRules
    #pvz jei yra 11110a0b11....., tai treeBits - bitukai; symbols - a,b
    def __separateTreeBitsAndLetters(self, treeStr):
        bits = []
        letters = []
        for element in treeStr:
            if isinstance(element, bool):
                bits.append(element)
            else:
                letters.append(element)
        return bitarray(bits), letters
    #Gaunam taisykles. Pvz:. 1110a110b... -> a dekoduojama i 0001, b i 
    def __getEncodingDecodingRules(self, node):
        str = []
        if node.getLetter() == '':
            str.append(True)
        else:
            str.append(False)
            str.append(node.getLetter())
        if node.leftChild is not None:
            str.extend(self.__getEncodingDecodingRules(node.leftChild))
        if node.rightChild is not None:
            str.extend(self.__getEncodingDecodingRules(node.rightChild))
        return str
    
    def __createTree(self):
        rootNode = Node('')
        uniqueCharsRepresentedInBits = self.__getUniqueLettersInWord()
        for letter in uniqueCharsRepresentedInBits:
            rootNode = self.__updateTree(rootNode, letter)
        return rootNode
        
    def __updateTree(self, node, letter):
        #letter[0], kadangi letter butu [raide, daznis]
        encodedLetter = self.lettersDictionary[letter[0]]
        currentNode = node
        for i in range(0, len(encodedLetter)):
            bit = encodedLetter[i]
            if bit == 0:
                if currentNode.leftChild == None:
                    currentNode.leftChild = Node('')
                currentNode = currentNode.leftChild
            elif bit == 1:
                if currentNode.rightChild == None:
                    currentNode.rightChild = Node('')
                currentNode = currentNode.rightChild
        currentNode.setLetter(letter[0])
        return node
        
    def getEncodedData(self):
        encodedWord = bitarray()
        i = 0
        while i < len(self.word):
            currentLetter = self.word[i:i+self.codeWordLength]
            encodedLetter = self.__getEncodedLetter(currentLetter.to01())
            encodedWord.extend(encodedLetter)
            i += len(currentLetter)
        #print(self.suffixBits)
        return EncodedData(encodedWord, self.suffixBits)
    
    def __getEncodedLetter(self, letter):
        return self.lettersDictionary[letter]
    
    #Gaunam žodyna koki simboli i koki uzkoduoti. Tai diction[a] - gaunam kaip uzkoduotas a
    def __getLettersDictionary(self):
        uniqueSymbols = self.__getUniqueLettersInWord()
        #print(uniqueSymbols)
        symbolsList = self.__splitListOfSymbolsToListOfSymbolsList(uniqueSymbols)
        diction = self.__createDictionaryForSymbols(symbolsList, "", {})
        #print("dict dydis")
        #print(len(diction))
        return diction
    #Jei turim lista [a,b,c,d], tai verciam i [[a],[b],[c],[d]]
    def __splitListOfSymbolsToListOfSymbolsList(self, uniqueSymbols):
        list = []
        for element in uniqueSymbols:
            newList = []
            newList.append(element)
            list.append(newList)
        return list
    
    #gaunam dictionary raidems
    def __createDictionaryForSymbols(self, symbolsList, currentSeq, diction):
        #print(len(symbolsList))
        if(len(symbolsList) == 1):
            diction[((symbolsList[0])[0])[0]] = bitarray(currentSeq)
            #print("key: %s, value: %s" % (((symbolsList[0])[0])[0], currentSeq))
            return diction
        while len(symbolsList) != 2:
            #2 mažiausius bucketus apjungiam i viena bucketa. Jei turim [[a],[b],[c],[d]] verciam i [[a], [b], [c,d]]
            #print(len(symbolsList))
            symbolsList = self.__merge2LeastBucketsIntoOne(symbolsList)
            #print(len(symbolsList))
            #print(len(symbolsList))
        #Po loopo gaunam lista kuriame yra du itemai, pvz [[a, c, h, ...], [b, d, e, ...]]
        symbolsList = self.__sortDescending(symbolsList)
        leftList = self.__splitListOfSymbolsToListOfSymbolsList(symbolsList[0])
        currentSeq = currentSeq + "0"
        diction = self.__createDictionaryForSymbols(leftList, currentSeq, diction)
        currentSeq = currentSeq[:len(currentSeq)-1]
        
        rightList = self.__splitListOfSymbolsToListOfSymbolsList(symbolsList[1])
        currentSeq = currentSeq + "1"
        diction = self.__createDictionaryForSymbols(rightList, currentSeq, diction)
        
        return diction
        
    def __merge2LeastBucketsIntoOne(self, symbolsList):
        symbolsList = self.__sortDescending(symbolsList)
        least = symbolsList[-1]
        secLeast = symbolsList[-2]
        least.extend(secLeast)
        symbolsList.pop()
        symbolsList.pop()
        symbolsList.append(least)
        
        return symbolsList
        
    def __sortDescending(self, symbolsList):
        #print(symbolsList)
        for i in range(0, len(symbolsList)-1):
            for j in range(i+1, len(symbolsList)):
                #print("%d is %d" % (i, j))
                value1 = self.__calculateTotalValueOfBucket(symbolsList[i])
                #print(value1)
                value2 = self.__calculateTotalValueOfBucket(symbolsList[j])
                #print(value2)
                if(value2 > value1):
                    temp = symbolsList[i]
                    symbolsList[i] = symbolsList[j]
                    symbolsList[j] = temp
                    i -= 1
        return symbolsList
    
    def __calculateTotalValueOfBucket(self, bucket):
        totalValue = 0
        for item in bucket:
            totalValue = totalValue + item[1]
        return totalValue

    #Gaunam lista unikaliu raidziu ir ju daznius [['00001', 1534], [...], ...]
    def __getUniqueLettersInWord(self):
        i = 0
        length = len(self.word)
        dict = {}
        while i < length:
            letter = self.word[i:i+self.codeWordLength]
            if letter.to01() in dict:
                dict[letter.to01()] += 1
            else:
                dict[letter.to01()] = 0
            i += len(letter)
        dictList = []
        for key, value in dict.items():
            dictList.append([key, value])
        return dictList

class CodeWriter:
    def __init__(self, encodingRules, encodedData):
        self.encodingRules = encodingRules
        self.encodedData = encodedData
    def writeToFile(self, fileName):
        #Rasom: 3 bitai pasako kiek uzkoduotam zodyje yra nereikalingu bituku, tam kad uzkoduotas zodis tilptu i pilna baita. + 5 bitai pasako kiek bitu liko neuzkoduotu
        #Gaunam kiek bitu nuskaityti neuzkoduotai galunei
        #Rasom neuzkoduota galune
        #Rasom kiek baitu skirta kodavimo/dekodavimo taisykliu medziui
        #Rasom medi
        #Rasom viska iki galo - uzkoduota zodi
        encodedWord = self.encodedData.getEncodedWord()
        suffixBits = self.encodedData.getSuffixBits()
        letterLength = len(self.encodingRules.getLetters()[0])
        trashAndSuffixBitsLengthByte = self.__getTrashAndSuffixBitsLengthByte(len(encodedWord), len(suffixBits))
        letterLengthByte = self.__int_to_bytes(letterLength)
        suffixBitsBytes = self.__getBytesFromNonFullBits(suffixBits)
        encodedWordInBytes = self.__getEncodedWordInBytes(encodedWord)
        treeRulesBytes = self.__getBytesFromNonFullBits(self.encodingRules.getTreeBits())
        letters = self.encodingRules.getLetters()
        letters = self.__convertLettersToBitsArray(letters)
        lettersBytes = self.__getBytesFromNonFullBits(letters)
        treeRequiredBytes = len(treeRulesBytes)
        treeRequiredBytesByte = self.__int_to_bytes(treeRequiredBytes)   
        
        
        f = open(fileName, 'wb')
        f.write(trashAndSuffixBitsLengthByte)
        f.write(letterLengthByte)
        f.write(suffixBitsBytes)
        f.write(treeRequiredBytesByte)
        f.write(treeRulesBytes)
        f.write(lettersBytes)
        f.write(encodedWordInBytes)
        f.close()
    def __convertLettersToBitsArray(self, letters):
        bits = bitarray()
        for letter in letters:
            #print(letter)
            bits.extend(letter)
        return bits
    def __getTrashAndSuffixBitsLengthByte(self, encodedWordLength, suffixBitsLength):
        if encodedWordLength % 8 == 0:
            value1 = 0
        else:
            value1 = (8 - (encodedWordLength % 8)) << 5
        return self.__int_to_bytes(value1 + suffixBitsLength)
    #Gaunam baitus, is bitu sekos kurios liekana != 0 (uzpildom vienetukais gala)
    def __getBytesFromNonFullBits(self, bits):
        #Gaunam kiek bitu reikia kad uzpildytume baita
        bitsToAdd = self.__bitsToGetFullByte(len(bits))
        #Prijungiam bitukas, kad gautume pilna baita
        bits.extend(self.__addBitsToCompleteByte(bitsToAdd))
        #Verciam i baitus
        return bits.tobytes()
    
    def __addBitsToCompleteByte(self, bitsToAdd):
        bits = []
        for i in range(0, bitsToAdd):
            bits.append(True)
        return bits
        
    def __getEncodedWordInBytes(self, bitArray):
        bitsToAdd = self.__bitsToGetFullByte(len(bitArray))
        bitArray.extend(self.__appendBits(bitsToAdd))
        bytes = bitArray.tobytes()
        return bytes
    
    def __appendBits(self, bitsToAdd):
        extraBits = bitarray()
        for i in range(0, bitsToAdd):
            extraBits.append(True)
        return extraBits
    
    def __bitsToGetFullByte(self, bits):
        if bits % 8 == 0:
            return 0
        else:
            return (int(bits / 8) + 1) * 8 - bits
    def __int_to_bytes(self, x):
        if x == 0:
            b = bitarray(8)
            b.setall(False)
            return b.tobytes()
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')    

#text1 = input('Uzkoduoto simbolio ilgis bitais: ')
'''
try:
    codedSymbolInBitsLength = int(text1)
except ValueError:
    print("Ivestas ne skaicius")
    sys.exit(2)
    
if codedSymbolInBitsLength < 2 or codedSymbolInBitsLength > 24:
    print("Skaicius turi buti tarp 2 ir 24")
    sys.exit(3)
'''
#Nustatom kiek bitu traktuosim kad yra raides ilgis
codedSymbolInBitsLength = 8
#Nuskaitom norima uzkoduoti faila
f = open(r"C:\Users\Dovydas\infoTeorija\tests\fileToRead.txt", 'rb')
allBytes = f.read()
#Nuskaitom faila i kuri uzkoduosim 
text3 =  r"C:\Users\Dovydas\infoTeorija\tests\encodedFile.txt"

coder = Coder(allBytes, codedSymbolInBitsLength)
encodedData = coder.getEncodedData()
encodingRules = coder.getEncodingRules()
codeWriter = CodeWriter(encodingRules, encodedData)
codeWriter.writeToFile(text3)