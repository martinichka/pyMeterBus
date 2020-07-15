#!/usr/bin/env python

import serial
import meterbus
import time
from struct import pack
import binascii

from meterbus.globals import g
from meterbus.defines import *

address = meterbus.ADDRESS_NETWORK_LAYER # don't use primary address, but select by secondary address

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
    meterbus.debug(True)
    

    def application_reset():
        frame = meterbus.TelegramLong()
        frame.header.cField.parts = [ CONTROL_MASK_SND_UD | CONTROL_MASK_DIR_M2S ]
        frame.header.aField.parts = [address]
        frame.body.bodyHeader.ci_field.parts = [0x50]
        frame.body.bodyPayload.body = [0x00]
        meterbus.serial_send(ser, frame)
        frame = meterbus.load(meterbus.recv_frame(ser, 1))
        assert isinstance(frame, meterbus.TelegramACK)

    def snd_nke():
        frame = meterbus.TelegramShort()
        frame.header.cField.parts = [ CONTROL_MASK_SND_NKE | CONTROL_MASK_DIR_M2S ]
        frame.header.aField.parts = [address]
        meterbus.send_request_frame(ser, address, frame)
        frame = meterbus.load(meterbus.recv_frame(ser, 1))
        assert isinstance(frame, meterbus.TelegramACK)

    def req_ske():
        frame = meterbus.TelegramShort()
        frame.header.cField.parts = [ CONTROL_MASK_REQ_SKE | CONTROL_MASK_DIR_M2S ]
        frame.header.aField.parts = [address]
        meterbus.send_request_frame(ser, address, frame)
        frame = meterbus.load(meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH))
        assert isinstance(frame, meterbus.TelegramShort)
        return frame

    def req_ud1():
        frame = meterbus.TelegramShort()
        frame.header.cField.parts = [ CONTROL_MASK_REQ_UD1 | CONTROL_MASK_DIR_M2S ]
        frame.header.aField.parts = [address]
        meterbus.send_request_frame(ser, address, frame)
        frame = meterbus.load(meterbus.recv_frame(ser, 1))
        assert isinstance(frame, meterbus.TelegramACK)

    def req_ud2(fcb=False):
        frame = meterbus.TelegramShort()
        frame.header.cField.parts = [ CONTROL_MASK_REQ_UD2 | CONTROL_MASK_DIR_M2S | (CONTROL_MASK_FCB if fcb else 0) ]
        frame.header.aField.parts = [address]
        meterbus.send_request_frame(ser, address, frame)
        frame = meterbus.load(meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH))
        assert isinstance(frame, meterbus.TelegramLong)
        return frame

    def req_logger(logger_id):
        frame = meterbus.TelegramLong()
        frame.header.cField.parts = [ CONTROL_MASK_SND_UD | CONTROL_MASK_DIR_M2S ]
        frame.header.aField.parts = [address]
        frame.body.bodyHeader.ci_field.parts = [0x50]
        frame.body.bodyPayload.body = [0xF0, 0xF0, logger_id << 4, 0x00]
        meterbus.serial_send(ser, frame)
        frame = meterbus.load(meterbus.recv_frame(ser, 1))
        assert isinstance(frame, meterbus.TelegramACK)        

    def ping_address(ser, address, retries=5):
        for i in range(0, retries + 1):
            meterbus.send_ping_frame(ser, address)
            try:
                frame = meterbus.load(meterbus.recv_frame(ser, 1))
                if isinstance(frame, meterbus.TelegramACK):
                    return True
            except meterbus.MBusFrameDecodeError:
                pass

        return False

    def send_select_frame(secondary_address):
        meterbus.send_select_frame(ser, secondary_address)
        try:
            frame = meterbus.load(meterbus.recv_frame(ser, 1))
        except meterbus.MBusFrameDecodeError as e:
            frame = e.value

        assert isinstance(frame, meterbus.TelegramACK)

    # select by secondary address
    send_select_frame("711744492D2C3404")

    # request normal frame (assuming logger application has been terminated)
    frame = req_ud2()
    t = frame_get_time(frame)
    print("Timestamp of normal request before: " + t)
  
    req_logger(5)
    time.sleep(1)
    
    empty = False
    cnt = 0
    try:
        while not empty: 
            frame = req_ud2((cnt % 2) == 0)
            
            t = frame_get_time(frame)
            l = frame_get_selected_logger(frame)

            print("cnt: {}, logger: {}, timestamp: {}".format(cnt, l, t))
            if t is None:
                empty = True
            cnt = cnt + 1
            # time.sleep(2)
    finally:
        application_reset()

        # request normal frame (after logger application has been terminated)
        frame = req_ud2()
        t = frame_get_time(frame)

        print("Timestamp of normal request after: " + t)
