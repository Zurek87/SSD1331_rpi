import SSD1331
import time


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
    time.sleep(5)
test(device)
device.remove()