from machine import Pin, SPI # SPI is a class associated with the machine library. 
# The below specified libraries have to be included. Also, ssd1306.py must be saved on the Pico. 
from ssd1306 import SSD1306_SPI # this is the driver library and the corresponding class
import framebuf # this is another library for the display. 
from machine import Pin, I2C
import time
import utime

class Radio:
    
    def __init__( self, NewFrequency, NewVolume, NewMute ):

#
# set the initial values of the radio
#
        self.Volume = 2
        self.Frequency = 88
        self.Mute = False
#
# Update the values with the ones passed in the initialization code
#
        self.SetVolume( NewVolume )
        self.SetFrequency( NewFrequency )
        self.SetMute( NewMute )
        
      
# Initialize I/O pins associated with the radio's I2C interface

        self.i2c_sda = Pin(26)
        self.i2c_scl = Pin(27)

#
# I2C Device ID can be 0 or 1. It must match the wiring. 
#
# The radio is connected to device number 1 of the I2C device
#
        self.i2c_device = 1 
        self.i2c_device_address = 0x10

#
# Array used to configure the radio
#
        self.Settings = bytearray( 8 )


        self.radio_i2c = I2C( self.i2c_device, scl=self.i2c_scl, sda=self.i2c_sda, freq=200000)
        self.ProgramRadio()

    def SetVolume( self, NewVolume ):
#
# Conver t the string into a integer
#
        try:
            NewVolume = int( NewVolume )
            
        except:
            return( False )
        
#
# Validate the type and range check the volume
#
        if ( not isinstance( NewVolume, int )):
            return( False )
        
        if (( NewVolume < 0 ) or ( NewVolume >= 16 )):
            return( False )

        self.Volume = NewVolume
        return( True )



    def SetFrequency( self, NewFrequency ):
#
# Convert the string into a floating point value
#
        try:
            NewFrequency = float( NewFrequency )
            
        except:
            return( False )
#
# validate the type and range check the frequency
#
        if ( not ( isinstance( NewFrequency, float ))):
            return( False )
 
        if (( NewFrequency < 88.0 ) or ( NewFrequency > 108.0 )):
            return( False )

        self.Frequency = NewFrequency
        return( True )
        
    def SetMute( self, NewMute ):
        
        try:
            self.Mute = bool( int( NewMute ))
            
        except:
            return( False )
        
        return( True )

#
# convert the frequency to 10 bit value for the radio chip
#
    def ComputeChannelSetting( self, Frequency ):
        Frequency = int( Frequency * 10 ) - 870
        
        ByteCode = bytearray( 2 )
#
# split the 10 bits into 2 bytes
#
        ByteCode[0] = ( Frequency >> 2 ) & 0xFF
        ByteCode[1] = (( Frequency & 0x03 ) << 6 ) & 0xC0
        return( ByteCode )

#
# Configure the settings array with the mute, frequency and volume settings
#
    def UpdateSettings( self ):

        self.Settings = bytearray( 8 )

        if ( self.Mute ):
            self.Settings[0] = 0x80
        else:
            self.Settings[0] = 0xC0

        self.Settings[1] = 0x09 | 0x04
        self.Settings[2:3] = self.ComputeChannelSetting( self.Frequency )
        self.Settings[3] = self.Settings[3] | 0x10
        self.Settings[4] = 0x04
        self.Settings[5] = 0x00
        self.Settings[6] = 0x84
        self.Settings[7] = 0x80 + self.Volume

        self.Settings = self.Settings[:8]
#        
# Update the settings array and transmitt it to the radio
#
    def ProgramRadio( self ):

        self.UpdateSettings()
        self.radio_i2c.writeto( self.i2c_device_address, self.Settings )

#
# Extract the settings from the radio registers
#
    def GetSettings( self ):
