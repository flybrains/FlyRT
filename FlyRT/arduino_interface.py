import serial
import time
import threading
# For all arduino experiments:
# Red Light = 1
# Green Light = 2
# For serial commands sent to arduino port

def init_serial(comm_port, baud):
	return serial.Serial(comm_port, baud, write_timeout=0)

def lights_IFD(ser, last_pulse_time, accum, ifd, ifd_thresh, pulse_len, pulse_lockout, ifd_time_thresh, LED_color, LED_intensity):

	if (LED_color=='red'):
		send_str = str(LED_intensity)

	for_green = ['0','0','a', 'b','c','d','e','f','g','h','i']

	if (LED_color=='green'):
		send_str = str(for_green[LED_intensity])

	def send_command(pulse_len, send_str):
		start_time = time.time()

		while((time.time() - start_time) < pulse_len):
			ser.write(str.encode(send_str))
			time.sleep(1)
		ser.write(str.encode('0'))

	if (ifd < ifd_thresh):

		accum[1]=time.time()

		if (accum[1] is not None) and ((accum[1] - accum[0]) >= ifd_time_thresh) and ((time.time() - last_pulse_time) > pulse_lockout):

			send_thread = threading.Thread(target=send_command, args=(pulse_len, send_str,))
			send_thread.start()

			return time.time(), accum

		else:

			return last_pulse_time, accum
	else:
		accum = [time.time(), None]

		return last_pulse_time, accum

def lights_PP(ser, last_pulse_time, pulse_len, rt_pp_delay, rt_pp_period, LED_color, LED_intensity):

	if (LED_color=='red'):
		send_str = str(LED_intensity)

	for_green = ['0','0','a', 'b','c','d','e','f','g','h','i']

	if (LED_color=='green'):
		send_str = str(for_green[LED_intensity])

	def send_command(pulse_len, send_str):
		start_time = time.time()

		while((time.time() - start_time) < pulse_len):
			ser.write(str.encode(send_str))
			time.sleep(1)
		ser.write(str.encode('0'))

	if ((time.time() - last_pulse_time) >= rt_pp_period):

		send_thread = threading.Thread(target=send_command, args=(pulse_len, send_str,))
		send_thread.start()

		return time.time()


	return last_pulse_time

def close_port(ser):
	ser.close()
	return None