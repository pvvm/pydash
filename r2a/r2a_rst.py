from xml.etree.ElementTree import parse
from r2a.ir2a import IR2A
from player.parser import *
import time

class R2A_RST(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.qi = []                    # lista de qualidades
        self.request_time = 0
        self.last_fetch = 1             # tempo que durou para ser feito o download do último segmento (sft)
        self.quality_level = []
        pass

    def handle_xml_request(self, msg):
        #self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):

        parsed_mpd = parse_mpd(msg.get_payload())   # recebe o payload e faz o parsing
        self.qi = parsed_mpd.get_qi()               # recebe a lista de qualidades
        #print(self.qi)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()     # recebe o tempo do pedido
        print("QUALITY LEVEL LIST: ",self.quality_level)

        mi = 1/self.last_fetch                      # mi = msd/sft (considerando que a duração do segmento é sempre 1)
        epsilon = 0
        quality = 0

        if len(self.quality_level) != 0:
            quality = self.quality_level[-1]
            if quality < 19:                  # calcula o epsilon
                epsilon = (self.qi[quality + 1] - self.qi[quality]) / self.qi[quality]
            else:
                epsilon = 99999

        # Valores a serem modificados
        buf_min = 15
        buf_reduce = 30
        buf_safety = 45
        gamma = 0.8

        buffer_tuple = self.whiteboard.get_playback_buffer_size()   # tupla do tempo do buffer analisado e seu tamanho

        if len(buffer_tuple) > 0:
            print("A")
            buf_c = buffer_tuple[-1][1]     # tamanho atual do buffer

            if buf_c < buf_min:
                print("B")
                if mi >= 1:
                    print("C")
                    if quality > 0:
                        quality -= 1
                else:
                    print("D")
                    index = 0
                    for i in range(0, len(self.qi)):
                        if self.qi[i] < self.qi[quality] * mi:
                            index = i
                    quality = index
            
            elif mi < gamma and buf_c < buf_reduce:
                print("E")
                if quality > 0:
                    quality -= 1
            
            elif mi > (1 + epsilon) and buf_c > buf_safety:
                print("F")
                if quality < 19:
                    print("G")
                    quality += 1

            msg.add_quality_id(self.qi[quality])
            self.quality_level.append(quality)

        else:
            print("H")
            msg.add_quality_id(self.qi[0])
            self.quality_level.append(quality)

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.last_fetch = time.perf_counter() - self.request_time   # tempo para ser feito o ultimo fetch
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
