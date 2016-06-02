import sys, pygame
import picamera
import time
from time import sleep
import os
import ConfigParser
import Image
from PIL import ImageFont
from PIL import ImageDraw
import eztext 
import cups
from threading import Thread
import math
import shutil
import driveFuncs
import httplib2
import os

from apiclient import discovery
from apiclient.http import MediaFileUpload

#check internet connection
internetOn = driveFuncs.internet_on()

#read settings file
config = ConfigParser.ConfigParser()
config.read('settings.txt')

#Settings:
printCollage = True
imagedir = 'photos_temp/'
archiveDir='prints/'
toUploadDir = 'notUploaded/'
countdown = int(config.get('settings','countdown'))#seconds for countdown
inDev = False 
showCaption = True
aspectRatio = 1.0*4/3

#Google Drive Settings
Gfolder = config.get('folders','driveFolder')
Gsub= config.get('folders','driveExt') + time.strftime("%Y_%m_%d")

#initialize camera
camera = picamera.PiCamera()
camera.preview_alpha = 130
camera.resolution = (1296,972)
camera.hflip = True
camera.sensor_mode = 4
    

#initialize background
pygame.init()
pygame.mouse.set_visible(False)
green = 0, 204, 0
red= 204,0,0
blue= 51,51,255
black = 32, 32, 32
white= 250,250,250
screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
(mon_w, mon_h) = screen.get_size()

def scaled(number):
    scaler = mon_h/1000.0
    value = int(number*scaler)
    return value
    
background = pygame.Surface((scaled(aspectRatio*1000),scaled(1000))) #Create the background object
background = background.convert() #Convert it to a background

#Create Folders if necessary
if not os.path.exists(imagedir): 
    os.makedirs(imagedir)

if internetOn:    
    if driveFuncs.folderSearch(Gfolder)=='':
        driveFuncs.insertFolder(Gfolder, '' )
    if driveFuncs.folderSearch(Gsub)=='':
        driveFolder = driveFuncs.insertFolder(Gsub, driveFuncs.folderSearch(Gfolder))
    else: driveFolder = driveFuncs.folderSearch(Gsub)
        
    #Upload toBeUploaded files
    if os.path.exists(toUploadDir):
        if driveFuncs.containsPrints(toUploadDir):
            for file in os.listdir(toUploadDir):
                if file.endswith(".jpg"):
                    driveFuncs.save2drive(os.path.join(toUploadDir,file), file, driveFolder)
            shutil.rmtree(toUploadDir, ignore_errors=True)
    
#Initialize variables
exitFlag=0
images=[]
lastPhoto="" 
lastCollage=""
showLastPhoto=False
showLastCollage=False
state = 0 #statemachine 
groupcounter = 1
imagecounter = 1
groupName=""
groupDescription=""
numPrints=""

smallfont = pygame.font.Font(None, scaled(50))
mediumfont = pygame.font.Font(None, scaled(100))
largefont = pygame.font.Font(None, scaled(250))
hugefont =pygame.font.Font(None, scaled(400))
    
####Functions
def startPreview():
    camera.start_preview()
    
#initialize/clear global variables
def clearScreen():
    global Message1, Message2, Message3, Message4
    global Numeral
    global textBox1, textBox2, textBox3
    global Title, oldTitle
    global updateRect
    global showLastPhoto, showLastCollage, showHorses, showCEEO
   
    Message1=Message2=Message3=Numeral=textBox1=textBox2=textBox3=Title=Message4= ""
    oldTitle=""
    updateRect= ()
    showLastPhoto = False
    showHorses = False
    showCEEO = False
    showLastCollage = False
    return

