##########################################################################
# Author: Jamie Bossenbroek
# Date: 7/25/21
#
# The purpose of this function is to parse together AVI (*.avi)
# PW Doppler Files from VEVO Software. The output will be a grayscale
# unit8 matrix of the parsed AVI. This is a single image of the
# coronary flow pattern which can then be used to extract parameters
# for flow pattern analysis.
#
##########################################################################

import cv2
import numpy as np
from PIL import Image, ImageChops
import pytesseract

def firstImage(videoFile):
    '''
    This function returns the first image from a video avi file as a
    numpy array. It is used in colormode.py
    '''
    vid = cv2.VideoCapture(videoFile)
    ret, frame = vid.read()
    return frame
    


def autoVel(img):
    '''
    This function returns a list of numbers identified in a given image.
    Numbers are assumed to be vertically aligned, and then image is assumed
    to be cropped to the region of interest
    '''
    #cMode = img_grey[breakageR[4]:breakage[5], :breakage[1]]

    #Binarize and invert images    
    img = np.invert(img)
    img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)[1]
    
    #Read text
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/Cellar/tesseract/4.1.1/bin/tesseract'
    tconfig = r'--psm 4 digits'
    numFound = pytesseract.image_to_string(img, lang='eng', config=tconfig)
    
    digits = filter(lambda x: x != "", numFound.split("\n"))
    
    return list(digits)



