##########################################################################
# Author: Jamie Bossenbroek
# Date: 2/18/20
#
# The purpose of this function is to parse together AVI (*.avi)
# PW Doppler Files from VEVO Software. The output will be a grayscale
# unit8 matrix of the parsed AVI. This is a single image of the
# coronary flow pattern which can then be used to extract parameters
# for flow pattern analysis.
#
##########################################################################

import cv2, time
import numpy as np
from PIL import Image, ImageChops

def firstImage(videoFile):
    '''
    This function returns the first image from a video avi file as a
    numpy array. It is used in gui.py and colormode.py
    '''
    vid = cv2.VideoCapture(videoFile)
    ret, frame = vid.read()
    return frame
    

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
    if width == 1168 and height == 864:
        values = [490, 1022, 1046, 41, 1000]
    elif width == 880 and height == 666:
        values = [378, 772, 830, 34, 500]
    else:
        critcut = round(0.567 * height)
        sc = round(0.875 * width)
        if height == 872:
            critcut = 496
        elif height == 880:
            critcut = 499
            sc = 1021
        elif height == 896:
            critcut = 498
            sc = 1021
        values = [critcut, sc, round(0.895 * width), round(0.125*height)-67, 1000]



    ###Crop frames to pertinent information (flow pattern, ecg, and time scale)
    #Find row breaks
    grayImage = cv2.cvtColor(videoFrames[0], cv2.COLOR_RGB2GRAY) #Convert to grayscale
    pixelRowMean = np.average(grayImage, axis = 1) #Pixel row mean
    blackRows = [i for i, x in enumerate(pixelRowMean) if x == 0] #Find black rows
    breakage = []
    count = 0
    
    #Find where blank sections occur and store last row of each section
    for row in blackRows[:-1]:
        if blackRows[count + 1] - blackRows[count] != 1: #Indicates new section begins
            breakage.append(row) #Hold location for later crop
        count += 1
        
    #Cropping frames vertically
    BottomWindowCutoff = breakage[-2] #Below ECG
    TopWindowCutoff = breakage[-4] #Doppler Window start
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
        grayImage[:, values[2]:] = 0 #Black out temperature and heart rate
        
        pixelRowMean = np.average(grayImage, axis = 1) #Pixel row mean
        pixelColumnMean = np.average(grayImage, axis = 0) #Pixel column mean
        notBlackRows = [i for i, x in enumerate(pixelRowMean) if x != 0] #Find rows that aren't all black
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
    for window in dopWinMerge[:-5]:
        (nrows, ncols, third) = window.shape #Find size of difference area
        nrowsStore.append(nrows) #Store number of rows
        #Larger frames indicate potential slide bar reset
        if ncols > values[4]:
            splitscroll.append(count)
        count += 1
    for window in dopWinMerge[-5:-1]:
        (nrows, ncols, third) = window.shape #Find size of difference area
        nrowsStore.append(nrows) #Store number of rows
    
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
            while c < 10 and (index + c < len(dopWinMerge)-1) and check:
                (nrows, ncols, third) = dopWinMerge[index + c].shape
                if nrows == values[0] and ncols == values[1]:
                    check = False
                c += 1
            #Find slider reset frame
            if check:
                c = 0
                (nrows, ncols, third) = dopWinMerge[index].shape
                while nrows != values[0] and (index + c < len(dopWinMerge)-1):
                    c += 1
                    (nrows, ncols, third) = dopWinMerge[index + c].shape
                if (index + c < len(dopWinMerge)-1):
                    newsplitscroll.append(index + c)
            
    newsplitscroll = list(dict.fromkeys(newsplitscroll))
    print(newsplitscroll)
   
    ###Merge images around slider bar reset
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
    endDopLoc = [i for i, x in enumerate(nrowsStore) if x == values[0]] #Find locations of doppler images
    endDopLoc = endDopLoc[-1]
    lastImage = cropImagesFinal[endDopLoc + 1] #Last frame where doppler portion updated
    lastImage = cv2.cvtColor(lastImage, cv2.COLOR_RGB2GRAY) #Convert to grayscale
    lastImage[0:values[3], :] = 0 #Remove Vevo logo
    pixelColumnMean = np.average(lastImage, axis = 0) #Pixel column mean
    pixelColumnMean = np.where(pixelColumnMean != 0, pixelColumnMean, 200) #Make 0's larger numbers
    endLocation = np.argmin(pixelColumnMean) #+ 1 #Right edge of last image will be minimum of entire image
    lastImage = lastImage[:, 0:endLocation] #+1] #Crop array
    pixelColumnMean = np.average(lastImage, axis = 0) #Pixel column mean
    clearZero = [i for i, x in enumerate(pixelColumnMean) if x < 0.2]
    lastImage = np.delete(lastImage, clearZero, axis = 1) #Clear low values from image
    newFirst.append(lastImage)
    

    
    ###Parse together all images
    wholeSequence = np.concatenate(newFirst, axis = 1)
    wholeSequence[0:values[3], :] = 0 #Remove Vevo logo
    wholeSequence = wholeSequence[values[3]-1:, :] #Remove Vevo logo
    (c, length) = wholeSequence.shape #Find pixel length of image
    timeperpixel = length / duration / 10 #Calculate time-per-pixel
    cv2.imwrite('test.png', wholeSequence) #View parsed image
    
    return wholeSequence, timeperpixel
