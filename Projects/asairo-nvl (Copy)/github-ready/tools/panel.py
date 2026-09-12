"""Native black MGR panel with the measured Itsusora corner coverage."""
import math,struct
WIDTH,HEIGHT,RADIUS=688,528,13.25
def rounded_panel():
 pixels=bytearray(WIDTH*HEIGHT*4)
 for y in range(HEIGHT):
  dy=max(RADIUS-(y+.5),(y+.5)-(HEIGHT-RADIUS),0)
  for x in range(WIDTH):
   dx=max(RADIUS-(x+.5),(x+.5)-(WIDTH-RADIUS),0)
   pixels[(y*WIDTH+x)*4+3]=round(255*max(0,min(1,RADIUS+.5-math.hypot(dx,dy))))
 # BGRA, bottom-up BMP. The symmetric panel is identical after a vertical flip.
 bmp=b'BM'+struct.pack('<IHHI',54+len(pixels),0,0,54)+struct.pack('<IiiHHIIiiII',40,WIDTH,HEIGHT,1,32,0,len(pixels),0,0,0,0)+pixels
 packed=b''.join(bytes([len(bmp[i:i+32])-1])+bmp[i:i+32] for i in range(0,len(bmp),32))
 return struct.pack('<HII',1,len(bmp),len(packed))+packed