#        
# Need to read the entire register space. This is allow access to the mute and volume settings
# After and address of 255 the 
#
        self.RadioStatus = self.radio_i2c.readfrom( self.i2c_device_address, 256 )

        if (( self.RadioStatus[0xF0] & 0x40 ) != 0x00 ):
            MuteStatus = False
        else:
            MuteStatus = True
            
        VolumeStatus = self.RadioStatus[0xF7] & 0x0F
 
 #
 # Convert the frequency 10 bit count into actual frequency in Mhz
 #
        FrequencyStatus = (( self.RadioStatus[0x00] & 0x03 ) << 8 ) | ( self.RadioStatus[0x01] & 0xFF )
        FrequencyStatus = ( FrequencyStatus * 0.1 ) + 87.0
        
        if (( self.RadioStatus[0x00] & 0x04 ) != 0x00 ):
            StereoStatus = True
        else:
            StereoStatus = False
        
        return( MuteStatus, VolumeStatus, FrequencyStatus, StereoStatus )

#
# initialize the FM radio
#
fm_radio = Radio( 101.9, 2, False ) # set the initialized frequency to the local radio station to 101.9


# Define columns and rows of the oled display. These numbers are the standard values. 
SCREEN_WIDTH = 128 #number of columns
SCREEN_HEIGHT = 64 #number of rows


# Initialize I/O pins associated with the oled display SPI interface

spi_sck = Pin(18) # sck stands for serial clock; always be connected to SPI SCK pin of the Pico
spi_sda = Pin(19) # sda stands for serial data;  always be connected to SPI TX pin of the Pico; this is the MOSI
spi_res = Pin(21) # res stands for reset; to be connected to a free GPIO pin
spi_dc  = Pin(20) # dc stands for data/command; to be connected to a free GPIO pin
spi_cs  = Pin(17) # chip select; to be connected to the SPI chip select of the Pico 

#
# SPI Device ID can be 0 or 1. It must match the wiring. 
#
SPI_DEVICE = 0 # Because the peripheral is connected to SPI 0 hardware lines of the Pico

#
# initialize the SPI interface for the OLED display
#
oled_spi = SPI( SPI_DEVICE, baudrate= 100000, sck= spi_sck, mosi= spi_sda )

#
# Initialize the display
#
oled = SSD1306_SPI( SCREEN_WIDTH, SCREEN_HEIGHT, oled_spi, spi_dc, spi_res, spi_cs, True )


# Config the 3 buttons
btnSelect = machine.Pin(0,machine.Pin.IN,machine.Pin.PULL_UP)
btnDown = machine.Pin(1,machine.Pin.IN,machine.Pin.PULL_UP)
btnUp = machine.Pin(2,machine.Pin.IN,machine.Pin.PULL_UP)

# software debounce for buttons
prev_states = {}
def debounce(btn):
    cur = btn.value()

    if btn not in prev_states:
        prev_states[btn] = cur

    if cur != prev_states[btn]:
        prev_states[btn] = cur

        if cur == 0:
            utime.sleep_ms(30)

            if btn.value() == 0: 
                return 0

    return 1

selectedMenu = 0
currentMenu = 0

clockMenu = 0
radioMenu = 1
freqMenu = 2
volMenu = 3
readMenu = 4
goBack = 5


count = 0
#Configure Display for radio settings
def displayRadioSettings():
    global selectedMenu
    
    oled.text("Radio Settings",10,0)
    
    # Make the cursor loop around list
    if selectedMenu < 0:
        selectedMenu = 3
    elif selectedMenu > 3:
        selectedMenu = 0
    
    if selectedMenu == 0:
        oled.fill_rect(0,18,128,11,1)
        oled.text("Change Frequency", 0,20,0)
    else:
        oled.text("Change Frequency",0,20)
    
    if selectedMenu == 1:
        oled.fill_rect(0,28,128,11,1)
        oled.text("Change Volume",0,30,0)
    else:
        oled.text("Change Volume",0,30)
    
    if selectedMenu == 2:
        oled.fill_rect(0,38,128,11,1)
        oled.text("Read Settings", 0,40,0)
    else:
        oled.text("Read Settings",0,40)
        
    if selectedMenu ==3:
        oled.fill_rect(0,48,128,11,1)
        oled.text("Go Back", 0,50,0)
    else:
        oled.text("Go Back",0,50)

