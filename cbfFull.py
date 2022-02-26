##########################################################################
#Author: Jamie Bossenbroek
#Date: 8/28/21
#
#This program will allow the user to semi-automatically analyze PW Doppler and
#Color Mode video files. This program gives the user the ability to obtain 
#point velocity, slope, time, area under the curve (VTI), and Heart Rate 
#measurements for coronary blood flow patterns. Additionally and if
#desired, the program will extract diameter measurements from coronary
#Color Mode files and determne blood flow velocity under baseline and
#hyperemic conditions as well as coronary flow reserve and coronary flow
#velocity reserve. Compared to manual analysis, this program drastically
#reduces time of analysis and nearly eliminates intraoperator bias.
#
##########################################################################
import time, cv2, scipy, tkinter, guis, vevoAVIparser, colormode, math
from tkinter import filedialog
from skimage import morphology
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



# Track analysis time
startTime = time.perf_counter()

###File selection, parameter input, and video parsing
#Select folder containing video files to be analyzed
root = tkinter.Tk()
root.withdraw()
folderpath = filedialog.askdirectory(parent = root, initialdir = "/", title = "Select Folder Path")

#Input filename where doppler analysis results will be stored
savefile = filedialog.asksaveasfilename(parent = root, initialdir = folderpath, title = "Save Results As:")
if not savefile.endswith('.xlsx', len(savefile) - 5):
    savefile += '.xlsx'
 
    
#Open question dialogue for choice of method analysis: Doppler or Color Mode
root.deiconify()
window = guis.Method(root)
root.mainloop()
choice = window.choice

#Select files for analysis
filename = [] #Store doppler filenames
pics = [] #Store parsed video images
TP = [] #Store time per pixel
velocityMax = [] #Store maximum velocities
angleG = [] #Store probe angle
maxPen = [] #Store max penetration
minPen = [] #Store min penetration

#Select baseline files for analysis
root = tkinter.Tk()
root.withdraw()
blfiles = filedialog.askopenfilenames(parent = root, initialdir = folderpath, title = "Select baseline video files", filetypes = [("Video files","*.avi")])
numBLVideos=len(list(blfiles))
filename.extend(list(blfiles))

#Select hyperemic files for analysis
hfiles = filedialog.askopenfilenames(parent = root, initialdir = folderpath, title = "Select hyperemic video files", filetypes = [("Video files","*.avi")])
numHVideos=len(list(hfiles))
filename.extend(list(hfiles))
root.destroy()

for video in filename:
    #Read in video files and proccess with vevoAVIparser
    pictureBL, timeperpixelBL, maxVel = vevoAVIparser.parse(video) #Return parsed image and time per pixel
    pics.append(pictureBL)
    TP.append(timeperpixelBL)
    velocityMax.append(maxVel) #Store maximum velocity
    
    

#Select colormode videos for analysis        
if choice == "Combined Analysis":
    root = tkinter.Tk()
    root.withdraw()
    baselineCModeFile = filedialog.askopenfilename(parent = root, initialdir = folderpath, title = "Select baseline colormode file", filetypes = [("Video files","*.avi")])
    hyperemicCModeFile = filedialog.askopenfilename(parent = root, initialdir = folderpath, title = "Select hyperemic colormode file", filetypes = [("Video files","*.avi")])
    filenameCMode = [baselineCModeFile, hyperemicCModeFile]
    root.destroy()
    
    #Input parameters for bl and hyperemia colormode
    root = tkinter.Tk()
    window = guis.DataEntryOne(root, filename[0], filename[numBLVideos])
    root.mainloop()
    angleG.extend(list(window.VAngleG)) #Store probe angle
    angleG = [int(item) for item in angleG]
    maxPen.extend(list(window.Max_Pen)) #Store maximum penetration depth
    maxPen = [float(item) for item in maxPen]
    minPen.extend(list(window.Min_Pen)) #Store minimum penetration depth
    minPen = [float(item) for item in minPen]
    


