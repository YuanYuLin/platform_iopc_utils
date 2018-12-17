#!/bin/python2.7

import struct
import pprint
import sys
import ConfigParser
import binascii
import json

'''
[Boot disk layout]
'''

def create_buffer(record_count, record_size):
    buff=[]
    for idx in range(0, record_count):
        buff.append(bytearray('\0' * record_size))

    return buff

def dao_to_buffer(dao, buff, record_format, data_size):
    g_index=0
    for key in dao.keys():
        pad = bytearray(str.encode('\0' *  data_size))

        idx=0
        for ch in bytearray(key):
            pad[idx]=ch
            idx+=1

        for ch in bytearray(dao[key]):
            pad[idx]=ch
            idx+=1

        crc32 = 0
        rec_type = 1
        key_len = len(key)
        val_len = len(dao[key])
        resv = 0
        data = struct.pack(record_format, crc32, rec_type, key_len, val_len, resv, str(pad))
        crc32 = binascii.crc32(bytearray(data))

        data = struct.pack(record_format, 0, rec_type, key_len, val_len, resv, str(pad))

        idx=0
        for ch in bytearray(data):
            buff[g_index][idx] = ch
            idx+=1
        g_index+=1

    return buff

def out_to_binary(buff, dao_bin_path):
    #create_buffer(1, (64 * 1024))
    #struct.pack("12sH50s", "$[IOPC_DATA]", record_count, bytearray('\0' * 50))
    fd=open(dao_bin_path, 'wb')
    for rec in buff:
        fd.write(rec)
    fd.close()

def out_to_c(buff, record_count, record_format):
    ft=open('db_init.inc', 'w')
    ft.write('#define DAO_KV_MAX ' + str(record_count) + '\n')
    ft.write('static struct dao_kv_512_t dao_kv_list[DAO_KV_MAX]={')
    idx=0
    for rec in buff:
        csum, tp, kl, vl, rsv, data = struct.unpack(record_format, rec)
        ft.write('\n' + '{')
        ft.write('.hdr = {')
        ft.write('.chksum = ')
        ft.write(str(int(csum)))
        ft.write(',')
        ft.write('.type = ')
        ft.write(str(int(tp)))
        ft.write(',')
        ft.write('.key_len = ')
        ft.write(str(int(kl)))
        ft.write(',')
        ft.write('.val_len = ')
        ft.write(str(int(vl)))
        ft.write(',')
        ft.write('.resv = ')
        ft.write(str(int(rsv)))
        ft.write('},')
        ft.write('.data = {')
        for ch in bytearray(data):
            ft.write(str(int(ch)))
            ft.write(',')
        ft.write('}')
        ft.write('},')
    ft.write('};')
    ft.close()

def head_to_binary(pack):
    data = bytearray('\0' * 64)
    idx = 0
    for ch in bytearray(pack):
        data[idx] = ch
        idx += 1
    return data

def size_to_bytes(size_str):
    val = 0
    if size_str[-1:] == 'B':
        val = int(size_str[0:-1])
    elif size_str[-1:] == '%':
        val = 0xFFFFFFFF
    return val

def create_header(layout_obj):
    header = bytearray('\0' * (64 *1024))
    buffers = []
    version = 1
    table_type = str(layout_obj["table_type"])
    platform = str(layout_obj["platform"])
    platform_id = layout_obj["platform_id"]
    print table_type, platform, platform_id
    pack = struct.pack("12sI20sI12s", "$[IOPCHEAD]$".ljust(12), version, platform.ljust(20), platform_id, table_type.ljust(12))
    buffers.append(head_to_binary(pack))
    for part in layout_obj["parts"]:
        obj = layout_obj[part]
        part_name = str(part)
        boot=obj["boot"]
        fstype = str(obj["fstype"])
        start = size_to_bytes(obj["start"])
        end = size_to_bytes(obj["end"])

        bin_file = obj["bin_files"]
        pack = struct.pack("12s10s10sQQB", "$[IOPCREC]$".ljust(12), part_name.ljust(10), fstype.ljust(10), start, end, boot)
        buffers.append(head_to_binary(pack))

    pack = struct.pack("12sI20sI12s", "$[IOPCEND]$".ljust(12), version, platform.ljust(20), platform_id, table_type.ljust(12))
    buffers.append(head_to_binary(pack))
    idx = 0
    for sec in buffers:
        for ch in sec:
            header[idx]=ch
            idx+=1

    return header

def help():
    print "usage: dao.py <dao.ini> <dao.bin>"
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        help()
    dao={}
    cfg_ini = sys.argv[1]
    dao_bin_path = sys.argv[2]
    config = ConfigParser.RawConfigParser()
    config.read(cfg_ini)
    single_section = config.items("CFG_DAO")
    for item in single_section:
        print "key = %s, valule = %s" % (item[0], item[1])
        key = item[0]
        val = item[1]
        dao[key] = val

    header_size = 12
    data_size = 500
    record_count=128
    record_format="IBBHI" + str(data_size) + "s"
    record_size= header_size + data_size

    buf=create_buffer(record_count, record_size)
    buf=dao_to_buffer(dao, buf, record_format, data_size)
    out_to_binary(buf, dao_bin_path)
    out_to_c(buf, record_count, record_format)

    layout = config.get('CFG_IMAGE', 'layout')
    layout_obj  = json.loads(layout)
    '''
    header_bin = create_header(layout_obj)
    hdr_path = dao_bin_path + ".hdr"
    fd=open(hdr_path, 'wb')
    fd.write(header_bin)
    fd.close()
    '''