#Update background display
def UpdateDisplay():
    global background, updateRect, oldTitle
    background.unlock()
    background.fill(black)
    
    if inDev:
        stateIcon = smallfont.render(str(state),1, (0, 255,0))
        background.blit(stateIcon,(10,10))
    
    #if messages exist, print them to background
    if (Title != ""):
        tTitle = pygame.font.Font(None, scaled(80)).render(Title,1, green)
        textRect = tTitle.get_rect()
        textRect.centerx = background.get_rect().centerx
        textRect = textRect.move(0,scaled(200))
        background.blit(tTitle,textRect)
    if (textBox1 != ""):
        text = smallfont.render(textBox1,1, red)
        background.blit(text,(scaled(100),scaled(450)))
    if (textBox2 != ""):
        text = smallfont.render(textBox2,1, red)
        background.blit(text,(scaled(100),scaled(550)))
    if (textBox3 != ""):
        text = smallfont.render(textBox3,1, green)
        background.blit(text,(scaled(100),scaled(700))) 
    if (Message1 != ""):
        text = smallfont.render(Message1,1, green)
        background.blit(text,(scaled(200),scaled(200)))
    if (Message2 != ""):
        text = smallfont.render(Message2,1, green)
        background.blit(text,(scaled(200),scaled(300)))
    if (Message3 != ""):
        text = smallfont.render(Message3,1, green)
        background.blit(text,(scaled(200),scaled(600)))
    if (Message4 != ""):
        text = smallfont.render(Message4,1, green)
        textRect = text.get_rect()
        textRect.centerx = background.get_rect().centerx
        textRect = textRect.move(0,scaled(850))
        background.blit(text,textRect)
    if (Numeral != ""):
        text = hugefont.render(Numeral,1, (255,0,0))
        textRect = text.get_rect()
        textRect.centerx = background.get_rect().centerx
        textRect = textRect.move(0,scaled(400))
        background.blit(text,textRect)
    if (showLastPhoto):
        scale=0.4*mon_h/1000.0
        groupPic = pygame.image.load(lastPhoto)
        picSize = groupPic.get_rect()
        newWidth=int(picSize.size[0]*scale)
        newHeight=int(picSize.size[1]*scale)
        groupPic = pygame.transform.smoothscale(groupPic,(newWidth,newHeight))
        background.blit(groupPic,(scaled(800),scaled(50)))
    if (showLastCollage):
        scale=0.5*mon_h/1000.0
        collage = pygame.image.load(lastCollage)
        picRect = collage.get_rect()
        newWidth=int(picRect.size[0]*scale)
        newHeight=int(picRect.size[1]*scale)
        collage = pygame.transform.smoothscale(collage,(newWidth,newHeight))
        collageRect = collage.get_rect()
        collageRect.center = background.get_rect().center
        collageRect =collageRect.move(0,scaled(-200))
        background.blit(collage,collageRect)
    if (showHorses):
        scale=0.5*mon_h/1000.0
        collage = pygame.image.load('holdhorses.png')
        picRect = collage.get_rect()
        newWidth=int(picRect.size[0]*scale)
        newHeight=int(picRect.size[1]*scale)
        collage = pygame.transform.smoothscale(collage,(newWidth,newHeight))
        collageRect = collage.get_rect()
        collageRect.center = background.get_rect().center
        collageRect =collageRect.move(0,scaled(200))
        background.blit(collage,collageRect)
    if (showCEEO):
        scale=0.5*mon_h/1000.0
        collage = pygame.image.load('CEEO.png')
        picRect = collage.get_rect()
        newWidth=int(picRect.size[0]*scale)
        newHeight=int(picRect.size[1]*scale)
        collage = pygame.transform.smoothscale(collage,(newWidth,newHeight))
        collageRect = collage.get_rect()
        collageRect.center = background.get_rect().center
        collageRect =collageRect.move(0,scaled(300))
        background.blit(collage,collageRect)
        
    #screen.blit(fit2screen(background), (0,0)) #print backgroud
    blit2screen(background)
    if updateRect == ():
        pygame.display.update()
    else: pygame.display.update(updateRect) #update screen
    return

def blit2screen(surface):
    global mon_w, mon_h, aspectRatio
    wzero=0
    hzero=0
    if mon_w > aspectRatio*mon_h:
        wzero=(mon_w-int(aspectRatio*mon_h))/2
    else:
        hzero=(mon_h-int(mon_w/aspectRatio))/2
    screen.blit(surface, (wzero,hzero))
    return 

def takePicture():
    global images, lastPhoto
    global imagecounter
      
    filename = 'image'+ `imagecounter` + '.jpg'
    camera.capture(os.path.join(imagedir,filename)) #take/save photo
    camera.stop_preview()
    images.append(Image.open(os.path.join(imagedir,filename)).transpose(Image.FLIP_LEFT_RIGHT)) #save image object for compiling
    lastPhoto = os.path.join(imagedir,filename)
    imagecounter +=1
    return


