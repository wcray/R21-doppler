##########################################################################
# Author: Jamie Bossenbroek
# Date: 7/16/19
#
# The purpose of this function is to return an array containing all the 
# measured diameters from each frame of a Color Mode .avi file ROI.
#
##########################################################################

import numpy as np
import cv2, yellowCropAVI
from collections import Counter
from PIL import Image

def vesselDiam(image, pixelScale, run):
    ###Mask vessels
    #Set range of colors
    minimum = (0, 150, 80)
    maximum = (110, 255, 255)
    maskedImageGray = yellowCropAVI.threshold(image, minimum, maximum)
        
    #Identify contours of vessles (if present)
    edges = cv2.Canny(maskedImageGray, 30, 100)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    height, width = maskedImageGray.shape
    
    ###Calculate diameter of each vessel present
    diameters = []
    mask = np.ones(maskedImageGray.shape[:2], dtype = "uint8") * 255
    for vessel in contours:
        #Check that vessel is large enough that it's not noise
        (size, x, y) = vessel.shape
        #Check that vessel is not on sides or bottom edge of ROI
        minW = np.min(vessel[:, 0, 0])
        maxW = np.max(vessel[:, 0, 0])
#        minH = np.min(vessel[:, 0, 1])
        maxH = np.max(vessel[:, 0, 1])
        if size > 100 + (50*run) and maxH < height - 2 and minW > 1 and maxW < width - 2:
            vertical = {}
            #Create list of all vertical pixels and corresponding horizontal pixels
            count = 0
            for row in vessel[:, 0, 1]:
                vertical.setdefault(row, []).append(vessel[count, 0, 0])
                count += 1
            #Subtract left-most vessel wall from right-most vessel wall
            holdW = []
            for key in vertical:
                widthD = max(vertical[key]) - min(vertical[key])
                if widthD > 10 and len(vertical[key]) < 10:
                    holdW.append(widthD)
            diam = np.mean(holdW)
            if diam >10 + (run*15):
                diameters.append(round(diam * pixelScale, 5))
            else:
                cv2.drawContours(mask, vessel, -1, 0, -1)
        else:
            cv2.drawContours(mask, vessel, -1, 0, -1)
    
    if len(diameters) > 0:
        if (run == 0):
            title = 'bl_'
        else:
            title = 'hyperemia_'
        name = title + str(max(diameters)) + '.png'
        comb = cv2.bitwise_and(edges, edges, mask=mask)
        comb = maskedImageGray + comb
        saveim = Image.fromarray(comb)
        saveim.save(name)
    return diameters