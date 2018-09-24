import serial
import time

def init_serial(comm_port, baud):
	return serial.Serial(comm_port, baud, timeout=0)

def lights(ser, ifd, thresh, flash_t, wait_t)
	
	if ifd < thresh:
		ser.write('1')
		time.sleep(flash_t)
		ser.write('0')

	else:
		ser.write('0')

	return None
