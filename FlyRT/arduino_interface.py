import serial
import time
import threading

def init_serial(comm_port, baud):
	return serial.Serial(comm_port, baud)

def lights(ser, ifd, thresh, pulse_len):

	def send_command(pulse_len):
		t_start = time.time()

		while ((time.time() - t_start) < pulse_len):
			ser.write(str.encode('1'))
		ser.write(str.encode('0'))

	send_thread = threading.Thread(target=send_command, args=(pulse_len,))

	if (ifd < thresh):
		send_thread.start()
	else:
		pass

	return time.time()
