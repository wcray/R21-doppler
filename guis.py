##########################################################################
# Author: Jamie Bossenbroek
# Date: 7/12/19
#
# This function contains the GUI selection tools used in the cbf.py program:
#   Method(): the user chooses their method of analysis
#   DataEntry(): the user inputs probe angle, max velocity, and min and max probe penetration 
#   ScrollTest(): check if the automated doppler envelope is acceptable
#
##########################################################################


import tkinter, cv2, vevoAVIparser
from PIL import Image, ImageTk


class Num():
    def __init__(self, master, num):
        self.master = master
        master.title("Enter number of videos to analyze")
        self.num = 0
        
        #Set window size and position
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        self.master.geometry("320x100+%d+%d" % (screen_width/2-160, screen_height/4))
        
        #Number entry
        if num == 1:
            tkinter.Label(master, text = "Number of baseline Doppler videos:").pack()
        else:
            tkinter.Label(master, text = "Number of hyperemic Doppler videos:").pack()
        self.e1 = tkinter.Entry(master)
        self.e1.pack()
  
        #Save and exit
        tkinter.Button(master, text = "Save", command = self.end).pack()
        master.bind('<Return>', self.end) #Bind enter key to button
        
    def end(self, _event=None):
        self.num = self.e1.get()
        self.master.destroy()

        
        
class Method():
    def __init__(self, master):
        self.master = master
        master.title("Choose Method of Analysis")
        
        #Set window size and position
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        self.master.geometry("320x100+%d+%d" % (screen_width/2-160, screen_height/4))
        
        #Buttons for method selection
        tkinter.Button(master, text = "Doppler Flow Pattern Analysis", command = self.choice1).pack()
        master.bind('d', self.choice1) #Bind key to button
        tkinter.Button(master, text = "Combined Analysis", command = self.choice2).pack()
        master.bind('c', self.choice2) #Bind key to button
        
        #String variable to store and display choice
        self.choice = ''
        self.labelText = tkinter.StringVar()
        self.labelText.set('Selection: ')
        tkinter.Label(master, textvariable = self.labelText).pack()
        
        #Save choice and exit
        tkinter.Button(master, text = "Save", command = self.end).pack()
        master.bind('<Return>', self.end) #Bind enter key to button
        
    def choice1(self, _event=None):
        self.choice = 'Doppler Flow Pattern Analysis'
        self.labelText.set('Selection: ' + self.choice)
    def choice2(self, _event=None):
        self.choice = 'Combined Analysis'
        self.labelText.set('Selection: ' + self.choice)
    def end(self, _event=None):
        self.master.destroy()        
        

        