###Store final results and values
flowProp = [] #Store flow properties
colorPall = [] #Store colorMode parameters
vti_hr = [] #Store VTI x HR
w = pd.ExcelWriter(savefile) #File writer
countALL = 0
for picture in pics:
    ###Crop Doppler images
    pixelRowMean = np.average(picture, axis = 1) #Pixel row mean
    horizLineRow = np.argmax(pixelRowMean) #Find baseline, which is mostly white
    blankRows = [i for i, x in enumerate(pixelRowMean) if x == 0] #Find blank rows
    diffblankRows = np.diff(blankRows) #Find difference between blank rows
    ecgRowStart = [i for i, x in enumerate(diffblankRows) if x != 1]
    ecgTopWindow = blankRows[ecgRowStart[-1]] + 2 #This is below top of gray box
    
    dopplerRegion = picture[0:horizLineRow+1, :] #Crop everything below baseline
    ecgRegion = picture[ecgTopWindow:ecgTopWindow + diffblankRows[ecgRowStart[-1]]-3, :] #Crop ECG pattern
    
    vertPixelsMax = blankRows[ecgRowStart[0]+1] - blankRows[ecgRowStart[0]] #Height of Doppler Region column in pixels
    velocityPerPixel = velocityMax[countALL] / vertPixelsMax #Calculate velocity per pixel
    timePerPixel = .1/TP[countALL] #Calculate time-per-pixel
    
    
    
    ###Threshold doppler images
    blur = cv2.GaussianBlur(dopplerRegion, (9, 9), 3.0) #Gaussian filter
    kernel = np.ones((5, 5), np.uint8) #Structuring element 5 pixels in length
    dopplerFilter = cv2.dilate(blur, kernel, iterations=1) #Dilate region
    values90 = np.percentile(dopplerFilter.ravel(), 90)
    threshUP = dopplerFilter
    threshUP = np.where(threshUP < values90, threshUP, threshUP+50)
    thresh, doppFiltBW = cv2.threshold(threshUP, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU) #Determine threshold using otsu's method
    
    
    #Check if threshold is OK or if user would like to adjust it manually
    root = tkinter.Tk()
    window = guis.ScrollTest(root, thresh, doppFiltBW, dopplerRegion)
    root.mainloop()
    finalThresh = int(window.threshold)
    
    #Remove noise
    finalThresh, doppFiltBW = cv2.threshold(dopplerFilter, finalThresh, 255, cv2.THRESH_BINARY)
    removeNoise = morphology.remove_small_objects(doppFiltBW.astype(bool), min_size=250, connectivity=2).astype(int) #Remove objects less than 250 pixels
    removeNoise = morphology.remove_small_holes(removeNoise, area_threshold=150, connectivity=2).astype(int) #Fill holes smaller than 200 pixels
    
    border = np.pad(removeNoise, (1,1), 'minimum') #Pad array with 0s
    border = border[1:, :] #Remove top pad
    
    border = np.where(border==0, border, 255)
    cv2.imwrite('border.png', border)
    imgBW = cv2.imread('border.png')
    imgray = cv2.cvtColor(imgBW, cv2.COLOR_RGB2GRAY) #Convert to grayscale
    contours,hierarchy = cv2.findContours(imgray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) #Find contours in image
            
    imgRows = imgBW.shape[0] #Image height
    imgCols = imgBW.shape[1] #Image width
    radius = imgRows/10 #NEED TO TEST OTHER VALUES
    contourList = [];
    
    for idx in np.arange(len(contours)):
        cnt = contours[idx]
        for pt in cnt:
            rowCnt = pt[0][1]
            colCnt = pt[0][0]
            check1 = (rowCnt >= imgRows-1-radius and rowCnt < imgRows)
            
            #Identify all contours touching top edge withing radius
            if check1:
                contourList.append(idx)
                break
            
    for idx in contourList:
        cv2.drawContours(imgBW, contours, idx, (0,0,0), -1) #Draw contours
        
    imgray = cv2.cvtColor(imgBW, cv2.COLOR_RGB2GRAY).astype('int64')    
    removeNoiseHold = np.subtract(border, imgray) #Remove contours from original image
    removeNoise = removeNoiseHold[:-1, 1:-1] #Remove side and bottom padding
    
    #Display final image with top noise removed
    borderimg = np.where(removeNoise==0, removeNoise, 255)
    cv2.imwrite('border.png', borderimg)
    
    #Threshold ECG region
    ecgThresh, ecgRegionBinary = cv2.threshold(ecgRegion, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    
    
    
    ###Extracting the envelope
    #Store first white pixel in flow pattern envelope
    velStore = []
    checksBase = []
    print(int(horizLineRow))
    for column in removeNoise.T:
        velocity = [i for i, x in enumerate(column) if x > 0] #Find white pixels
        if not velocity:
            velStore.append(int(horizLineRow)) #Store baseline location
            checksBase.append(column)
        else:
            velStore.append(velocity[0]) #Store first pixel from top
    
    ecgStore = []
    for column in ecgRegionBinary.T:
        ecgVelocity = [i for i, x in enumerate(column) if x > 0] #Find white pixels
        if not ecgVelocity:
            ecgStore.append(len(column)-1) #Store baseline location
        else:
            ecgStore.append(ecgVelocity[0]) #Store first pixel from top
    
    #Create axis of values
    timeAxis = np.linspace(0, timePerPixel*(len(dopplerRegion[0])-1), len(removeNoise[0])) #Horizontal time axis in ms
    vertAxis = np.linspace(0, velocityPerPixel*len(removeNoise), len(removeNoise)) #Vertical velocity axis in mm/s
    vertAxisECG = np.linspace(0, velocityPerPixel*len(ecgRegionBinary), len(ecgRegionBinary)) #Vertical velocity axis in mm/s
    
    #Convert from pixel to velocity
    ##Note: pixels in real image go from top to bottom
    velStore[:] = [len(removeNoise) - x-1 for x in velStore]
    ecgStore[:] = [len(ecgRegionBinary) - x-1 for x in ecgStore]
    
    #Store actual velocity values from image
    finalVertMat = []
    for pixel in velStore:
        finalVertMat.append(vertAxis[pixel]) #Obtain velocity value from vertAxis
    
    finalVertECG = []
    for pixel in ecgStore:
        finalVertECG.append(vertAxisECG[pixel]) #Obtain velocity value from vertAxisECG
    
    #Apply lowpass buttworth filter
    [b, a] = scipy.signal.iirfilter(3, 0.3, btype = 'lowpass', ftype = 'butter')
    finalVertButter = scipy.signal.filtfilt(b, a, finalVertMat)
    
    
    
    ###Divide into cardiac cycles
    #Find ecg peaks
    locs = scipy.signal.find_peaks(finalVertECG, distance = 120, width = 2)[0]
    
    #Check first and last peaks
    peaklocadd = 20 #arbitrary number to compare ecg peak with doppler start
    peaks = [finalVertECG[i] for i in locs] #Determine velocity of peaks
    if locs[-1] + peaklocadd > len(removeNoise[0]) or peaks[-1] < np.mean(peaks[1:-1]) * .75:
        locs = np.delete(locs, -1) #Last peak is not representative, so remove
        peaks = np.delete(peaks, -1)
    if peaks[0] < np.mean(peaks[1:-1]) * .75:
        locs = np.delete(locs, 0) #First peak is not representative, so remove
    
    count = 0
    peakdist = []
    for a in locs[:-1]:
        peakdist.append(locs[count+1] - a)
        count+=1
    
    avgPeakDist = np.mean(peakdist)
    distAdd = np.percentile(peakdist, 25)
    count = 0
    for a in peakdist:
        while a > avgPeakDist and locs[count+1] - locs[count] - distAdd > np.min(peakdist):
            locs = np.insert(locs, count+1, locs[count] + distAdd)
            a -= distAdd
            count += 1
        count+=1
            
    #View ecg peaks
    peakImg = ecgRegionBinary
    peakImg.T[locs] = 255
    filenamepeak = 'peaks' + str(countALL) + '.png'
    cv2.imwrite(filenamepeak, peakImg)
    
    #Calculate beats-per-minute
    bpm = []
    count = 0
    maxTime = [timeAxis[i] for i in locs] #Determine time of peaks
    while count < len(maxTime) - 1:
        bpm.append(round(60 / (maxTime[count+1] - maxTime[count])))
        count += 1
        
    #Create matrix for cardiac cycle locations on Doppler Region
    singleCycle = np.zeros(shape=(2, len(locs)))
    peakCheck = np.zeros(shape=(2, peaklocadd))
    count = 0
    for index in locs:
        peakCheck[0, :] = timeAxis[index:index+peaklocadd]
        peakCheck[1, :] = finalVertButter[index:index+peaklocadd]
        rangeMinLoc = np.argmin(peakCheck[1, :]) #Location of minimum velocity
        rangeMin = peakCheck[1, rangeMinLoc] #Minimum velocity in filtered distance
        if rangeMin*1.4 < finalVertButter[index]:
            #Start of cycle is more representative at this point
            singleCycle[0, count] = timeAxis[index+rangeMinLoc-1]
            singleCycle[1, count] = finalVertButter[index+rangeMinLoc-1]
        else:
            #R-wave peak is at a representative start point
            singleCycle[0, count] = timeAxis[index]
            singleCycle[1, count] = finalVertButter[index]
        count += 1
    
    #Store all data for each cycle
    cardiacCycleTimes = []
    cardiacCycleVels = []
    count = 0
    while count < len(singleCycle[0, :])-1:
        start = [i for i, x in enumerate(timeAxis) if x == singleCycle[0][count]][0]
        end = [i for i, x in enumerate(timeAxis) if x == singleCycle[0][count+1]][0]
        cardiacCycleTimes.append(timeAxis[start:end+1]) #All time points from beginning to end of cycle
        cardiacCycleVels.append(finalVertButter[start:end+1]) #All velocity points from beginning to end of cycle
        count +=1
    
    
    
    ###Extract key parameters from each cycle
    flowProperties = []
    count = 0
    hold, length = singleCycle.shape
    implot = plt.imshow(dopplerRegion) #Plot data on doppler image
    while count < length-1:
        timeCycle = cardiacCycleTimes[count] #Extract time values for cycle
        filtEnvelope = cardiacCycleVels[count] #Extract velocity values for cycle
        velSlope = np.diff(np.insert(filtEnvelope, 0, 0)) / np.diff(np.insert(timeCycle, 0, 0));
        integral = np.trapz(filtEnvelope, timeCycle) #Determine VTI
        
        #Peak diastolic velocity (PDV)
        filtMaxLoc = np.argmax(filtEnvelope) #Maximum velocity index
        filtMax = filtEnvelope[filtMaxLoc] #Maximum velocity
        PVtime = timeCycle[filtMaxLoc] #Maximum velocity time
        
        #Peak diastolic acceleration (PDA)
        twentyCycle = (timeCycle[-1]-timeCycle[0]) * .2 #20% of total beat duration
        twentyWinStart = PVtime - twentyCycle #Time 20% prior to peak
        index20 = np.argmin([abs(x-twentyWinStart) for x in timeCycle]) #Find index of time closest to 20%
        PDAvel = max(velSlope[index20:filtMaxLoc+1]) #PDA velocity
        PDAloc = [i for i, x in enumerate(velSlope) if x == PDAvel][0] #PDA location
        
        #Diastolic velocity or beginning of diastolic phase (BD)
        fifteenCycle = (timeCycle[-1]-timeCycle[0]) * .075 #7.5% of total beat duration
        fifteenWinStart = timeCycle[PDAloc] - fifteenCycle #Time 7.5% prior to peak

        index15 = np.argmin([abs(x - fifteenWinStart) for x in timeCycle]) #Find index of time closest to %7.5
        DV1vel = min(filtEnvelope[index15:PDAloc+1]) #Decay velocity
        DV1time = timeCycle[[i for i, x in enumerate(filtEnvelope) if x == DV1vel][0]] #Decay velocity time
        
        #Peak diastolic deceleration (PDD)
        if filtMaxLoc + 10 < len(velSlope):
            PDDvel = min(velSlope[filtMaxLoc+10:])
            PDDloc = [i for i, x in enumerate(velSlope[filtMaxLoc+10:]) if x == PDDvel][0] + filtMaxLoc+10
        else:
            PDDvel = min(velSlope[filtMaxLoc:])
            PDDloc = [i for i, x in enumerate(velSlope[filtMaxLoc:]) if x == PDDvel][0] + filtMaxLoc
        PDDtime = timeCycle[PDDloc]
        PDDplot = filtEnvelope[PDDloc]
        
        #Decay velocity
        DV2zeros = np.nonzero(np.diff(np.sign(velSlope[1:PDDloc])))
        if len(DV2zeros[0]) <= 1:
            DV2loc = filtMaxLoc + round((PDDloc - filtMaxLoc)*.75)
        else:
            DV2loc = DV2zeros[-1][-1]
            if DV2zeros[-1][-1] <= filtMaxLoc+5:
                DV2loc = filtMaxLoc + round((PDDloc - filtMaxLoc)*.75)
        DV2loc = int(DV2loc)
        DV2time = timeCycle[DV2loc] #Decay velocity time
        DV2vel = filtEnvelope[DV2loc] #Decay velocity
        
        #Beginning of cycle
        begTime = timeCycle[0]
        begVel = filtEnvelope[0]
        
        #End of cycle
        endTime = timeCycle[len(velSlope)-1]
        endVel = filtEnvelope[len(velSlope)-1]
        
        #Calculate and store flow pattern parameters
        ##Note: [4 times, 4 slopes, 3 velocities, heart rate, VTI] for each cycle
        flowProperties.append([(DV1time-begTime)*1000, (PVtime-DV1time)*1000, (DV2time-PVtime)*1000, (endTime-DV2time)*1000, \
                               (DV1vel-begVel)/(DV1time-begTime), (filtMax-DV1vel)/(PVtime-DV1time), \
                               (DV2vel-filtMax)/(DV2time-PVtime), (endVel-DV2vel)/(endTime-DV2time), \
                               DV1vel, filtMax, DV2vel, bpm[count], integral])

        #Plot critical points
        plt.scatter([begTime/timePerPixel], [len(dopplerRegion)-begVel/velocityPerPixel], s=1, c='b')
        plt.scatter([DV1time/timePerPixel], [len(dopplerRegion)-DV1vel/velocityPerPixel], s=1, c='g')
        plt.scatter([PVtime/timePerPixel], [len(dopplerRegion)-filtMax/velocityPerPixel], s=1, c='y')
        plt.scatter([DV2time/timePerPixel], [len(dopplerRegion)-DV2vel/velocityPerPixel], s=1, c='m')
        plt.scatter([PDDtime/timePerPixel], [len(dopplerRegion)-PDDplot/velocityPerPixel], s=1, c='r')
        
        count += 1
        
    #Resize and display plot
    fig = plt.gcf()
    fig.set_size_inches(16, 4)
    figname = savefile[:-5] + '_' + str(countALL+1) + '.png'
    fig.savefig(figname, dpi=200)
    plt.show()
    
    #Create dataframe of calculated valyes
    data = np.around(flowProperties, 2)
    flowProp.append(data)
    parameters = pd.DataFrame({'Results':['Systolic Rise Time', 'Diastolic Rise Time', 'Diastolic Decay Time 1', \
                                          'Diastolic Decay Time 2', 'Systolic Slope', 'Diastolic Slope', 'Decay Slope 1', \
                                          'Decay Slope 2', 'Diastolic Velocity', 'Peak Velocity', 'Decay Velocity 1', \
                                          'Heart Rate', 'VTI']})
    
    #Calculate average of each parameter
    compareAvg = np.mean(data, axis = 0)
    count = 1
    for cycle in data:
        header = 'Cycle ' + str(count)
#        if cycle[9] > compareAvg[9] * 0.5:
        parameters[header] = cycle
#        else:
#            parameters[header] = ['unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative', 'unrepresentative']
        count += 1
    parameters['Average'] = np.mean(parameters, axis = 1)
    
    #Write results to excel file
    sheetnm = 'Video' + str(countALL)
    parameters.to_excel(w, sheet_name = sheetnm)
    
    vti_hr.append(parameters['Average'].iloc[-1] * parameters['Average'].iloc[-2])

    #END OF FOR LOOP
    countALL += 1

endTime = time.perf_counter() - startTime;
print('Doppler time: ' + str(endTime))
startTime = time.perf_counter()

###Colormode Analysis
if choice == 'Combined Analysis':
    #Baseline colormode
    colorDist = maxPen[0] - minPen[0]
    colorDist = round(colorDist, 2)
    colorParameters = colormode.analyse(filename[0], filenameCMode[0], colorDist, angleG[0], 0)
    colorPall.append(colorParameters)
    
    #Hyperemic colormode
    colorDist = maxPen[numBLVideos] - minPen[numBLVideos]
    colorDist = round(colorDist, 2)
    colorParameters = colormode.analyse(filename[numBLVideos], filenameCMode[1], colorDist, angleG[numBLVideos], 1)
    colorPall.append(colorParameters)
    
    #Write color parameters to excel file and calculate CBF
    colorDF = pd.DataFrame({'Results':['Number of Frames', 'Mode Diam', 'Freq mode', 'Max Diam', 'Min Diam', 'Mean Diam', 'Median Diam', 'Std Dev', 'CBF']})
    CBF = (vti_hr[0] * colorPall[0][5] * colorPall[0][5] * (math.pi/4))/1000
    colorPall[0].append(CBF)
    colorDF['Baseline'] = colorPall[0]
    CBF = (vti_hr[1] * colorPall[1][5] * colorPall[1][5] * (math.pi/4))/1000
    colorPall[1].append(CBF)
    colorDF['Hyperemic'] = colorPall[1]
    colorDF = colorDF.transpose()
    colorDF.to_excel(w, sheet_name = 'Color Mode')

w.save()
endTime = time.perf_counter() - startTime;
print('CMode time: ' + str(endTime))