import SSD1331
import time
from oledFontSupport.oledFontSupport import *
device = SSD1331.SSD1331()

def test(device):
    r, g, b = (48, 213, 200)
    rd, gd, bd = (1,1,1)
    arr = []
    for x in range(9000):
        color = device.color565(r, g, b)
        
        r +=1 * rd
        g +=2 * gd
        b +=3 * bd
        if r > 255: 
            r = 0
            rd = 0 - rd
        if g > 255: 
            g = 0
            gd = 0 - gd
        if b > 255: 
            b = 0
            bd = 0 - bd
        arr.extend([(color >> 8) & 0xFF, color & 0xFF])
        
    device.write_many_pixels(arr)
    #time.sleep(1)
    #device.clear()
    color = device.color565(48, 213, 200)
    red = device.color565(255, 10, 10)
    bg_color = 0x0001
    fs = FontSettings(font = PI_LOGO, height=32, width=25)
    f = OledFontSupport(device, fs)
    
    x,y = (5, 5)
    xd, yd = (1, 1)
    for i in range(1000):
        
        f.draw_char(x, y, 0, color, bg_color)
        x += 1 * xd
        y += 1 * yd
        if (x >= SSD1331.SSD1331_SCREEN_WIDTH - 25) or (x <= 0):
            xd = 0 - xd
        if (y >= SSD1331.SSD1331_SCREEN_HEIGHT - 32) or (y <= 0):
            yd = 0 - yd
        device.draw_line(x - 1, y - 1, x + 25 ,y - 1, red)
        #device.draw_line(x + 25, y -1, x + 25, y + 32, bg_color)
        #device.draw_line(x, y, x, y, bg_color)
        #device.draw_line(x, y, x, y, bg_color)
        #time.sleep(0.1)
    time.sleep(5)
test(device)
device.remove()