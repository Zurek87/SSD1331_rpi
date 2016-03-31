import struct
import spidev
import time
import RPi.GPIO as GPIO

# based on:
#  - libs from github:
#    - c++ https://github.com/adafruit/Adafruit-SSD1331-OLED-Driver-Library-for-Arduino
#    - python
#  - SSD1331 manual: https://www.adafruit.com/datasheets/SSD1331_1.2.pdf
# Danger! many libs in python replicated this same bugs (ie: using normal gpio.out pin as CS pin, not dedicated to spi) 
# or strange names (function changes 24bit color to 16bit named "color656" not "color565" )
# 
# stop using 'fake' CS pin (#23) and starting use SPI CE0 pin


class SSD1331:
    COMMAND = GPIO.LOW
    DATA    = GPIO.HIGH
    SCREEN_WIDTH  = 0x5F # from 0 to real_width - 1
    SCREEN_HEIGHT = 0x3F
    
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
        self.spi.max_speed_hz = 6000000
    
    def __reset_oled(self):
        self.spi.cshigh = True
        self.spi.xfer([0])
        GPIO.output(self.oled_res, GPIO.LOW)
        time.sleep(0.5)
        GPIO.output(self.oled_res, GPIO.HIGH)
        time.sleep(0.5)
        self.spi.cshigh = False
        self.spi.cshigh = False
        self.spi.xfer([0])
        
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
        
    def remove(self):
        GPIO.cleanup()
        self.spi.close()
    
    def select_pixel(self, x, y):
        if (x > self.SCREEN_WIDTH) or (y > self.SCREEN_HEIGHT):
            return False
        self.__write_command([self.CMD_SETCOLUMN, x, self.SCREEN_WIDTH, self.CMD_SETROW, y, self.SCREEN_HEIGHT])
        return True
        
    def draw_pixel(self, x, y, color):
        if self.select_pixel(x, y):
            self.__write_data([(color >> 8) & 0xFF, color & 0xFF])
        
    def draw_line(self, x0, y0, x1, y1, c):
        # // Boundary check
        # if ((y0 >= TFTHEIGHT) && (y1 >= TFTHEIGHT))
        #   return;
        # if ((x0 >= TFTWIDTH) && (x1 >= TFTWIDTH))
        #   return;    
        # if (x0 >= TFTWIDTH)
        #   x0 = TFTWIDTH - 1;
        # if (y0 >= TFTHEIGHT)
        #   y0 = TFTHEIGHT - 1;
        # if (x1 >= TFTWIDTH)
        #   x1 = TFTWIDTH - 1;
        # if (y1 >= TFTHEIGHT)
        #   y1 = TFTHEIGHT - 1;
        #    
        # writeCommand(SSD1331_CMD_DRAWLINE);
        # writeCommand(x0);
        # writeCommand(y0);
        # writeCommand(x1);
        # writeCommand(y1);
        # delay(SSD1331_DELAYS_HWLINE);  
        # writeCommand((uint8_t)((color >> 11) << 1));
        # writeCommand((uint8_t)((color >> 5) & 0x3F));
        # #writeCommand((uint8_t)((color << 1) & 0x3F));
        # delay(SSD1331_DELAYS_HWLINE); 
        return
    
    def clear(self):
        self.__write_command([self.CMD_CLEAR_WINDOW, 0x00, 0x00, 0x5F, 0x3F])
    
    def __write_command(self, cmd):
        GPIO.output(self.oled_dc, GPIO.LOW)
        self.spi.xfer(cmd)
        
    def __write_data(self, data):
        GPIO.output(self.oled_dc, GPIO.HIGH)
        self.spi.xfer(data)
        
