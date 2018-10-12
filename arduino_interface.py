import serial
import time

def init_serial(comm_port, baud):
	return serial.Serial(comm_port, baud)

def lights(ser, ifd, thresh):
	
	if (ifd < thresh):
		ser.write(str.encode('1'))
	else:
		ser.write(str.encode('0'))

	return None
