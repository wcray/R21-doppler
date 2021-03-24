##########################################################################
# Author: Jamie Bossenbroek
# Date: 7/16/19
#
# The purpose of this function is primarily to isolate the yellow square
# from both the PW Doppler and Color Mode .avi files. The function will
# find the columns left, center(in PW Doppler), and right of the square and the 
# rows on top and bottom. It also finds the row and column scaling factor
# to the center of the vessel. 
#
##########################################################################

import numpy as np
import cv2, tkinter, guis
from PIL import Image

def threshold(image, minimum, maximum):
    '''
    This function returns a grayscale thresholded image given an
    image and the minimum and maximum threshold values.
    '''
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) #Convert to rgb
    hvsImage = cv2.cvtColor(image, cv2.COLOR_RGB2HSV) #Convert to hvs
    mask = cv2.inRange(hvsImage, minimum, maximum) #Create mask from given thresholds
    maskedImage = cv2.bitwise_and(image, image, mask = mask) #Threshold image
    maskedImageGray = cv2.cvtColor(maskedImage, cv2.COLOR_RGB2GRAY) #Convert to grayscale
    return maskedImageGray

def main(firstImage, firstCMImage):
    ###Threshold Images
    #Set range of colors
    minimum = (20, 50, 80)
    maximum = (50, 255, 220)
    
    maskedImageGray = threshold(firstImage, minimum, maximum)
    maskedCMImageGray = threshold(firstCMImage, minimum, maximum)
    

    
    ###Find column scale and row scale from doppler image
    #Determine row locations of yellow box
    rows = []
    pixelRowMean = np.average(maskedImageGray, axis = 1) #Pixel row mean
    indexR = np.argsort(pixelRowMean)
    rows.append(np.min(indexR[-2:])) #Top of yellow box
    rows.append(np.max(indexR[-2:])) #Bottom of yellow box
    
    #Determine column locations of yellow box
    columns = []
    pixelColumnMean = np.average(maskedImageGray, axis = 0) #Pixel column mean
    indexC = np.argsort(pixelColumnMean)
    columns.append(np.min(indexC[-3:])) #Left of yellow box
    columns.append(int(np.median(indexC[-3:]))) #Middle of yellow box
    columns.append(np.max(indexC[-3:])) #Right of yellow box
    
    #Determine vertical location of center yellow line
    ##Note: this will be in between the yellow gate
    maskedImageGray[rows[1]:, :] = 0
    pixelRowMean = np.average(maskedImageGray, axis = 1) #Pixel row mean
    indexR = np.argsort(pixelRowMean)
    dif = (rows[1]-rows[0])/10
    vesselCenter = indexR[-2]
    if not vesselCenter >= rows[0] + dif and not vesselCenter <= rows[1] - dif:
        inrange = []
        add = 0
        while add < 5 or len(inrange) == 0:
            vesselCenter = indexR[-2 - add]
            if vesselCenter >= rows[0] + dif and vesselCenter <= rows[1] - dif:
                inrange.append(vesselCenter) #Save if between top and bottom of yellow box
            add += 1
        vesselCenter = int(round(np.max(inrange)+np.min(inrange))/2) #Find center between top and bottom of gate
    
#    print('Vessel center: ' + str(vesselCenter))
#    print(rows)
#    checker = 0
#    while checker != vesselCenter:
#        copy = firstImage
#        copy[vesselCenter, :] = 255
#        copy[:, columns[1]] = 255
#        Image.fromarray(copy).show()
#        root = tkinter.Tk()
#        window = guis.Num(root, 0)
#        root.mainloop()
#        checker = vesselCenter
#        vesselCenter = int(window.num)
        
    colScale = (columns[1]-columns[0])/(columns[2]-columns[0]) #Calculate column scaling factor for ROI
    rowScale = (vesselCenter-rows[0])/(rows[1]-rows[0]) #Calculate row scaling factor for RIO
    
    
    
    ###Find yellow box location on CMode image
    #Determine row locations of yellow box
    rows = []
    pixelRowMean = np.average(maskedCMImageGray, axis = 1) #Pixel row mean
    indexR = np.argsort(pixelRowMean)
    rows.append(np.min(indexR[-2:])) #Top of yellow box
    rows.append(np.max(indexR[-2:])) #Bottom of yellow box
    height, width = maskedCMImageGray.shape
    block = height/8*7
    if abs(rows[0]-rows[1]) < 20 or rows[1] > block:
        indexR = indexR[indexR < block]
        rows = []
        rows.append(np.min(indexR[-2:]))
        rows.append(np.max(indexR[-2:]))
    
    #Determine colum locations of yellow box
    columns = []
    pixelColumnMean = np.average(maskedCMImageGray, axis = 0) #Pixel column mean
    indexC = np.argsort(pixelColumnMean)
    columns.append(np.min(indexC[-2:])) #Left of yellow box
    columns.append(np.max(indexC[-2:])) #Right of yellow box
    
    return colScale, rowScale, rows, columns