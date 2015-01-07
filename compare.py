class NefComparison:

  def readNmrStarFile(self,fileName,printData=False):

    import ccp.format.nmrStar.bmrb.File as nmrStar

    origNmrStarFile = nmrStar.File(verbosity = 2, filename = fileName)

    #
    # Read star file
    #

    if origNmrStarFile.read():
      print "  Error reading nmrStar file %s" % self.name
      return False

    #
    # Go through the data in the file
    #

    if printData:
      for origSaveFrame in origNmrStarFile.datanodes:
      
        print origSaveFrame.title

        for tagtable in origSaveFrame.tagtables:

          for tagIndex in range(len(tagtable.tagnames)):

            tagName = tagtable.tagnames[tagIndex]
            tagValues = tagtable.tagvalues[tagIndex]

            print tagName, tagValues

    return origNmrStarFile

  def compareNefFiles(self,fileName1,fileName2):
  
    fileNames = (fileName1,fileName2)
  
    nefFiles = {}
    
    for fileName in fileNames:
  
      nefFiles[fileName] = self.readNmrStarFile(fileName) 
    
    missingSfs = []

    missingTagNames = []
    mismatchTagValues = []

    missingTagTables = []
    missingTagTableNames = []
    mismatchTagTableValues = []
    tagValuemismatches = []
   
    for fileName in fileNames:
      refNefFile = nefFiles[fileName]
      
      otherFileName = fileNames[not(fileNames.index(fileName))]
      otherNefFile = nefFiles[otherFileName]
      
      for datanode in refNefFile.datanodes:
        sfName = datanode.title
        sfFound = False
        for otherDataNode in otherNefFile.datanodes:
          if sfName == otherDataNode.title:
            sfFound = True
            
            for tagtable in datanode.tagtables:
            
              tagId = self.getTagId(tagtable.tagnames[0])
            
              tagTableFound = False
              for refTagtable in otherDataNode.tagtables:
                refTagId = self.getTagId(refTagtable.tagnames[0])
                
                if tagId == refTagId:
                  tagTableFound = True
                
                  if tagtable.free: # Is 1 if it's values belonging to the sf, otherwise it's a loop. Handle differently

                    for tagIndex in range(len(tagtable.tagnames)):
                      tagname = tagtable.tagnames[tagIndex]
                      if tagname not in refTagtable.tagnames:
                        missingTagNames.append((tagname,tagId,sfName,fileName,otherFileName)) 
                      else:
                        refTagIndex = refTagtable.tagnames.index(tagname)
                        
                        # Hard comparison, can be made softer
                        tagvalue = tagtable.tagvalues[tagIndex][0]
                        refTagvalue = refTagtable.tagvalues[refTagIndex][0]
                        if tagvalue != refTagvalue:
                          tagValuemismatch = (sfName,tagId,tagname) # Enough to identify these
                          
                          if tagValuemismatch not in tagValuemismatches:
                            mismatchTagValues.append((tagname,tagId,sfName,tagvalue,refTagvalue,fileName,otherFileName)) 
                            tagValuemismatches.append(tagValuemismatch)

                  else:
                  
                    # First identify tagnames to compare, list the ones that are missing
                    tagindexesToCompare = []
                    refTagIndexesToCompare = []
                    
                    for tagIndex in range(len(tagtable.tagnames)):
                      tagname = tagtable.tagnames[tagIndex]
                      if tagname not in refTagtable.tagnames:
                        missingTagTableNames.append((tagname,tagId,sfName,fileName,otherFileName)) 
                      else:
                        refTagIndex = refTagtable.tagnames.index(tagname)
                        
                        tagindexesToCompare.append(tagIndex)
                        refTagIndexesToCompare.append(refTagIndex)
                   
                    if fileName == fileNames[0]:
                      # Make ref db of all values in correct tag order                  
                      # NOTE: Doing this one only once, no need to do twice!!
                      tagtableValueTuples = []
                      refTagtableValueTuples = []

                      for (curTagtable,curTagindexesToCompare,curTagtableValueTuples) in ((tagtable,tagindexesToCompare,tagtableValueTuples),
                                                                                          (refTagtable,refTagIndexesToCompare,refTagtableValueTuples)):

                        for tagValueIndex in range(len(curTagtable.tagvalues[curTagindexesToCompare[0]])):
                          valueList = []
                          for tagIndex in curTagindexesToCompare:
                            valueList.append(curTagtable.tagvalues[tagIndex][tagValueIndex])
                          valueTuple = tuple(valueList)  
                          curTagtableValueTuples.append(valueTuple)

                      # Then check whether we've got a match. Note that serials should probably be removed here, and some values (i.e. floats) should not be compared as string
                      # Can special-case all that in above loop for quick hacking purposes
                      for valueTuple in tagtableValueTuples[:]:
                       if valueTuple in refTagtableValueTuples:
                         tagtableValueTuples.remove(valueTuple)
                         refTagtableValueTuples.remove(valueTuple)
                         
                      for valueTuple in tagtableValueTuples:
                        mismatchTagTableValues.append((tagId,sfName,str(valueTuple),fileName,otherFileName))

                      for valueTuple in refTagtableValueTuples:
                        mismatchTagTableValues.append((tagId,sfName,str(valueTuple),otherFileName,fileName))

                      #    print tagtable.tagnames
                      #    print tagtable.tagvalues
                      #    sys.exit()
              
              if not tagTableFound:
                missingTagTables.append((tagId,sfName,fileName,otherFileName))  
              
              
        
        if not sfFound:
          missingSfs.append((sfName,fileName,otherFileName)) 
        
    
    if missingSfs:
      self.printHeader("Saveframes missing")
      print
      curFileName = None
      for (sfName,fileName,otherFileName) in missingSfs:
        if curFileName != otherFileName:
          print " * Missing in {}\n".format(otherFileName)
          curFileName = otherFileName
        print "   {}".format(sfName)
      print

    if missingTagTables:
      self.printHeader("Loops missing")
      print
      curFileName = None      
      for (tagId,sfName,fileName,otherFileName) in missingTagTables:
        if curFileName != otherFileName:
          print " * Missing in {}\n".format(otherFileName)
          curFileName = otherFileName
        print "   {} : {}".format(sfName,tagId)
      print
      
    if missingTagNames:
      self.printHeader("Tag names missing")
      print
      curFileName = None      
      for (tagname,tagId,sfName,fileName,otherFileName) in missingTagNames:
        if curFileName != otherFileName:
          print " * Missing in {}\n".format(otherFileName)
          curFileName = otherFileName
        print "   {} : {}".format(sfName,tagname)
      print

    if mismatchTagValues:
      self.printHeader("Tag value mismatches")
      print
      for (tagname,tagId,sfName,tagvalue,refTagvalue,fileName,otherFileName) in mismatchTagValues:
        print "  '{}' <-> '{}'    {}:{}".format(tagvalue,refTagvalue,sfName,tagname)
      print

    if missingTagTableNames:
      self.printHeader("Loop tag names missing")
      print
      curFileName = None      
      for (tagname,tagId,sfName,fileName,otherFileName) in missingTagTableNames:
        if curFileName != otherFileName:
          print " * Missing in {}\n".format(otherFileName)
          curFileName = otherFileName
        print "   {} : {}".format(sfName,tagname)
      print

    if mismatchTagTableValues:
      self.printHeader("Loop tag value mismatches")
      currentId = None
      for (tagId,sfName,valueTupleString,fileNamePresent,fileNameMissing) in mismatchTagTableValues:
        if currentId != (sfName,tagId):
          print
          print ("  {}:{}".format(sfName,tagId))
          currentId = (sfName,tagId)
      
        print ("    '{}' not present in {}".format(valueTupleString,fileNameMissing))
      print


  def getTagId(self,tagName):
  
    return tagName.split('.')[0]
  
  def printHeader(self,text):
  
    print ("*" * (len(text) + 4))
    print ("* {} *".format(text))
    print ("*" * (len(text) + 4))
    
if __name__ == '__main__':
  
  nc = NefComparison()
  nc.compareNefFiles('data/original/CCPN_CASD155.nef','data/modified/CCPN_CASD155.nef')
  #nc.compareNefFiles('data/original/CCPN_H1GI.nef','data/original/CCPN_H1GI_alt.nef')
