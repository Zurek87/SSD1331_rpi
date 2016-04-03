from fonts import *

class FontSettings():
    def __init__(self, **kwargs):
        self.font = kwargs.get('font', FONT_5x7)
        self.height = kwargs.get('height', 7)
        self.width = kwargs.get('width', 5)
        #self.bit_height = kwargs.get('bit_height', 0x7F)
        self.is_dict_font = isinstance(self.font, dict)
    
    def get_char(self, i):
        if isinstance(i, str):
            if len(i) == 1:
                i = ord(i)

        if self.font[i]:
            return self.font[i]
        return []


class OledFontSupport():
    
    def __init__(self, device, font_settings):
        self.device = device
        self.font = font_settings
    
    def draw_char(self, x, y, char, color, bg_color):
        char_arr = self.font.get_char(char)
        if char_arr:
            char_data = []
            lines = []
            for i in xrange(0, self.font.height):
                for j in xrange(0, self.font.width):
                    line = char_arr[j]
                    line >>= i
                    if line & 0x1:
                        char_data.extend([(color >> 8) & 0xFF, color & 0xFF])
                    else:
                        char_data.extend([(bg_color >> 8) & 0xFF, bg_color & 0xFF])
                    
            self.device.write_many_pixels(char_data, x, y, x + self.font.width -1, y + self.font.height)


    def draw_string(self, x, y, str, color):
        for i in str:
            self.draw_char(x, y, i, color)
            x = x + self.font.width + 1
            
            