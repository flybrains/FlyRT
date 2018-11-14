import  numpy as np
import time
import cv2
import sys
import os
from datetime import datetime
import serial
#import PyCapture2
import csv

import config
import metrics
from global_draw import draw_global_results, add_thumbnails
import data_logger as dl
from data_logger import Logger
from info_panel import generate_info_panel, get_vis_shape
from select_arena_roi import crop_frame
import arduino_interface as ard
import utils
import image_patch as ip
from find_animals import detect_blobs
from maintain_id import preserve_id
from tracker import Tracker, Track
from wings import get_head_coords

def run(cd, process_min=None, process_max=None, n_processes=None):

	# Read in parameters set using the UI
	input_vidpath = 	str(cd['path'])
	recording =     	bool(cd['record'])
	logging =       	bool(cd['log'])
	scaling =       	float(cd['scaling'])
	multi = 			cd['multi']
	n_inds =        	int(cd['n_inds'])
	heading =       	bool(cd['heading'])
	wings =         	bool(cd['wings'])
	ifd_on =        	bool(cd['IFD'])
	arena_mms =     	float(cd['arena_mms'])
	thresh_val =    	cd['thresh_val']
	crop = 				cd['crop']
	r = 				cd['r']
	mask = 				cd['mask']
	comm =          	str(cd['comm'])
	baud =          	int(cd['baud'])
	ifd_min =       	float(cd['IFD_thresh'])
	pulse_len =     	float(cd['pulse_len'])
	pulse_lockout = 	float(cd['pulse_lockout'])
	ifd_time_thresh = 	float(cd['IFD_time_thresh'])
	rt_ifd = 			bool(cd['RT_IFD'])
	rt_pp = 			bool(cd['RT_PP'])
	rt_pp_delay = 		int(cd['RT_PP_Delay'])
	rt_pp_period = 		int(cd['RT_PP_Period'])
	rt_LED_red = 		bool(cd['LED_color_Red'])
	rt_LED_green = 		bool(cd['LED_color_Green'])
	rt_LED_intensity = 	int(cd['LED_intensity'])
	FLIR =          	bool(cd['FLIR'])
	rt_LED_color =		cd['rt_LED_color']
	colors = [(0,255,0),(0,255,255),(255,0,255),(255,255,255),(255,255,0),(255,0,0),(0,0,0)]

	# Initialize control flow parameters
	stop_bit, roll_call, all_present, history = False, 0, False, None

	# Initialize frame counters
	process_frame_count, fps_calc = 0, 0

	# Set scaling params
	mm2pixel = float(arena_mms/crop.shape[0])

	# Set up serial port if needed
	if (rt_ifd) or (rt_pp==True):
		ser = ard.init_serial(comm, baud)
		time.sleep(2)

	# Determine final output frame size
	vis, vis_shape = get_vis_shape(crop, scaling)

	# Generate loctions to store outuput data
	utils.file_ops()

	# Start csv logger
	if logging==True:
		logger = dl.Logger()
		logger.create_outfile()
		logger.write_header(process_frame_count, n_inds, ifd=True, headings = True)

	# Use calculated shape to initialize writer
	if (recording==True):
		dt = datetime.now()
		out = cv2.VideoWriter("generated_data/movies/"+str(dt.month)+"_"+str(dt.day)+"_"+str(dt.year)+"_"+str(dt.hour)+str(dt.minute)+'.avi', cv2.VideoWriter_fourcc(*'MJPG'), 30, (vis.shape[1], vis.shape[0]), True)

	# Diff calculation initialization
	last, df = 0, []

	# Individual location(s) measured in the last and current step [x,y]
	meas_last, meas_now= list(np.zeros((n_inds,4))), list(np.zeros((n_inds,4)))

	# Init backups for error-prone functions
	last_good_list, old_meas, old_ind = None, [[meas_last, meas_now]], [None]

	# Initialize metrics backups
	old_ifd, old_angles = 0, [0,0]

	# Initialize RT Experiment Backups
	last_pulse_time, accum = 0, [time.time(), None]

	# FLIR Camera Stuff
	def capIm():
		# Function retreives buffer from FLIR camera in place of cv2 capture
		try:
			img = cam.retrieveBuffer()
		except PyCapture2.Fc2error as fc2Err:
			print("Error retrieving buffer :", fc2Err)
			return False, []
		data = np.asarray(img.getData(), dtype=np.uint8)
		data = data.reshape((img.getRows(), img.getCols()))
		return True, data

	# Check if Real Time experiment being done with FLIR camera, init connection if so
	if FLIR==True:
		bus = PyCapture2.BusManager()
		cam = PyCapture2.Camera()
		uid = bus.getCameraFromIndex(0)
		cam.connect(uid)
		cam.startCapture()
		this=1
	else:
		cap = cv2.VideoCapture(input_vidpath)
		if cap.isOpened() == False:
			sys.exit('Video file cannot be read! Please check input_vidpath to ensure it is correctly pointing to the video file')
		else:
			print('Capture Opened')

	# Initialize time
	time0 = time.time()

	while(True):

		# Capture frame-by-frame
		n_inds = int(cd['n_inds'])
		time1 = time.time()

		if FLIR==True:
			ret = True
			ret, frame = capIm()
			frame = np.expand_dims(frame, 2)
			frame = cv2.cvtColor(frame,cv2.COLOR_GRAY2BGR)
			this+=1
		else:
			ret, frame = cap.read()
			this = cap.get(1)


		if ret == True:

			#Resize & keep color frame, make BW frame
			frame = crop_frame(frame, r)
			cl_frame = cv2.resize(frame, None, fx = scaling, fy = scaling, interpolation = cv2.INTER_LINEAR)
			bw_frame = cv2.cvtColor(cl_frame, cv2.COLOR_BGR2GRAY)
			_, thresh = cv2.threshold(bw_frame, thresh_val,255,0)

			#+++++++++++++++++++++
			# Detect contours
			contours, meas_last, meas_now, num_valid_contours, wins = detect_blobs(cl_frame, thresh, meas_last,  meas_now,  colors)
			print(meas_now)

			# Generate metrics
			angles, old_angles = metrics.relative_angle(meas_now, old_angles)
			ifd, old_ifd = metrics.ifd([[int(meas[0][0]), int(meas[0][1])] for meas in meas_now], old_ifd, 0.5, mm2pixel)

			# Assign detections to Track object
			if process_frame_count > 0:
				tracker.assign_detection(meas_now, ifd)
			else:
				tracker = Tracker(n_inds, meas_now)

			meas_now = [track.get_coords() for track in tracker.list_of_tracks]
			pixel_meas = [[int(meas[0][0]), int(meas[0][1])] for meas in meas_now]
			# ++++++++++++++++++++++++++

			# Check to see if expected animal-count is present
			if num_valid_contours==n_inds:
				if process_frame_count==0:
					all_present=True
				roll_call += 1
				if roll_call > 150:
					all_present=True
			else:
				if process_frame_count < 300:
					roll_call = 0

			# Begin logging and metrics if all animals present
			if all_present==True:

				# Generate trace history
				history = dl.history(process_frame_count, history, pixel_meas)

				# Drawing
				new_frame = draw_global_results(cl_frame, meas_now, colors, history, n_inds, traces=True, heading=True)

				# Pass dictionary to data panel for visualization
				info_dict ={"frame_count": process_frame_count,
							"fps_calc": fps_calc,
							"logging":logging,
							"ifd": ifd,
							"recording": recording,
							"heading": angles}

				# Generate visualization from drawn frame and info
				vis = generate_info_panel(new_frame, info_dict, vis_shape)

				# Send light commands if doing an RT expriment
				if rt_ifd==True:
					last_pulse_time, accum = ard.lights_IFD(ser, last_pulse_time, accum, ifd, ifd_min, pulse_len, ifd_time_thresh, rt_LED_color, rt_LED_intensity)
				if (rt_pp==True) and ((time.time() - time0) >= rt_pp_delay):
					last_pulse_time = ard.lights_PP(ser, last_pulse_time, pulse_len, rt_pp_delay, rt_pp_period, rt_LED_color, rt_LED_intensity)
			else:
				# If all animals not yet present, use placeholders
				new_frame = cl_frame
				info_dict = None
				vis =  generate_info_panel(new_frame, info_dict, vis_shape)

			# Show present frame. Suppress to improve realtime speed
			cv2.imshow("FlyRT", vis)

			# Write to .avi
			if (recording==True):
				out.write(vis)

			# Write current measurment and calcs to CSV
			if (logging == True) and (all_present==True):
				logger.write_meas(process_frame_count, float(process_frame_count/30), pixel_meas[0:n_inds], ifd, angles)

			# FPS Calcs
			process_frame_count+=1
			fps = True
			time2 = time.time()
			fps_calc = float(process_frame_count/(time2-time0))

			# GUI Stop Tracking Button
			stop_bit = config.stop_bit
			if cv2.waitKey(1) & (stop_bit==True):
				break
		else:
			break

	# Clean up
	if FLIR==True:
		cam.stopCapture()
		cam.disconnect()
	else:
		cap.release()
	if logging==True:
		logger.close_writer()
	if (recording==True):
		out.release()
	cv2.destroyAllWindows()
	cv2.waitKey()

	return None