def displayClock():
    localTime = utime.localtime()
    year = localTime[0]
    month = localTime[1]
    DOM = localTime[2]
    hour = localTime[3]
    minute = localTime[4]
    second = localTime[5]
    weekday = localTime[6]

    oled.text("%02d:%02d:%02d"%(hour, minute, second), 35, 20)
    oled.text("%02d/%02d/%02d"%(DOM,month,year),25,30)
    oled.fill_rect(8,43,120,10,1) # (start coordinate x, y, width, height, B/W)
    oled.text("Radio Settings",10,45,0)
"""   
def displayFreqSettings():
    global selectedMenu
    oled.text("Change Frequency",0, 0)
 
    if selectedMenu == 0:
        oled.fill_rect(19,24,80,10,1)
        oled.text("%.1f MHz"%fm_radio.Frequency,20,25,0)
    else:
        oled.text("%.1f MHz"%fm_radio.Frequency,20,25)

    if selectedMenu == 1:
        oled.fill_rect(29,54,60,10,1)
        oled.text("Go Back", 30,55,0)
    else:
        oled.text("Go Back", 30,55)
"""      
def displayFreqSettings():
    oled.text("Up/Down to", 0,0)
    oled.text("change frequency",0,10)
    oled.fill_rect(19,29,80,10,1)
    oled.text("%.1f MHz"%fm_radio.Frequency,20,30,0)
    
    oled.text("Press select",0,45)
    oled.text("to save",0,55)

def displayVolSettings():
    oled.text("Up/Down to", 0,0)
    oled.text("change volume", 0,10)
    oled.fill_rect(48,29,30,10,1)
    oled.text("%2d"%fm_radio.Volume,50,30,0)
    
    oled.text("Press select",0,45)
    oled.text("to save",0,55)
    
def displayAllSettings():
    oled.text("Volume: %2d"%fm_radio.Volume,0,0)
    oled.text("Frequency:%.1f"%fm_radio.Frequency,0,10)
    
    oled.fill_rect(29,49,60,10,1)
    oled.text("Go back", 30, 50, 0)

while ( True ):
    oled.fill(0)
    
    # Control Clock Menu
    if currentMenu == clockMenu or currentMenu == goBack:
        displayClock()
        if debounce(btnSelect) == 0:
            selectedMenu = 0
            currentMenu = radioMenu

    # Control Radio Menu
    if currentMenu == radioMenu:
        displayRadioSettings()
        
        if debounce(btnUp) == 0:
            selectedMenu = selectedMenu - 1
        if debounce(btnDown) ==0:
            selectedMenu = selectedMenu + 1
        
        if debounce(btnSelect) == 0:
            currentMenu = selectedMenu + 2
            selectedMenu = 0
    
    # Control Frequency Menu
    # To do: make it scan up/down to next station
    if currentMenu == freqMenu:
        displayFreqSettings()
        
        if debounce(btnUp) == 0:
            if fm_radio.Frequency < 108.0:
                fm_radio.SetFrequency(fm_radio.Frequency+0.1)
                fm_radio.ProgramRadio()
        
        if debounce(btnDown) == 0:
            if fm_radio.Frequency > 88.0:
                fm_radio.SetFrequency(fm_radio.Frequency-0.1)
                fm_radio.ProgramRadio()
        
        if debounce(btnSelect) == 0:
            currentMenu = radioMenu
            selectedMenu = 0
    
    # Control Volume Menu
    # To do: implement the mute function when volume reaches 0
    if currentMenu == volMenu:
        displayVolSettings()
            
        if debounce(btnUp) == 0:
            if fm_radio.Volume < 15:
                fm_radio.SetVolume(fm_radio.Volume + 1)
                fm_radio.ProgramRadio()
        
        if debounce(btnDown) ==0:
            if fm_radio.Volume >0:
                fm_radio.SetVolume(fm_radio.Volume - 1)
                fm_radio.ProgramRadio()
                
        if debounce(btnSelect) == 0:
            currentMenu = radioMenu
            selectedMenu = 0
    
    # Display all settings and give option to "go back" 
    if currentMenu == readMenu:
        displayAllSettings()
        
        if debounce(btnSelect) == 0:
            currentMenu = radioMenu
            selectedMenu = 0
          
    oled.show()