def AssAndPrint(): #assembles collage and prints it
#    global Message1, Message2
    global images, lastCollage, showCaption
    thumbs= []
    
    UpdateDisplay()
    #new grid to print
    pheight=1000
    pwidth = 1500 #int(round(pheight*1.5))
    
    if showCaption:
        if groupName == "" and groupDescription == "":
            captionOn = False
        else: captionOn = True
        if groupName == "" or groupDescription == "":
            dash = ""
        else: dash = " - "
        
    if captionOn: 
        iheight = 450
        iwidth = int(iheight*640/480) 
        offset = 640-iwidth
        border = 10
        forPrint = Image.new("RGB", (pwidth, pheight), "white")
        title = Image.open('general.jpg')
        title=title.rotate(90)
        title.thumbnail((1000,1000))
        
        for i in range (1,5):
            images[i].thumbnail((iwidth,iheight))
            
        forPrint.paste(images[1],(offset+20,10))
        forPrint.paste(images[2],(offset+20,30+iheight))
        forPrint.paste(images[3],(offset+40+iwidth,10))
        forPrint.paste(images[4],(offset+40+iwidth,30+iheight))
        forPrint.paste(title,(offset+50+iwidth*2,10)) 
        
        font = ImageFont.truetype('Verdana.ttf', 35)
        draw = ImageDraw.Draw(forPrint)
        draw.text((offset+20, 930),groupName + dash + groupDescription,(0,0,0),font=font)
        
    else:
        iwidth = 400 
        iheight = 480 
        border = 10

        forPrint = Image.new("RGB", (pwidth, pheight), "white")
        title = Image.open('general.jpg')
        title.thumbnail((1000,1000))
        title=title.rotate(90)
        #thumbnail the 4 images 
        for i in range (1,5):
            images[i].thumbnail((640,480))

        forPrint.paste(images[1],(20,10))
        forPrint.paste(images[2],(20,30+480))
        forPrint.paste(images[3],(40+640,10))
        forPrint.paste(images[4],(40+640,30+480))
        forPrint.paste(title,(50+640*2,10))
    
    if not os.path.exists(archiveDir): 
        os.makedirs(archiveDir)
    
        
    archivename = 'PB'+time.strftime("%Y%m%d_%H%M") + '.jpg'
    forPrint.save(archiveDir+archivename) #save to Archive folder
    lastCollage = os.path.join(archiveDir,archivename)
    
    if internetOn:
        driveFuncs.save2drive(archiveDir+archivename, archivename, driveFolder)
    else: 
        if not os.path.exists(toUploadDir): 
            os.makedirs(toUploadDir)
        forPrint.save(toUploadDir+archivename)
        
    #Dumb printer crops a bit fix
    extra = 30
    fheight=int(pheight+extra)
    fwidth=int(fheight*1.5)
    cropPrint = Image.new("RGB", (fwidth, fheight), "white")
    cropPrint.paste(forPrint,(int(.75*extra),int(.5*extra)))
    cropPrint.save(archiveDir+'temp.jpg')
    return
   
def sendToPrinter():
    global numPrints
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = printers.keys()[0]
    
    if numPrints != 0:
        conn.printFile(printer_name,archiveDir+'temp.jpg',"PhotoBooth",{"copies": str(numPrints)})
    return

def timer():
    global Numeral 
    for j in range (countdown, 0, -1):
        Numeral = str(j)
        UpdateDisplay()
        sleep(1)
    Numeral = '0'
    UpdateDisplay()
    sleep(.1)
    Numeral=""
    UpdateDisplay()
    return

def capture():
    startPreview()
    timer()
    clearScreen()
    UpdateDisplay()
    takePicture()
    camera.stop_preview()
    return

#Main Script 
def main(threadName, *args):
    #call globals
    global Title, Message1, Message2, Message3, Message4, state, showLastPhoto, showLastCollage, updateRect, showHorses, showCEEO 
    global numPrints, groupName, groupDescription
    clock = pygame.time.Clock() 
    
        
    clearScreen()
    while not exitFlag:
        clock.tick(30)
