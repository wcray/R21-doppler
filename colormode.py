##########################################################################
# Author: Jamie Bossenbroek
# Date: 7/16/19
#
# The purpose of this function is to determine the diameter of the 
# left anterior descending coronary artery from Color Doppler Mode .avi
# files. Determines number of frames analyzed, mode/max/min/average 
# diameter, and standard deviation of diameter. 
#
##########################################################################

import cv2, vevoAVIparser, yellowCropAVI, vesselMaskAVI
import numpy as np
from collections import Counter
from PIL import Image

def analyse(videoFile, videoFileCW, colorScale, angle, run):
    #Obtain first image from Doppler .avi file
    firstImage = vevoAVIparser.firstImage(videoFile)
    
    #Create video object of CMode .avi file
    vid = cv2.VideoCapture(videoFileCW)
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
    firstImageCW = videoFrames[0]
    
    #Call yellowCropAVI to determine cropping scale and region of interest
    colScale, rowScale, rows, columns = yellowCropAVI.main(firstImage, firstImageCW)
    
    #Calculate mm/pixel
    height = rows[1] - rows[0] #Height of CMode region in pixels
    pixelScale = colorScale/height
    (height, width, three) = firstImageCW.shape
    
    save = run
    run= 1
    
    ###Cropping CMode frames to region of interest
    centerCol = columns[0] + round((columns[1]-columns[0])*colScale) #Identify column where center line was located on PW Doppler file
    centerCol = int(centerCol)
    centerRow = rows[0] + round((rows[1]-rows[0])*rowScale) #Identify row where center line was located on PW Doppler file
    centerRow = int(centerRow)
    cropCol = [int(columns[0]+round((centerCol-columns[0])/(2+2*run))), int(centerCol+round((2*run+1)*(columns[1]-centerCol)/(2+2*run)))] #Column window region of interest
    cropRow = [int(rows[0]+round((centerRow-rows[0])/(2+2*run))), int(centerRow+round((2*run+1)*(rows[1]-centerRow)/(2+2*run)))] #Row window region of interest
    run = save
    #Crop each frame and identify diameters of vessels present
    diamMode = []
    for image in videoFrames:
        padheight = (rows[1]-centerRow) - (centerRow - rows[0])
        padwidth = (columns[1]-centerCol) - (centerCol - columns[0])
        #Image.fromarray(image).show()
        if padheight > rows[0]:
            padheight = rows[0]
        if padwidth > columns[0]:
            padwidth = columns[0]
        if padheight < rows[1] - height:
            padheight = rows[1] - height
        if padwidth < columns[1] - width:
            padwidth = columns[1] - width
        if padheight <= 0 and padwidth <=0:
            area = image[rows[0]:rows[1]+1-padheight, columns[0]:columns[1]+1-padwidth]
            rotateim = Image.fromarray(area)
            rotateim = rotateim.rotate(angle)
            image = np.array(rotateim)
            croppedImage = image[cropRow[0]-rows[0]:cropRow[1]-rows[1]+padheight, cropCol[0]-columns[0]:cropCol[1]-columns[1]+padwidth] #Crop frame
        elif padheight > 0 and padwidth > 0:
            area = image[rows[0]-padheight:rows[1]+1, columns[0]-padwidth:columns[1]+1]
            rotateim = Image.fromarray(area)
            rotateim = rotateim.rotate(angle)
            image = np.array(rotateim)
            croppedImage = image[cropRow[0]-rows[0]+padheight:cropRow[1]-rows[1], cropCol[0]-columns[0]+padwidth:cropCol[1]-columns[1]] #Crop frame
        elif padheight <= 0  and padwidth > 0:
            area = image[rows[0]:rows[1]+1-padheight, columns[0]-padwidth:columns[1]+1]
            rotateim = Image.fromarray(area)
            rotateim = rotateim.rotate(angle)
            image = np.array(rotateim)
            croppedImage = image[cropRow[0]-rows[0]:cropRow[1]-rows[1]+padheight, cropCol[0]-columns[0]+padwidth:cropCol[1]-columns[1]] #Crop frame
        elif padheight > 0 and padwidth <= 0:
            area = image[rows[0]-padheight:rows[1]+1, columns[0]:columns[1]+1-padwidth]
            rotateim = Image.fromarray(area)
            rotateim = rotateim.rotate(angle)
            image = np.array(rotateim)
            croppedImage = image[cropRow[0]-rows[0]+padheight:cropRow[1]-rows[1], cropCol[0]-columns[0]:cropCol[1]-columns[1]+padwidth] #Crop frame
        diameters = vesselMaskAVI.vesselDiam(croppedImage, pixelScale, run) #Return diameter(s) of vessel(s)
        if diameters:
            diamMode.append(np.max(diameters)) #Only keep maximum diameter measurement
    
    
    
    ###Remove unrepresentative values from data set
    mean = np.mean(diamMode)
    std = np.std(diamMode)
    botcut = mean - (2.4*std)
    topcut = mean + (3*std)
    for entdiam in diamMode:
        if entdiam < botcut or entdiam > topcut:
            diamMode.remove(entdiam)
    
    
    ###Calculate and return parameters
    numFrames = len(diamMode) #Number of frames analyzed
    if numFrames > 0:
        maxD = np.max(diamMode) #Maximum diameter
        minD = np.min(diamMode) #Minimum diameter
        mean = np.mean(diamMode) #Average diameter
        median = np.median(diamMode)
        std = np.std(diamMode) #Standard deviation
        data = Counter(diamMode)
        modes = data.most_common()
        freqMode = data.most_common(1)[0][1] #Frequency of mode
        maximum = [i for i, x in enumerate(modes) if x[1] == freqMode]
        maxVals = [modes[i][0] for i in maximum]
        mode = max(maxVals) #Maximum mode
    else:
        mode = 0
        freqMode = 0
        maxD = 0
        minD = 0
        mean = 0
        median = 0
        std = 0
        print('Empty')
    
    ColorParameters = [numFrames, mode, freqMode, maxD, minD, mean, median, std]
    
    return ColorParameters