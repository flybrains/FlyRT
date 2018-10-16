import serial
import time
import threading

def init_serial(comm_port, baud):
	return serial.Serial(comm_port, baud)

def lights(ser, ifd, thresh, pulse_len, accum, IFD_time_thresh):

	def send_command(pulse_len):
		t_start = time.time()

		while ((time.time() - t_start) < pulse_len):
			ser.write(str.encode('1'))
		ser.write(str.encode('0'))

	send_thread = threading.Thread(target=send_command, args=(pulse_len,))

	if (ifd < thresh):
		accum = accum + float(1/30)
		if accum > IFD_time_thresh:
			send_thread.start()
	else:
		pass
		accum = 0

	return time.time(), accum