class DataEntry():
    def __init__(self, master, bl, h, choice):
        self.master = master
        self.bl = bl
        self.h = h
        self.cmode = choice == 'Combined Analysis'
        master.title("Input Parameters")
        
        #Parameters to be input
        self.Velocity_Max = []
        self.VAngleG = []
        self.Max_Pen = []
        self.Min_Pen = []
        
        #Screen and picture size
        screen_width = master.winfo_screenwidth()
        pic_width = int(3*screen_width/7)
        pic_height = int(pic_width/1.5)
        
        if bl:
            #Display first image from doppler file
            image = vevoAVIparser.firstImage(bl)
            imageBL = Image.fromarray(image)
            imageBL = imageBL.resize((pic_width, pic_height), Image.ANTIALIAS)
            self.dispBL = ImageTk.PhotoImage(imageBL)
            self.ArtworkBL = tkinter.Label(master, image = self.dispBL)
            self.ArtworkBL.photo = self.dispBL
        
            tkinter.Label(master, text = "Baseline Doppler", font = 'Helvetica 18 bold').grid(row = 0, columnspan = 2)
            self.ArtworkBL.grid(row = 1, columnspan = 2)
            tkinter.Label(master, text = "Max Velocity on y-axis (mm/s):").grid(row = 2)
            self.e1 = tkinter.Entry(master)
            self.e1.grid(row = 2, column = 1)
            #Color mode parameters
            if self.cmode:
                tkinter.Label(master, text = "Angle of Probe from Verticle (degrees):").grid(row = 3)
                self.e2 = tkinter.Entry(master)
                self.e2.grid(row = 3, column = 1)
                tkinter.Label(master, text = "Max Penetration Depth (mm):").grid(row = 4)
                self.e3 = tkinter.Entry(master)
                self.e3.grid(row = 4, column = 1)
                tkinter.Label(master, text = "Min Penetration Depth (mm):").grid(row = 5)
                self.e4 = tkinter.Entry(master)
                self.e4.grid(row = 5, column = 1)
        if h:
            #Display first image from hyperemic file
            image = vevoAVIparser.firstImage(h)
            imageH = Image.fromarray(image)
            imageH = imageH.resize((pic_width, pic_height), Image.ANTIALIAS)
            self.dispH = ImageTk.PhotoImage(imageH)
            self.ArtworkH = tkinter.Label(master, image = self.dispH)
            self.ArtworkH.photo = self.dispH
            
            tkinter.Label(master, text = "Hyperemic Doppler", font = 'Helvetica 18 bold').grid(row = 0, column = 2, columnspan = 2)
            self.ArtworkH.grid(row = 1, column = 2, columnspan = 2)
            tkinter.Label(master, text = "Max Velocity on y-axis (mm/s):").grid(row = 2, column = 2)
            self.e5 = tkinter.Entry(master)
            self.e5.grid(row = 2, column = 3)
            #Color mode parameters
            if self.cmode:
                tkinter.Label(master, text = "Angle of Probe from Verticle (degrees):").grid(row = 3, column = 2)
                self.e6 = tkinter.Entry(master)
                self.e6.grid(row = 3, column = 3)
                tkinter.Label(master, text = "Max Penetration Depth (mm):").grid(row = 4, column = 2)
                self.e7 = tkinter.Entry(master)
                self.e7.grid(row = 4, column = 3)
                tkinter.Label(master, text = "Min Penetration Depth (mm):").grid(row = 5, column = 2)
                self.e8 = tkinter.Entry(master)
                self.e8.grid(row = 5, column = 3)
         
        #Return input values and exit
        tkinter.Button(master, text = "Enter", command = self.get_values, height = 5, width = 20).grid(row = 6, column = 3)
        master.bind('<Return>', self.get_values) #Bind enter key to button
            
    def get_values(self, _event=None):
        if self.bl:
            self.Velocity_Max.append(self.e1.get())
            if self.cmode:
                self.VAngleG.append(self.e2.get())
                self.Max_Pen.append(self.e3.get())
                self.Min_Pen.append(self.e4.get())
        if self.h:
            self.Velocity_Max.append(self.e5.get())
            if self.cmode:
                self.VAngleG.append(self.e6.get())
                self.Max_Pen.append(self.e7.get())
                self.Min_Pen.append(self.e8.get())
        self.master.destroy()
        
        
        
class DataEntryOne():
    def __init__(self, master, bl, choice):
        self.master = master
        self.bl = bl
        self.cmode = choice == 'Combined Analysis'
        master.title("Input Parameters")
        self.Velocity_Max = 0
        self.VAngleG = 0
        self.Max_Pen = 0
        self.Min_Pen = 0
        
        #Screen and picture size
        screen_width = master.winfo_screenwidth()
        pic_width = int(3*screen_width/7)
        pic_height = int(pic_width/1.5)
        
        #Display first image from doppler file
        image = vevoAVIparser.firstImage(bl)
        imageBL = Image.fromarray(image)
        imageBL = imageBL.resize((pic_width, pic_height), Image.ANTIALIAS)
        self.dispBL = ImageTk.PhotoImage(imageBL)
        self.ArtworkBL = tkinter.Label(master, image = self.dispBL)
        self.ArtworkBL.photo = self.dispBL
    
        tkinter.Label(master, text = "Doppler Video", font = 'Helvetica 18 bold').grid(row = 0, columnspan = 2)
        self.ArtworkBL.grid(row = 1, columnspan = 2)
        tkinter.Label(master, text = "Max Velocity on y-axis (mm/s):").grid(row = 2)
        self.e1 = tkinter.Entry(master)
        self.e1.grid(row = 2, column = 1)
        if self.cmode:
                tkinter.Label(master, text = "Angle of Probe from Verticle (degrees):").grid(row = 3)
                self.e2 = tkinter.Entry(master)
                self.e2.grid(row = 3, column = 1)
                tkinter.Label(master, text = "Max Penetration Depth (mm):").grid(row = 4)
                self.e3 = tkinter.Entry(master)
                self.e3.grid(row = 4, column = 1)
                tkinter.Label(master, text = "Min Penetration Depth (mm):").grid(row = 5)
                self.e4 = tkinter.Entry(master)
                self.e4.grid(row = 5, column = 1)
         
        #Return input values and exit
        tkinter.Button(master, text = "Enter", command = self.get_values, height = 5, width = 20).grid(row = 6, column = 1)
        master.bind('<Return>', self.get_values) #Bind enter key to button
        
    def get_values(self, _event=None):
        self.Velocity_Max = self.e1.get()
        if self.cmode:
                self.VAngleG = self.e2.get()
                self.Max_Pen = self.e3.get()
                self.Min_Pen = self.e4.get()
        self.master.destroy()
        


