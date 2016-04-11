import struct
import spidev
import time
import RPi.GPIO as GPIO
import sys

# based on:
#  - libs from github:
#    - c++ https://github.com/adafruit/Adafruit-SSD1331-OLED-Driver-Library-for-Arduino
#  - SSD1331 manual: https://www.adafruit.com/datasheets/SSD1331_1.2.pdf
# Danger! many libs in python replicated this same bugs ( using normal gpio.out pin as CS pin, not dedicated to spi) 
# 
SSD1331_SCREEN_WIDTH  = 0x5F # from 0 to real_width - 1
SSD1331_SCREEN_HEIGHT = 0x3F
    
class SSD1331:

    
    # SSD1331 Commands
    CMD_DRAWLINE        = 0x21
    CMD_DRAWRECT        = 0x22
    CMD_FILL            = 0x26
    CMD_SETCOLUMN       = 0x15
    CMD_SETROW          = 0x75
    CMD_CONTRAST_A      = 0x81
    CMD_CONTRAST_B      = 0x82
    CMD_CONTRAST_C      = 0x83
    CMD_MASTERCURRENT   = 0x87
    CMD_SETREMAP        = 0xA0
    CMD_STARTLINE       = 0xA1
    CMD_DISPLAYOFFSET   = 0xA2
    CMD_NORMALDISPLAY   = 0xA4
    CMD_DISPLAYALLON    = 0xA5
    CMD_DISPLAYALLOFF   = 0xA6
    CMD_INVERTDISPLAY   = 0xA7
    CMD_SETMULTIPLEX    = 0xA8
    CMD_SETMASTER       = 0xAD
    CMD_DISPLAY_OFF     = 0xAE
    CMD_DISPLAY_ON      = 0xAF
    CMD_POWERMODE       = 0xB0
    CMD_PRECHARGE       = 0xB1
    CMD_CLOCKDIV        = 0xB3
    CMD_PRECHARGE_A     = 0x8A
    CMD_PRECHARGE_B     = 0x8B
    CMD_PRECHARGE_C     = 0x8C
    CMD_PRECHARGELEVEL  = 0xBB
    CMD_VCOMH           = 0xBE
    CMD_CLEAR_WINDOW    = 0x25
    
    
    def __init__(self, **kwargs):
        self.oled_res = kwargs.get('res_pin', 25)
        self.oled_dc = kwargs.get('dc_pin', 24)
        self.spi_bus = kwargs.get('spi_bus', 0)
        self.spi_device = kwargs.get('spi_device', 0)
        self.spi_speed = kwargs.get('spi_speed',16000000)#RPi spi max speed is 15,6 MHz(?)
        #init:
        self.__init_gpio()
        self.__open_SPI() 
        self.__reset_oled()
        self.__setup()
        self.clear()
        
        
    def __exit__(self):
        self.remove()
        
        
    def __init_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.oled_dc, self.oled_res], GPIO.OUT)
        GPIO.output(self.oled_dc, GPIO.LOW)
        GPIO.output(self.oled_res, GPIO.HIGH)
        
        
    def __open_SPI(self):
        self.spi = spidev.SpiDev()
        self.spi.open(self.spi_bus, self.spi_device)
        self.spi.mode = 0b11
        self.spi.max_speed_hz = self.spi_speed
    
    
    def __reset_oled(self):
        self.spi.cshigh = True
        GPIO.output(self.oled_res, GPIO.LOW)
        time.sleep(0.5)
        GPIO.output(self.oled_res, GPIO.HIGH)
        time.sleep(0.5)
        self.spi.cshigh = False
        
        
    def __setup(self):
        self.__write_command([self.CMD_DISPLAY_OFF])
        self.__write_command([self.CMD_SETREMAP, 0x72]) # 0x72 => RGB color mode; 0x76 => BGR color mode
        self.__write_command([self.CMD_STARTLINE, 0x00])
        self.__write_command([self.CMD_DISPLAYOFFSET, 0x00])
        self.__write_command([self.CMD_NORMALDISPLAY])
        self.__write_command([self.CMD_SETMULTIPLEX, 0x3F])
        self.__write_command([self.CMD_SETMASTER, 0x8E])
        self.__write_command([self.CMD_POWERMODE, 0x0B]) 
        self.__write_command([self.CMD_PRECHARGE, 0x74]) # @todo check why in some code is 0x31
        self.__write_command([self.CMD_CLOCKDIV, 0xD0]) # @todo check why in some code is 0xF0
        self.__write_command([self.CMD_PRECHARGE_A, 0x80])
        self.__write_command([self.CMD_PRECHARGE_B, 0x80])
        self.__write_command([self.CMD_PRECHARGE_C, 0x80])
        self.__write_command([self.CMD_PRECHARGELEVEL, 0x3E]) # @todo check why in some code is 0x3A
        self.__write_command([self.CMD_VCOMH, 0x3E]) 
        self.__write_command([self.CMD_MASTERCURRENT, 0x0F])# 0x06
        self.__write_command([self.CMD_CONTRAST_A, 0xFF])
        self.__write_command([self.CMD_CONTRAST_B, 0xFF])
        self.__write_command([self.CMD_CONTRAST_C, 0xFF])
        self.__write_command([self.CMD_DISPLAY_ON])
        
        
    def clear(self):
        self.__write_command([self.CMD_CLEAR_WINDOW, 0x00, 0x00, SSD1331_SCREEN_WIDTH, SSD1331_SCREEN_HEIGHT])
        
        
    def remove(self):
        GPIO.cleanup()
        self.spi.close()
    
    
    def __write_command(self, cmd):
        if not isinstance(cmd, (list, tuple)):
            cmd = [cmd]
        GPIO.output(self.oled_dc, GPIO.LOW)
        self.spi.xfer(cmd)
        
        
    def __write_data(self, data):
        if not isinstance(data, (list, tuple)):
            data = [data]
        GPIO.output(self.oled_dc, GPIO.HIGH)
        self.spi.xfer(data)
    
    
    def __prepare_big_data(self, data_array):
        init_size = sys.getsizeof(data_array)
        if init_size < 4096:
            return data_array
        new_array = []
        temp_array = []
        for x in data_array:
            temp_size = sys.getsizeof(temp_array) + sys.getsizeof(x)
            if temp_size >= 4096:
                 new_array.append(temp_array)
                 temp_array = []
            temp_array.append(x)
        if temp_array:
            new_array.append(temp_array)
        return new_array
    
    
    def write_many_pixels(self, data, x0 = 0, y0 = 0, x1 = SSD1331_SCREEN_WIDTH, y1 = SSD1331_SCREEN_HEIGHT):
        # after select_pixel_area you can send many pixel colors and it will be applay to next pixels
        # its useful for write images (line by line or on entire screen)
        if self.select_pixel_area(x0, y0, x1, y1):
            data = self.__prepare_big_data(data)
            for small_part in data:
                self.__write_data(small_part)
    
    
    def select_pixel(self, x, y):
        if (x > SSD1331_SCREEN_WIDTH) or (y > SSD1331_SCREEN_HEIGHT) or (x < 0) or (y < 0):
            return False
        self.__write_command([self.CMD_SETCOLUMN, x, x, self.CMD_SETROW, y, y])
        return True
    
    def select_pixel_area(self, x0, y0, x1, y1):
        if x0 > x1: x0, x1 = (x1, x0)
        if y0 > y1: y0, y1 = (y1, y0)
        
        if (x1 > SSD1331_SCREEN_WIDTH) or (y1 > SSD1331_SCREEN_HEIGHT) or (x0 < 0) or (y0 < 0):
            return False
        self.__write_command([self.CMD_SETCOLUMN, x0, x1 , self.CMD_SETROW, y0, y1])
        return True
    
    def draw_pixel_line(self, data, x0 = 0, x1 = SSD1331_SCREEN_WIDTH, y = 0):
        if self.select_pixel_area(x0, y, x1, y):
            self.__write_data(data)
            
    def draw_pixel(self, x, y, color):
        if self.select_pixel(x, y):
            self.__write_data([(color >> 8) & 0xFF, color & 0xFF])
        
        
    def draw_line(self, x0, y0, x1, y1, color):
        if x0 > x1: x0, x1 = (x1, x0)
        if y0 > y1: y0, y1 = (y1, y0)
        
        if (x1 > SSD1331_SCREEN_WIDTH) or (y1 > SSD1331_SCREEN_HEIGHT) or (x0 < 0) or (y0 < 0):
            return False
        
        self.__write_command([self.CMD_DRAWLINE, x0 & 0xFF, y0 & 0xFF, x1 & 0xFF, y1 & 0xFF])
        #delay?
        self.__write_command([(color >> 11) << 1, (color >> 5) & 0x3F, (color << 1) & 0x3F])
        return True
    
    
    def color565(self, r, g, b):
        c = r >> 3;
        c <<= 6;
        c |= g >> 2;
        c <<= 5;
        c |= b >> 3;
        return c;
    
    
