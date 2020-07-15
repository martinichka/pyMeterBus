#!/usr/bin/env python

import serial
import meterbus
import time
from struct import pack
import binascii

from meterbus.globals import g
from meterbus.defines import *

address = 49

def frame_get_time(frame):
    for record in frame.body.interpreted["records"]:
        if record["type"] == "VIFUnit.DATE_TIME_GENERAL":
            return record["value"]
    return None

def frame_get_selected_logger(frame):
    for record in frame.body.interpreted["records"]:
        if record["type"] == "VIFUnitExt.RESERVED":
            return binascii.b2a_hex(pack("<I", int(record["value"])))
    return None


with serial.Serial('/dev/ttyUSB0', 19200, 8, 'E', 1, 0.5) as ser:
    meterbus.debug(False)
    
    # #SND_NKE  
    # frame = meterbus.TelegramShort()
    # frame.header.cField.parts = [ CONTROL_MASK_SND_NKE | CONTROL_MASK_DIR_M2S ]
    # frame.header.aField.parts = [address]
    # meterbus.send_request_frame(ser, address, frame)
    # frame = meterbus.load(meterbus.recv_frame(ser, 1))
    # assert isinstance(frame, meterbus.TelegramACK)
    
    #Application reset  
    frame = meterbus.TelegramLong()
    frame.header.cField.parts = [ CONTROL_MASK_SND_UD | CONTROL_MASK_DIR_M2S ]
    frame.header.aField.parts = [address]
    frame.body.bodyHeader.ci_field.parts = [0x50]
    frame.body.bodyPayload.body = [0x00]
    meterbus.serial_send(ser, frame)
    frame = meterbus.load(meterbus.recv_frame(ser, 1))
    assert isinstance(frame, meterbus.TelegramACK)

#   #REQ_SKE  
#   frame = meterbus.TelegramShort()
#   frame.header.cField.parts = [ CONTROL_MASK_REQ_SKE | CONTROL_MASK_DIR_M2S ]
#   frame.header.aField.parts = [address]
#   meterbus.send_request_frame(ser, address, frame)
#   frame = meterbus.load(meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH))
#   assert isinstance(frame, meterbus.TelegramShort)
   
#   #REQ_UD1  
#   frame = meterbus.TelegramShort()
#   frame.header.cField.parts = [ CONTROL_MASK_REQ_UD1 | CONTROL_MASK_DIR_M2S ]
#   frame.header.aField.parts = [address]
#   meterbus.send_request_frame(ser, address, frame)
#   frame = meterbus.load(meterbus.recv_frame(ser, 1))
#   assert isinstance(frame, meterbus.TelegramACK)
    
    # #REQ_UD2  
    # frame = meterbus.TelegramShort()
    # frame.header.cField.parts = [ CONTROL_MASK_REQ_UD2 | CONTROL_MASK_DIR_M2S ]
    # frame.header.aField.parts = [address]
    # meterbus.send_request_frame(ser, address, frame)
    # frame = meterbus.load(meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH))
    # assert isinstance(frame, meterbus.TelegramLong)
    # print(frame.to_JSON())
    
    #REQ_Logger data
    frame = meterbus.TelegramLong()
    frame.header.cField.parts = [ CONTROL_MASK_SND_UD | CONTROL_MASK_DIR_M2S ]
    frame.header.aField.parts = [address]
    frame.body.bodyHeader.ci_field.parts = [0x50]
    frame.body.bodyPayload.body = [0xF0, 0xF0, 0x50, 0x00]
    meterbus.serial_send(ser, frame)
    frame = meterbus.load(meterbus.recv_frame(ser, 1))
    assert isinstance(frame, meterbus.TelegramACK)
    
    time.sleep(1)

    empty = False
    cnt = 0
    while not empty: 
        frame = meterbus.TelegramShort()
        frame.header.cField.parts = [ CONTROL_MASK_REQ_UD2 | (cnt % 2) * CONTROL_MASK_FCB ]
        frame.header.aField.parts = [address]
        meterbus.send_request_frame(ser, address, frame)
        frame = meterbus.load(meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH))
        assert isinstance(frame, meterbus.TelegramLong)
        
        t = frame_get_time(frame)
        l = frame_get_selected_logger(frame)

        print("cnt: {}, logger: {}, timestamp: {}".format(cnt, l, t))
        if t is None:
            empty = True
        cnt = cnt + 1
        # time.sleep(2)
