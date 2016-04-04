# SSD1331_rpi
Lib for oled SSD1331 to use with Raspberry pi (testet on rpi3)

###Connect SSD1331 to RPI:
```
SSD1331:		PI:
VCC		<->		3,3V
GDN		<->		GDN
NC	  not connected!
DIN		<->		MOSI
CLK		<->		SCLK
CS		<->		CE0
D/C		<->		#24
RES		<->		#25
```

MOSI, SCLK, CE0 are from SPI0 (http://pinout.xyz/pinout/spi)