#        ms=clock.get_time()
#        if ms > 500: print str(ms) + ' ' + str(state)
            
        if state == 0: #Welcome screen
            sleep(.05)
            Title = "Welcome to the Documentation Photobooth!"
            Message2 = "Press spacebar to get started"
            showCEEO= True 
        elif state == 1: #Take sample pic
            clearScreen()
            Message1=config.get('prompts','prompt0')
            UpdateDisplay()
            sleep(1)
            capture()
            state = 2.1; clearScreen()
        elif int(state)==2: #Get user info
            if state == 2.1:
                Message1="Tell me about about you!"
                showLastPhoto= True
                UpdateDisplay()
                showLastPhoto= False
                updateRect = pygame.Rect(0,scaled(400),scaled(2000),scaled(800))
                state =2.2 
            
            if state==2.4: 
                Message3 = "Great!"
                print(groupName, groupDescription)
                UpdateDisplay()
                sleep(2)
                clearScreen()
                state=3.1
        elif int(state) ==3: #take more photos
            if state == 3.1:
                Message1="Now Lets Take Some Pictures of You and Your Project!"
                UpdateDisplay()
                sleep(3)
                Message1=config.get('prompts','prompt1')
                UpdateDisplay()
                sleep(2)
                capture() 
                state = 3.2
            elif state ==3.2:
                Message1=config.get('prompts','prompt2')
                UpdateDisplay()
                sleep(2)
                capture()
                state=3.3
            elif state ==3.3:
                Message1=config.get('prompts','prompt3')
                UpdateDisplay()
                sleep(2)
                capture() 
                state=3.4; 
            elif state ==3.4:
                Message1=config.get('prompts','prompt4')
                UpdateDisplay()
                sleep(2)
                capture() 
                state=3.5; 
            elif state==3.5: state = 4.1; clearScreen()
        elif int(state) == 4:
            if state == 4.1:
                Message1="Compiling Photos"
                Message2="So, hold your horses"
                
                showHorses = True
                UpdateDisplay()
                AssAndPrint()
                clearScreen()
                if not printCollage: 
                    Message4="Printing Currently disabeld. Click SpaceBar to restart"
                    state = 4.5
                else: state = 4.2 #Message4="Sent to Printer. Click SpaceBar to restart"
                showLastCollage= True
                UpdateDisplay()
                showLastCollage= False
                updateRect=(0,scaled(650),scaled(1300),scaled(500))
            if state == 4.3:
                if 'True' == config.get('settings','send2printer'): 
                    sendToPrinter()
                    print 'no print'
                Message4="Sent to Printer. Click SpaceBar to restart"
                state=4.5
                
                
        UpdateDisplay()
        
def watchInput(threadName, *args):
    global Message3, exitFlag, state, textBox1, textBox2,textBox3, groupcounter, imagecounter, images
    global groupName, groupDescription, numPrints
    txtbx = eztext.Input(maxlength=45, prompt='title')
    clock = pygame.time.Clock() 
    
    while not exitFlag:
        clock.tick(30)
        ms=clock.get_time()
        if ms > 500: print str(ms) + ' ' + str(state)
        events = pygame.event.get()
        
        for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        exitFlag=1
                    if event.key == pygame.K_SPACE:
                        if state ==0: 
                            state = 1 
                            clearScreen() 
                        if state==4.5:
                            clearScreen()
                            sleep(.1)
                            groupcounter+=1 
                            imagecounter=1
                            images=[]
                            state =0 
                    if event.key == pygame.K_RETURN:
                        if state ==2.2: 
                            state = 2.3
                            groupName = txtbx.value
                            txtbx.value=""
                        elif state ==2.3: 
                            state = 2.4
                            groupDescription = txtbx.value
                            txtbx.value=""
                        elif state ==4.2:
                            state = 4.3
                            if '1' in txtbx.value:
                                numPrints = 1
                            elif '2' in txtbx.value:
                                numPrints = 2
                            elif '3' in txtbx.value:
                                numPrints = 3
                            elif '0' in txtbx.value:
                                numPrints = 0
                            else: numPrints=1
                            txtbx.value=""
                            textBox3=""
                            print str(numPrints) + ' prints'
                            
                            UpdateDisplay()
        if state ==2.2:
            txtbx.update(events)
            textBox1='Your Name(s): '+txtbx.value
        elif state == 2.3:
            txtbx.update(events)
            textBox2='Description of Project: '+txtbx.value
        elif state == 4.2:
            txtbx.update(events)
            textBox3='Quantity of Prints? (type 0, 1, 2, 3):     '+txtbx.value
    
                                                
#start Threads

Thread(target=watchInput, args=('WatchInput', 1)).start()
Thread(target=main, args=('Main',1)).start()
