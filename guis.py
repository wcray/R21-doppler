##########################################################################
# Author: Jamie Bossenbroek
# Date: 7/16/21
#
# This function contains the GUI selection tools used in the cbf.py program:
#   Method(): the user chooses their method of analysis
#   DataEntry(): the user inputs probe angle, max velocity, and min and max probe penetration 
#   ScrollTest(): check if the automated doppler envelope is acceptable
#
##########################################################################


import tkinter, cv2
from PIL import Image, ImageTk

    
        
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
        if self.choice:
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