def parse(videoFile):
    ###Create video object    
    vid = cv2.VideoCapture(videoFile)
    height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)) #Obtain video height
    width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)) #Obtain video width
    fps = vid.get(cv2.CAP_PROP_FPS) #Obtain frames per second
    frameCount = int(vid.get(cv2.CAP_PROP_FRAME_COUNT)) #Obtain number of frames
    duration = frameCount/fps #Calculate video duration in seconds
    
    #Create list of all video frames
    videoFrames = []
    while(vid.isOpened()):
        #Capture frame-by-frame
        ret, frame = vid.read()
        if ret:
            videoFrames.append(frame)
        else:
            break
    vid.release()
    cv2.destroyAllWindows()
    
    #Remove empty indicies
    list(filter((0).__ne__, videoFrames))
    
    #Values depending on video size
    ##Note: [slider bar row, slider bar column, temperature black-out, Vevo logo black-out, slide bar minimum]
    print('height: ' + str(height) + ' width: ' + str(width))
    if width == 880 and height == 666:
        values = [378, 772, 34, 500]
    elif width == 1168 and height == 864:
        values = [490, 1022, 41, 1000]
    elif width == 1168 and height == 872:
        values = [496, 1022, 42, 1000]
    elif width == 1168 and height == 880:
        values = [499, 1021, 43, 1000]
    elif width == 1168 and height == 896:
        values = [498, 1024, 45, 1000]
    else:
        #Default values
        values = [round(0.567 * height), round(0.875 * width), round(0.125*height)-67, 1000]
        print(values)



    ###Crop frames to pertinent information (flow pattern, ecg, and time scale)
    grayImage = cv2.cvtColor(videoFrames[0], cv2.COLOR_RGB2GRAY) #Convert to grayscale
    pixelRowMean = np.average(grayImage, axis = 1) #Pixel row mean
    blackRows = [i for i, x in enumerate(pixelRowMean) if x == 0] #Find black rows
    pixelColumnMean = np.average(grayImage, axis = 0) #Pixel row mean
    blackColumns = [i for i, x in enumerate(pixelColumnMean) if x == 0] #Find black rows
    
    #Find where blank sections occur and store last row of each section
    breakageR = []
    count = 0
    for row in blackRows[:-1]:
        if blackRows[count + 1] - blackRows[count] != 1: #Indicates new section begins
            breakageR.append(row) #Hold location for later crop
        count += 1
        
    #Find where blank sections occur and store last column of each section
    breakageC = []
    count = 0
    for column in blackColumns[:-1]:
        if blackColumns[count + 1] - blackColumns[count] != 1: #Indicates new section begins
            breakageC.append(column) #Hold location for later crop
        count += 1
     
    #autoDetect max velocity
    velScape = grayImage[breakageR[5]:breakageR[6], breakageC[1]:breakageC[2]]
    maxVel = int(autoVel(velScape)[0])

    #Cropping frames vertically
    BottomWindowCutoff = breakageR[-2] #Below ECG
    TopWindowCutoff = breakageR[-4] #Doppler Window start
    cropImages = []
    for image in videoFrames:
        cropImages.append(image[TopWindowCutoff:BottomWindowCutoff+1, :]) #Crop each frame
    
    #Find column breaks
    grayImage = cv2.cvtColor(cropImages[0], cv2.COLOR_RGB2GRAY) #Convert to grayscale
    pixelColumnMean = np.average(grayImage, axis = 0) #Pixel column mean
    blackColumns = [i for i, x in enumerate(pixelColumnMean[0:30]) if x == 0] #Find black columns on left
    LeftWindowCutoff = blackColumns[-1] #After color scale
    blackColumnsFull = [i for i, x in enumerate(pixelColumnMean) if x == 0] #Find black columns
    RightWindowCutoff = blackColumnsFull[len(blackColumns)] #Before velocity scale
    ##Note: right window cutoff will be first black column after left window cutoff
    
    #Cropping frames horizontally
    cropImagesFull = []
    for image in cropImages:
        cropImagesFull.append(image[:, LeftWindowCutoff:RightWindowCutoff+1]) #Crop each frame
    

    
    ###Calculate difference between consecutive frames
    differenceCropped = []
    count = 0
    while count < len(cropImagesFull) - 1:
        #numpy array to PIL Image
        image1 = Image.fromarray(videoFrames[count])
        image2 = Image.fromarray(videoFrames[count+1])
        
        #Save difference of frames
        diffImg = ImageChops.difference(image1, image2) #Difference between frames
        diff = np.array(diffImg) #Convert to numpy array
        grayImage = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY) #Convert to grayscale
        grayImage[:, breakageC[0]:] = 0 #Black out temperature and heart rate
        
        pixelRowMean = np.average(grayImage, axis = 1) #Pixel row mean
        notBlackRows = [i for i, x in enumerate(pixelRowMean) if x != 0] #Find rows that aren't all black
        pixelColumnMean = np.average(grayImage, axis = 0) #Pixel column mean
        notBlackColumns = [i for i, x in enumerate(pixelColumnMean) if x != 0] #Find columns that aren't all black
        if not notBlackRows and not notBlackColumns: #eliminates error where frame is same as last frame
            crop2 = [] #Same as previous frame, so remove
            cropImagesFull[count] = []
        else:
            #Crop so only area of difference is saved
            crop2 = diff[notBlackRows[0]:, notBlackColumns[0]:notBlackColumns[-1]+1]
        differenceCropped.append(crop2)
        count += 1
        
    #Remove empty/duplicate frames
    cropImagesFinal = list(filter(([]).__ne__, cropImagesFull))
    dopWinMerge = list(filter(([]).__ne__, differenceCropped))


    
    ###Identify frames where slider bar resets
    splitscroll = []
    nrowsStore = []
    count = 0
    for window in dopWinMerge[:-1]:
        (nrows, ncols, third) = window.shape #Find size of difference area
        nrowsStore.append(nrows) #Store number of rows
        if ncols > values[3]:
            splitscroll.append(count)
        count += 1
    
    #Find frames corresponding to slider bar reset
    newsplitscroll = []
    for index in splitscroll:
        (nrows, ncols, third) = dopWinMerge[index].shape #Find size of difference area
        if nrows == values[0] and ncols == values[1]:
            newsplitscroll.append(index) #Size corresponds to slider bar reset
        #Check for cases where slider bar is very close to edge of frame and size is not exact
        else:
            check = True
            c = -5
            #Check that frame is not next to actual slider bar reset frame
            #!!!TO DO: simplify, it takes up too much time
            while c < 5 and (index + c < len(dopWinMerge)-1) and check:
                (nrows, ncols, third) = dopWinMerge[index + c].shape
                if nrows == values[0] and ncols == values[1]:
                    check = False
                c += 1
            #Find slider reset frame
            if check:
                c = 0
                (nrows, ncols, third) = dopWinMerge[index].shape
                while nrows != values[0] and (index + c < len(dopWinMerge)-1) and c < 10:
                    c += 1
                    (nrows, ncols, third) = dopWinMerge[index + c].shape
                if (index + c < len(dopWinMerge)-1) and c < 10:
                    print('USED EXTRA CHECK FOR: ' + str(index+c))
                    newsplitscroll.append(index + c)
            
    newsplitscroll = list(dict.fromkeys(newsplitscroll))
   
    ###Merge images around slider bar reset
    endDopLoc = [i for i, x in enumerate(nrowsStore) if x == values[0]][-1] #Find locations of doppler images
    if endDopLoc in newsplitscroll: newsplitscroll.remove(endDopLoc)
    newFirst = []
    for index in newsplitscroll:
        #Find location of slider bar
        grayImage = cv2.cvtColor(cropImagesFinal[index + 1], cv2.COLOR_RGB2GRAY) #Convert to grayscale
        pixelColumnMean = np.average(grayImage, axis = 0) #Column pixel mean
        sliderBar = [i for i, x in enumerate(pixelColumnMean) if x > 0 and x < 1] #Determine where slider bar ends
        if not sliderBar:
            sliderBar = [0, 1]
        
        #Crop frame just before slider reset
        firstFrame = cropImagesFinal[index - 1]
        firstFrame = firstFrame[:, 0:sliderBar[-1]+1] #Keep left side of picture
        firstFrame = cv2.cvtColor(firstFrame, cv2.COLOR_RGB2GRAY) #Convert to grayscale
        
        #Crop frame just after slider reset
        splitFrame4Deletion = cropImagesFinal[index + 1]
        splitFrame4Deletion = splitFrame4Deletion[:, sliderBar[0]:] #Keep right side of picture
        splitFrame4Deletion = cv2.cvtColor(splitFrame4Deletion, cv2.COLOR_RGB2GRAY) #Convert to grayscale
        
        #Create new array of parsed image after slider bar reset
        combined = np.append(firstFrame, splitFrame4Deletion, axis = 1)
        pixelColumnMean = np.average(combined, axis = 0) #Pixel column mean
        clearZero = [i for i, x in enumerate(pixelColumnMean) if x < 0.2]
        combined = np.delete(combined, clearZero, axis = 1) #Clear blank columns
        newFirst.append(combined)
        
    #Follow similar routine for last partial image
    lastImage = cropImagesFinal[endDopLoc + 1] #Last frame where doppler portion updated
    lastImage = cv2.cvtColor(lastImage, cv2.COLOR_RGB2GRAY) #Convert to grayscale
    lastImage[0:values[2], :] = 0 #Remove Vevo logo
    pixelColumnMean = np.average(lastImage, axis = 0) #Pixel column mean
    pixelColumnMean = np.where(pixelColumnMean != 0, pixelColumnMean, 200) #Make 0's larger numbers
    endLocation = np.argmin(pixelColumnMean) #Right edge of last image will be minimum of entire image
    lastImage = lastImage[:, 0:endLocation] #Crop array
    pixelColumnMean = np.average(lastImage, axis = 0) #Pixel column mean
    clearZero = [i for i, x in enumerate(pixelColumnMean) if x < 0.2]
    lastImage = np.delete(lastImage, clearZero, axis = 1) #Clear low values from image
    newFirst.append(lastImage)
    

    
    ###Parse together all images
    wholeSequence = np.concatenate(newFirst, axis = 1)
    wholeSequence[0:values[2], :] = 0 #Remove Vevo logo
    wholeSequence = wholeSequence[values[2]-1:, :] #Remove Vevo logo
    (c, length) = wholeSequence.shape #Find pixel length of image
    timeperpixel = duration/length
    
    return wholeSequence, timeperpixel, maxVel