class ScrollTest():
    def __init__(self, master, automaticThreshold, otsuImage, blurredImage):
        self.master = master
        master.title("Scroll Test")
        self.blurredImage = blurredImage
        self.automaticThresh = automaticThreshold
        self.threshold = automaticThreshold
        
        #Set window position and picture size
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        self.pic_width = int(screen_width * .9)
        self.pic_height = int(self.pic_width * len(otsuImage)/len(otsuImage[0]))
        self.master.geometry("+%d+%d" % (screen_width/2-self.pic_width/2, screen_height/4))
        
        tkinter.Label(master, text = "Proceed with automated threshold or threshold image manually?").grid(row = 0, columnspan = 2)
        
        #Automatic threshold 
        tkinter.Button(master, text = "Use Automatic Threshold", command = self.automatic).grid(row = 1, columnspan = 2)
        tkinter.Label(master, text = "Automatic Threshold: " + str(self.automaticThresh)).grid(row = 2, columnspan = 2)
        master.bind('<Return>', self.automatic) #Bind enter key to button
        
        otsuImage = Image.fromarray(otsuImage)
        otsuImage = otsuImage.resize((self.pic_width, self.pic_height), Image.ANTIALIAS)
        self.otsu = ImageTk.PhotoImage(otsuImage)
        self.Artwork = tkinter.Label(master, image = self.otsu)
        self.Artwork.photo = self.otsu
        self.Artwork.grid(row = 3, columnspan = 2)
        
        #Manual threshold
        tkinter.Button(master, text = "Use Manual Threshold", command = self.manual).grid(row = 4, columnspan = 2)
        self.labelText = tkinter.StringVar()
        self.labelText.set('Manual threshold: ' + str(self.threshold))
        tkinter.Label(master, textvariable = self.labelText).grid(row = 5, columnspan = 2)
        
        #Increase or decrease threshold
        tkinter.Button(master, text = "+", command = self.increase, height = 2, width = 5).grid(row = 6, column = 1)
        master.bind('+', self.increase)
        tkinter.Button(master, text = "-", command = self.decrease, height = 2, width = 5).grid(row = 6, column = 0)
        master.bind('-', self.decrease)
        
        #Display manual threshold
        tkinter.Button(master, text="Display manual threshold", command = self.manualImage).grid(row = 7, columnspan = 2)
        master.bind('<space>', self.manualImage)
        
    def increase(self, _event=None):
        self.threshold += 1
        self.labelText.set('Manual threshold: ' + str(self.threshold))
    def decrease(self, _event=None):
        self.threshold -= 1
        self.labelText.set('Manual threshold: ' + str(self.threshold))
    def manualImage(self, _event=None):
        #Manual threshold image
        thresh, img = cv2.threshold(self.blurredImage, self.threshold, 255, cv2.THRESH_BINARY)
        img = Image.fromarray(img)
        img = img.resize((self.pic_width, self.pic_height), Image.ANTIALIAS)
        self.manualImage = ImageTk.PhotoImage(img)
        self.ArtworkM = tkinter.Label(self.master, image = self.manualImage)
        self.ArtworkM.photo = self.manualImage
        self.ArtworkM.grid(row = 8, columnspan = 2)
    def automatic(self, _event=None):
        self.threshold = self.automaticThresh
        self.master.destroy()
    def manual(self, _event=None):
        self.master.destroy()
