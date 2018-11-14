import  numpy as np
import  pandas  as  pd
import time
import cv2
import sys
from os import system
import os
from datetime import datetime
import serial
import PyCapture2
import csv

import config
import metrics
from global_draw import draw_global_results, add_thumbnails
import data_logger as dl
from data_logger import Logger
from select_arena_roi import launch_GUI, mask_frame
from info_panel import generate_info_panel
import arduino_interface as ard
import utils
import image_patch as ip
from find_animals import detect_blobs
from maintain_id import preserve_id
from tracker import Tracker, Track
from wings import get_head_coords

from FlyRTmulti import get_frame_max


def run(cd, process_min=None, process_max=None, n_processes=None):

	# Read in parameters set using the UI
	input_vidpath = 	str(cd['path'])
	recording =     	bool(cd['record'])
	logging =       	bool(cd['log'])
	scaling =       	cd['scaling']
	multi = 			cd['multi']
	n_inds =        	int(cd['n_inds'])
	heading =       	bool(cd['heading'])
	wings =         	bool(cd['wings'])
	ifd_on =        	bool(cd['IFD'])
	arena_mms =     	float(cd['arena_mms'])
	thresh_val =    	cd['thresh_val']
	mask_on =       	bool(cd['mask_on'])
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

	# Conditionally set the LED colors
	if rt_LED_red==True:
		rt_LED_color='red'
	if rt_LED_green==True:
		rt_LED_color='green'

	# Initialize control flow parameters
	stop_bit = False
	roll_call = 0
	all_present = False

	# If using multithreaded high speed post-hoc processing, initialize capture
	if multi==True:
		frames=[]
		cwd = os.getcwd()
		frames_save_dir = cwd+'/frame_pkgs'
		multi_frame_count = 0
		FLIR = False
		cap = cv2.VideoCapture(input_vidpath)
		cap.set(cv2.CAP_PROP_POS_FRAMES, process_min)

	# Set scaling params
	if arena_mms is not None:
		mm2pixel = float(arena_mms/crop.shape[0])
	else:
		mm2pixel = 0.1

	if scaling is not None:
		scaling = float(scaling)
	else:
		scaling = 1.0

	# Set up serial port if needed
	if (rt_ifd) or (rt_pp==True):
		ser = ard.init_serial(comm, baud)
		time.sleep(2)

	# Determine final output frame size
	max_pixel = 420
	if crop.shape[0]>max_pixel:
		info = np.zeros((crop.shape[0], int((crop.shape[0])*0.5), 3), np.uint8)
		padding=False
	else:
		info = np.zeros((max_pixel, 220, 3), np.uint8)
		pad = np.zeros((max_pixel - crop.shape[0], (crop.shape[0]), 3), np.uint8)
		padding=True

	if padding==True:
		h1, w1 = crop.shape[:2]
		h2, w2 = pad.shape[:2]
		tile1 = np.zeros((max(h1, h2), w2, 3), np.uint8)
		tile1[:h1,:w1, :3] = crop
		h3, w3 = tile1.shape[:2]
		h4, w4 = info.shape[:2]
		vis = np.zeros((max(h3, h4), w3+w4,3), np.uint8)
		vis[:h3, :w3,:3] = tile1
		vis[:h4, w3:w3+w4,:3] = info
	else:
		info = np.zeros((crop.shape[0], int((crop.shape[0])*0.5), 3), np.uint8)
		h1, w1 = crop.shape[:2]
		h2, w2 = info.shape[:2]

		vis = np.zeros((max(h1, h2), w1+w2,3), np.uint8)
		vis[:h1, :w1,:3] = crop
		vis[:h2, w1:w1+w2,:3] = info

	vis = cv2.resize(vis, None, fx = scaling, fy = scaling, interpolation = cv2.INTER_LINEAR)
	vis_shape = vis.shape
	utils.file_ops()

	# Initialize frame counter
	process_frame_count = 0
	fps_calc = 0

	if multi==True:
		global_frame_count = process_min
		batch_frame_count = 0

	# Start csv logger
	if logging==True:
		logger = dl.Logger()
		logger.create_outfile()
		logger.write_header(process_frame_count, n_inds, ifd=True, headings = True)

	# Use calculated shape to initialize writer
	if (recording==True) and (multi==False):
		dt = datetime.now()
		out = cv2.VideoWriter("generated_data/movies/"+str(dt.month)+"_"+str(dt.day)+"_"+str(dt.year)+"_"+str(dt.hour)+str(dt.minute)+'.avi',
								cv2.VideoWriter_fourcc(*'MJPG'),
								30,
								(vis.shape[1], vis.shape[0]),
								True)

	# Diff calculation initialization
	last = 0
	df = []
	colors = [(0,255,0),(0,255,255),(255,0,255),(255,255,255),(255,255,0),(255,0,0),(0,0,0)]

	# Initialize backup values for error-prone functions
	# Individual location(s) measured in the last and current step [x,y]
	meas_last = list(np.zeros((n_inds,4)))
	meas_now = list(np.zeros((n_inds,4)))

	last_good_list = None
	old_meas = [[meas_last, meas_now]]
	old_ind = [None]
	old_ifd = 0
	old_angles = [0,0]
	last_pulse_time = 0
	accum = [time.time(), None]



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

	# If not a Real Time experiment using FLIR or a post hoc experiment, init
	else:
		if multi==False:
			cap = cv2.VideoCapture(input_vidpath)
			if cap.isOpened() == False:
				sys.exit('Video file cannot be read! Please check input_vidpath to ensure it is correctly pointing to the video file')


	# Initialize time
	time0 = time.time()

	if FLIR==True:
		this=1

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

			#ROI Selection
			frame = mask_frame(frame, mask, r, mask_on, crop_on=True)

			#Resize & keep color frame, make BW frame
			cl_frame = cv2.resize(frame, None, fx = scaling, fy = scaling, interpolation = cv2.INTER_LINEAR)
			bw_frame = cv2.cvtColor(cl_frame, cv2.COLOR_BGR2GRAY)
			_, thresh = cv2.threshold(bw_frame, thresh_val,255,0)


			# Contour detection
			contours, meas_last, meas_now, num_valid_contours = detect_blobs(cl_frame,
																			 thresh,
																			 meas_last,
																			 meas_now,
																   			 colors)

			patches, _ = ip.extract_image_patches(cl_frame, [meas[0] for meas in meas_now], (20,20))

			#cv2.imshow('pat', patches[0])

			if len(meas_now)==len(patches):
				meas_now = [get_head_coords(meas_now[i], patches[i], 20) for i in range(len(meas_now))]
			else:
				pass

			angles, old_angles = metrics.relative_angle(meas_now, old_angles)

			ifd, old_ifd = metrics.ifd([[int(meas[0][0]), int(meas[0][1])] for meas in meas_now],
			 							old_ifd,
										0.5)
			ifd_mm = ifd*(mm2pixel)

			# Distance and heading based methods to ID fly
			# meas_now = preserve_id(ifd_mm, meas_now, meas_last, mm2pixel)

			if process_frame_count > 0:
				tracker.assign_detection(meas_now, ifd_mm)
			else:
				tracker = Tracker(n_inds, meas_now)

			meas_now = [track.get_coords() for track in tracker.list_of_tracks]



			pixel_meas = [[int(meas[0][0]), int(meas[0][1])] for meas in meas_now]
			#print(pixel_meas)


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

				if process_frame_count==0:
					history = dl.manage_history(None, pixel_meas, 200, init=True)

				else:
					try:
						history = dl.manage_history(history, pixel_meas, 200, init=False)

					except UnboundLocalError:
						history = dl.manage_history(None, pixel_meas, 200, init=True)


				# Drawing
				new_frame = draw_global_results(cl_frame,
												meas_now,
												colors,
												history,
												n_inds,
												DL=False,
												traces=True,
												heading=False)

				# Pass dictionary to data panel for visualization
				info_dict ={"frame_count": process_frame_count,
							"fps_calc": fps_calc,
							"logging":logging,
							"ifd": ifd_mm,
							"recording": recording,
							"heading": angles}

				vis = generate_info_panel(new_frame, info_dict, vis_shape)

				# Send light commands if doing an optogenetics expriment
				if rt_ifd==True:
					last_pulse_time, accum = ard.lights_IFD(ser,
															last_pulse_time,
															accum,
															ifd_mm,
															ifd_min,
															pulse_len,
															ifd_time_thresh,
															rt_LED_color,
															rt_LED_intensity)

				if (rt_pp==True) and ((time.time() - time0) >= rt_pp_delay):
					last_pulse_time = ard.lights_PP(ser,
													last_pulse_time,
													pulse_len,
													rt_pp_delay,
													rt_pp_period,
													rt_LED_color,
													rt_LED_intensity)
			else:
				new_frame = cl_frame
				info_dict = None
				vis =  generate_info_panel(new_frame, info_dict, vis_shape)


			if (multi==True):
				if (process_frame_count==0):
					frames_per_batch = get_frame_max(vis, process_max, process_min, n_processes)
					print('Got Max Frame: ', frames_per_batch)

				if (batch_frame_count <= frames_per_batch):
					try:
						frames.append(vis)
					except (AttributeError, NameError):
						frames=vis

					if batch_frame_count==frames_per_batch:
						frames = np.asarray(frames)
						np.save(frames_save_dir+'/frame_pkg_{}_{}.npy'.format((global_frame_count - batch_frame_count), (global_frame_count)), frames)
						print("Frames {} - {} processed".format((global_frame_count-batch_frame_count), global_frame_count))
						batch_frame_count=0
						frames = []

					if (global_frame_count >= process_max):
						frames = np.asarray(frames)
						np.save(frames_save_dir+'/frame_pkg_{}_{}.npy'.format((global_frame_count - batch_frame_count), (global_frame_count)), frames)
						print("Frames {} - {} processed".format((global_frame_count-batch_frame_count), global_frame_count))
						time.sleep(2)


			# Show present frame. Suppress to improve realtime speed
			#if multi==False:
				#cv2.imshow("FlyRT", vis)
				#cv2.imshow('t',thresh)

			# Write to .avi
			if (recording==True) and (multi==False):
				out.write(vis)

			# Write current measurment and calcs to CSV
			if (logging == True) and (all_present==True):
				logger.write_meas(process_frame_count, float(process_frame_count/30), pixel_meas[0:n_inds], ifd_mm, angles)

			# Increment multithreaded counts
			process_frame_count+=1
			if multi==True:
				batch_frame_count +=1
				global_frame_count = process_frame_count + process_min

			# FPS Calcs
			fps = True
			time2 = time.time()
			fps_calc = float(process_frame_count/(time2-time0))

			# GUI Stop Tracking Button
			stop_bit = config.stop_bit
			if cv2.waitKey(1) & (stop_bit==True):
				break

			# Break if multi-batch finishes before process limit
			if process_max is not None and (global_frame_count >= process_max):
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

	if (recording==True) and (multi==False):
		out.release()

	cv2.destroyAllWindows()
	cv2.waitKey()

	return None

if __name__=='__main__':

	# Quick sample case for testing, nothing special about these params
	mask, r, crop = launch_GUI('C:/Users/Patrick/Desktop/Video3.mp4')
	cd = {'path': 'C:/Users/Patrick/Desktop/Video3.mp4',
		  'record':False,
		  'log':False,
		  'scaling':0.8,
		  'multi':False,
		  'n_inds':2,
		  'heading':False,
		  'wings':False,
		  'IFD':True,
		  'arena_mms':40,
		  'thresh_val':80,
		  'mask_on':True,
		  'crop':crop,
		  'r':r,
		  'mask':mask,
		  'comm':None,
		  'baud':0,
		  'IFD_thresh':0,
		  'pulse_len':0,
		  'pulse_lockout':0,
		  'IFD_time_thresh':0,
		  'FLIR':False
		  }
	run(cd)
