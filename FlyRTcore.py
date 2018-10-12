
import  numpy as np
import  pandas  as  pd
import scipy.signal
import cv2
import sys
import time
from os import system
import config

import  tracktor  as tr

import metrics
from global_draw import draw_global_results, add_thumbnails
import data_logger as dl
from data_logger import Logger
from select_arena_roi import launch_GUI, mask_frame
from info_panel import generate_info_panel
import arduino_interface as ard
import utils
from datetime import datetime
import serial

def run(cd, crop, r, mask):

	# Read and set configs

	input_vidpath = str(cd['path'])
	recording = 	bool(cd['record'])
	logging = 		bool(cd['log'])

	arduino = 		bool(cd['arduino'])
	comm = 			str(cd['comm'])
	baud = 			int(cd['baud'])

	n_inds = 		int(cd['n_inds'])
	heading = 		bool(cd['heading'])
	wings = 		bool(cd['wings'])
	ifd_on = 		bool(cd['IFD'])
	scaling = 		cd['scaling']
	FLIR = 			bool(cd['FLIR'])

	arena_mms = 	float(cd['arena_mms'])
	thresh_val = 	cd['thresh_val']
	mask_on = 		bool(cd['mask_on'])

	stop_bit = False
	mot=True
	p2a = 0.5

	if arena_mms is not None:
		mm2pixel = float(arena_mms/crop.shape[0])
	else:
		mm2pixel = 0.1

	if scaling is not None:
		scaling = float(scaling)
	else:
		scaling = 1.0

	if arduino==True:
		ser = ard.init_serial(comm, baud)
		time.sleep(2)

	max_pixel = 210*2

	# Determine final output frame size
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
	frame_count = 0
	fps_calc = 0

	# Start csv logger
	if logging==True:
		logger = dl.Logger()
		logger.create_outfile()
		logger.write_header(frame_count, n_inds, ifd=True, headings = True)


	# Use calculated shape to initialize writer
	if recording==True:
		dt = datetime.now()
		out = cv2.VideoWriter("generated_data/movies/"+str(dt.month)+"_"+str(dt.day)+"_"+str(dt.year)+"_"+str(dt.hour)+str(dt.minute)+'.avi', cv2.VideoWriter_fourcc(*'MJPG'), 30, (vis.shape[1], vis.shape[0]), True)



	# Diff calculation initialization
	last = 0
	df = []

	colours = [(0,255,0),(0,255,255),(255,0,255),(255,255,255),(255,255,0),(0,0,255),(255,0,0),(0,0,0)]

	# Initialize backup values for error-prone functions
	# Individual location(s) measured in the last and current step [x,y]
	meas_last = list(np.zeros((n_inds,4)))
	meas_now = list(np.zeros((n_inds,4)))

	last_good_list = None
	old_meas = [[meas_last, meas_now]]
	old_ind = [None]
	old_ifd = 0
	old_angles = [0,0]


	## Open video
	if FLIR==True:
		cap = fc2.Context()
		cap.connect(*cap.get_camera_from_index(0))
		cap.set_video_mode_and_frame_rate(fc2.VIDEOMODE_640x480Y8, fc2.FRAMERATE_30)
		m, f = cap.get_video_mode_and_frame_rate()
		p = cap.get_property(fc2.FRAME_RATE)
		cap.set_property(**p)
		cap.start_capture()
	else:
		cap = cv2.VideoCapture(input_vidpath)
		if cap.isOpened() == False:
			sys.exit('Video file cannot be read! Please check input_vidpath to ensure it is correctly pointing to the video file')


	# Initialize time
	time0 = time.time()

	if FLIR==True:
		this=1

	while(True):
	    # Capture frame-by-frame
		
		if FLIR==True:
			ret = True
			img = fc2.Image()
			cap.retrieve_buffer(img)
			frame = np.array(img)
			frame = np.expand_dims(frame, 2)
			frame = cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)
			this+=1
		else:	
			ret, frame = cap.read()
			this = cap.get(1)
			

		if ret == True:

			#ROI Selection
			frame = mask_frame(frame, mask, r, mask_on, crop_on=True)

			# +++++++++++++++++++++++++++++++++++++++++
			# WarmUp Sequence
			warm_up_complete = False

			#Resize & keep color frame, make BW frame
			cl_frame = cv2.resize(frame, None, fx = scaling, fy = scaling, interpolation = cv2.INTER_LINEAR)
			bw_frame = cv2.cvtColor(cl_frame, cv2.COLOR_BGR2GRAY)

			# Get thresholded frame using modified tracktor library
			thresh = tr.colour_to_thresh(bw_frame, thresh_val)

			# Contour detection
			final, contours, meas_last, meas_now = tr.detect_and_draw_contours(cl_frame, thresh, meas_last, meas_now, p2a)

			# Operations to preserve identity and extract centroid coords
			row_ind, col_ind, old_meas, old_ind = tr.hungarian_algorithm(meas_last, meas_now, old_meas, old_ind)
			final, meas_now, df = tr.reorder_and_draw(final, colours, n_inds, col_ind, meas_now, df, mot, this)
			pixel_meas = [[int(meas[0]), int(meas[1])] for meas in meas_now]


			# Manage centroid tracking history 
			if frame_count==0:
				history = dl.manage_history(None, pixel_meas, 200, init=True)
			else:
				history = dl.manage_history(history, pixel_meas, 200, init=False)

			
			global_results = None
			new_frame = draw_global_results(cl_frame, meas_now, colours, history, DL=False, traces=True, heading=False)

			#new_frame = add_thumbnails(cl_frame, patches, results, colours)

			ifd, old_ifd = metrics.ifd(pixel_meas, old_ifd, 0.5)

			ifd_mm = ifd*(mm2pixel)

			angles, old_angles = metrics.relative_angle(meas_now, old_angles)

			info_dict ={"frame_count": frame_count,
						"fps_calc": fps_calc,
						"logging":logging,
						"ifd": ifd_mm,
						"recording": recording,
						"heading": angles}

			vis = generate_info_panel(new_frame, info_dict, vis_shape)

			if arduino==True:
				ard.lights(ser, ifd, ifd_min)
				

			# Show present frame. Suppress to improve realtime speed
			cv2.imshow("FlySORT", vis)
			
			# Write to .avi
			if recording==True:
				out.write(vis)


			# FPS Calcs
			fps = True
			time1 = time.time() - time0
			
			fps_calc = float(frame_count/time1)

			# Write current measurment and calcs to CSV
			if logging == True:
				logger.write_meas(frame_count, float(frame_count/30), pixel_meas[0:n_inds], ifd_mm, angles)


			frame_count+=1

			stop_bit = config.stop_bit
			if cv2.waitKey(1) & (stop_bit==True):
				break

		else:
			break


	if FLIR==True:
		cap.stop_capture()
		cap.disconnect()
	else:
		cap.release()

	logger.close_writer()
	
	if recording==True:
		out.release()

	cv2.destroyAllWindows()
	cv2.waitKey()

	return None



