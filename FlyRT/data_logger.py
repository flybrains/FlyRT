import csv
import os
from datetime import datetime


class Logger(object):
	def __init__(self):

		dt = datetime.now()
		month = str(dt.month)
		day = str(dt.day)
		year = str(dt.year)

		hour = str(dt.hour)
		minute = str(dt.minute)

		self.name_string = month+"_"+day+"_"+year+"_"+hour+minute+".csv"

	def create_outfile(self):
		self.f = open(os.getcwd()+"\\generated_data\\logs\\"+self.name_string, 'w', newline="")
		self.writer = csv.writer(self.f, delimiter=',')

		return None

	def write_header(self, frame_count, n_inds, ifd=True, headings=False):

		header = []

		header.append("Frame_No")
		header.append("Time (s)")

		for idx in range(n_inds):
			header.append("Animal_{}_x".format(str(idx)))
			header.append("Animal_{}_y".format(str(idx)))

		if ifd:
			header.append("IFD")

		if headings:
			header.append("1:2_angle_(deg)")
			header.append("2:1_angle_(deg)")

		self.writer.writerow(header)

		return None


	def write_meas(self, frame_count, time, pixel_meas, ifd=None, headings=None):

		elems = []

		elems.append(frame_count)
		elems.append(time)

		for meas in pixel_meas:
			elems.append(meas[0])
			elems.append(meas[1])

		if ifd is not None:
			elems.append(ifd)

		if headings is not None:
			elems.append(headings[0])
			elems.append(headings[1])


		self.writer.writerow(elems)

	def close_writer(self):
		self.f.close()


def manage_history(history, pixel_meas, hist_len, init=False):
	if init:
		history = []
	history.append(pixel_meas)
	if len(history) > hist_len:
		history.pop(0)
	return history

def history(frame_count, history, pixel_meas):

	if frame_count==0:
		return manage_history(None, pixel_meas, 200, init=True)

	else:
		try:
			return manage_history(history, pixel_meas, 200, init=False)

		except UnboundLocalError:
			return manage_history(None, pixel_meas, 200, init=True)
