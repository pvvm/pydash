from xml.etree.ElementTree import parse
from r2a.ir2a import IR2A
from player.parser import *
import time

class R2A_RST(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.qi = []                    # lista de qualidades
        self.request_time = 0
        self.last_fetch = 1             # tempo que durou para ser feito o download do último segmento (sft)
        self.quality_level = 0
        pass

    def handle_xml_request(self, msg):
        #self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):

        parsed_mpd = parse_mpd(msg.get_payload())   # recebe o payload e faz o parsing
        self.qi = parsed_mpd.get_qi()               # recebe a lista de qualidades
        print(self.qi)
        #t = time.perf_counter() - self.request_time
        #print(msg.get_payload())
        #print("\n\nTEMPO DE RESPOSTA", t, "\n\n")

        #self.throughputs.append(msg.get_bit_length() / t)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()
        #avg = mean(self.throughputs) / 2

        #selected_qi = self.qi[0]
        #for i in self.qi:
        #    if avg > i:
        #        selected_qi = i

        #msg.add_quality_id(selected_qi)

        #print("FETCH:      ", self.last_fetch)
        mi = 1/self.last_fetch                      # mi = msd/sft (considerando que a duração do segmento é sempre 1)
        #print("MI: ", mi)
        epsilon = 0

        qi_tuple = self.whiteboard.get_playback_qi()
        if len(qi_tuple) == 0:
            self.quality_level = 0
        else:
            self.quality_level = qi_tuple[-1][1]
            if self.quality_level < 19:                  # calcula o epsilon
                epsilon = (self.qi[self.quality_level + 1] - self.qi[self.quality_level]) / self.qi[self.quality_level]
            else:
                epsilon = 99999
        #print("EPSILON: ", epsilon)

        # Verificar se podem ser constantes
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
                    if self.quality_level > 0:
                        self.quality_level -= 1
                else:
                    print("D")
                    index = 0
                    for i in range(0, len(self.qi)):
                        if self.qi[i] < self.qi[self.quality_level] * mi:
                            index = i
                    self.quality_level = index
            
            elif mi < gamma and buf_c < buf_reduce:
                print("E")
                if self.quality_level > 0:
                    self.quality_level -= 1
            
            elif mi > (1 + epsilon) and buf_c > buf_safety:
                print("F")
                if self.quality_level < 19:
                    self.quality_level += 1
            
            msg.add_quality_id(self.qi[self.quality_level])

        else:
            print("G")
            msg.add_quality_id(self.qi[0])

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.last_fetch = time.perf_counter() - self.request_time
        #self.throughputs.append(msg.get_bit_length() / t)
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
