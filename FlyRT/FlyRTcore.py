
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


def get_frame_max(img, multi_max, start_frame, n_processes):

	# Function to determine how many frames to keep per package given:
	# - Max frame for the current thread
	# - Start frame for current thread
	# - How many similar processes are running concurrently
	# Returns maximum number of frames before initiating new package

	# Frame range for entire thread
	expected_load = multi_max - start_frame

	# Amount of RAM to allocate to storing images in memory
	n_gb = 6
	n_bytes = img.nbytes
	frames_per_pack = ((1.0e9*n_gb)/n_processes)/n_bytes

	if frames_per_pack > expected_load:

		frames_per_pack = expected_load

	return int(frames_per_pack)


def detect_blobs(frame, thresh, meas_last, meas_now):

	# Function to find valid fly contours and return centroid coordinates
	# Returns new meas_now tuple with error handling to return last valid one if
	# 	no good measurements found

	# Generate contours with no discrimination
	_, contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# Discriminate contours based on area percentage of total frame. Flies are generally between 0.001 and 0.01
	good_contours = []

	for i, contour in enumerate(contours):

			if ((cv2.contourArea(contour) / (thresh.shape[0]**2)) < 0.01) and ((cv2.contourArea(contour) / (thresh.shape[0]**2)) > 0.0001):

				good_contours.append(contour)

	meas_last = meas_now.copy()
	del meas_now[:]


	# Second round of discrimination based on whether or not centroid is filled and if it is in masked "non-arena" area
	better_contours = []

	for i, contour in enumerate(good_contours):

		M = cv2.moments(contour)

		if M['m00'] != 0:

			cx = int(M['m10']/M['m00'])
			cy = int(M['m01']/M['m00'])
			vx,vy, _, _ = cv2.fitLine(contours[i], cv2.DIST_L2,0,0.01,0.01)

			center_coords = np.asarray([int(frame.shape[0]/2), int(frame.shape[1]/2)])
			dist_to_center = np.linalg.norm(center_coords - np.asarray([cx,cy]))

			if (dist_to_center > (frame.shape[0]/2)):

				pass

			elif [int(cx), int(cy)] in [[0,0], [0, frame.shape[0]], [frame.shape[0],0], []]:

				pass

			else:

				# Check whether contour is mostly filled or not
				area = cv2.contourArea(contour)
				edge = int(np.sqrt(area))
				h = int(edge/2)
				window = thresh[(cy - h):(cy + h), (cx - h):(cx + h)]

				if np.mean(window) != np.nan:

					if (np.mean(window) > 60) and (np.mean(window) < 160):

						better_contours.append(contour)

					try:

						meas_now.append([cx, cy, vx[0], vy[0]])

					except TypeError:

						meas_now.append([cx, cy, vx, vy])

					else:

						cx = 0
						cy = 0
						vx,vy,_,_ = 0,0,0,0

	return contours, meas_last, meas_now, len(better_contours)


def run(cd, start_frame=None, multi_max=None, n_processes=None):

	input_vidpath = str(cd['path'])
	recording =     bool(cd['record'])
	logging =       bool(cd['log'])
	scaling =       cd['scaling']

	multi = 		cd['multi']

	n_inds =        int(cd['n_inds'])
	heading =       bool(cd['heading'])
	wings =         bool(cd['wings'])
	ifd_on =        bool(cd['IFD'])
	arena_mms =     float(cd['arena_mms'])
	thresh_val =    cd['thresh_val']
	mask_on =       bool(cd['mask_on'])

	crop = 			cd['crop']
	r = 			cd['r']
	mask = 			cd['mask']

	comm =          str(cd['comm'])
	baud =          int(cd['baud'])
	ifd_min =       float(cd['IFD_thresh'])
	pulse_len =     float(cd['pulse_len'])
	pulse_lockout = float(cd['pulse_lockout'])
	ifd_time_thresh = float(cd['IFD_time_thresh'])

	rt_ifd = bool(cd['RT_IFD'])
	rt_pp = bool(cd['RT_PP'])
	rt_pp_delay = int(cd['RT_PP_Delay'])
	rt_pp_period = int(cd['RT_PP_Period'])

	rt_LED_red = bool(cd['LED_color_Red'])
	rt_LED_green = bool(cd['LED_color_Green'])
	rt_LED_intensity = int(cd['LED_intensity'])

	FLIR =          bool(cd['FLIR'])


	if rt_LED_red==True:
		rt_LED_color='red'
	if rt_LED_green==True:
		rt_LED_color='green'

	stop_bit = False
	mot=True
	p2a = 0.5
	roll_call = 0
	all_present = False

	if multi==True:

		frames=[]

		cwd = os.getcwd()

		frames_save_dir = cwd+'/frame_pkgs'
		multi_frame_count = 0

		FLIR = False

		cap = cv2.VideoCapture(input_vidpath)
		cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)


	if arena_mms is not None:
		mm2pixel = float(arena_mms/crop.shape[0])
	else:
		mm2pixel = 0.1

	if scaling is not None:
		scaling = float(scaling)
	else:
		scaling = 1.0

	if (rt_ifd) or (rt_pp==True):
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

	if multi==True:
		frame_count=start_frame

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

	colors = [(0,255,0),(0,255,255),(255,0,255),(255,255,255),(255,255,0),(0,0,255),(255,0,0),(0,0,0)]

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



	# FLIR Camera Zone
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

			# +++++++++++++++++++++++++++++++++++++++++
			# WarmUp Sequence
			warm_up_complete = False

			#Resize & keep color frame, make BW frame
			cl_frame = cv2.resize(frame, None, fx = scaling, fy = scaling, interpolation = cv2.INTER_LINEAR)
			bw_frame = cv2.cvtColor(cl_frame, cv2.COLOR_BGR2GRAY)

			_, thresh = cv2.threshold(bw_frame, thresh_val,255,0)


			# Contour detection
			contours, meas_last, meas_now, num_valid_contours = detect_blobs(cl_frame, thresh, meas_last, meas_now)


			if num_valid_contours==n_inds:
				if frame_count==0:
					all_present=True
				roll_call += 1
				if roll_call > 150:
					all_present=True

			else:
				if frame_count < 300:
					roll_call = 0




			if all_present==True:

				pixel_meas = [[int(meas[0]), int(meas[1])] for meas in meas_now]

				if frame_count==0:
					history = dl.manage_history(None, pixel_meas, 200, init=True)
				else:
					try:
						history = dl.manage_history(history, pixel_meas, 200, init=False)
					except UnboundLocalError:
						history = dl.manage_history(None, pixel_meas, 200, init=True)


				patches, _ = ip.extract_image_patches(cl_frame, pixel_meas, (40,40))

				#cv2.imshow('patch',patches[0])

				new_frame = draw_global_results(cl_frame, meas_now, colors, history, n_inds, DL=False, traces=True, heading=False)

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


				if rt_ifd==True:
					last_pulse_time, accum = ard.lights_IFD(ser, last_pulse_time, accum, ifd_mm, ifd_min, pulse_len, ifd_time_thresh, rt_LED_color, rt_LED_intensity)

				if (rt_pp==True) and ((time.time() - time0) >= rt_pp_delay):
					last_pulse_time = ard.lights_PP(ser, last_pulse_time, pulse_len, rt_pp_delay, rt_pp_period, rt_LED_color, rt_LED_intensity)





			else:
				new_frame = cl_frame
				info_dict = None
				vis =  generate_info_panel(new_frame, info_dict, vis_shape)


			if (multi==True):

				if (multi_frame_count==0):
					max_frame = get_frame_max(vis, multi_max, start_frame, n_processes)
					print('Got Max Frame: ', max_frame)
					bottom = frame_count


				if (multi_frame_count <= max_frame):

					try:
						frames.append(vis)
					except (AttributeError, NameError):
						frames=vis

					if multi_frame_count==max_frame:

						frames = np.asarray(frames)
						np.save(frames_save_dir+'/frame_pkg_{}_{}.npy'.format(bottom, (frame_count)), frames)

						multi_frame_count=0
						bottom = frame_count + start_frame
						frames = []




			# Show present frame. Suppress to improve realtime speed
			if multi==False:
				cv2.imshow("FlyRT", vis)

			# Write to .avi
			if recording==True:
				out.write(vis)

			# FPS Calcs
			fps = True
			time1 = time.time() - time0

			fps_calc = float(frame_count/time1)

			# Write current measurment and calcs to CSV
			if (logging == True) and (all_present==True):
				logger.write_meas(frame_count, float(frame_count/30), pixel_meas[0:n_inds], ifd_mm, angles)


			frame_count+=1
			if multi==True:
				multi_frame_count +=1

			stop_bit = config.stop_bit
			if cv2.waitKey(1) & (stop_bit==True):
				break

			if multi_max is not None and (frame_count >= multi_max):
				break

		else:
			break




	if FLIR==True:
		cam.stopCapture()
		cam.disconnect()
	else:
		cap.release()


	if logging==True:
		logger.close_writer()

	if recording==True:
		out.release()

	cv2.destroyAllWindows()
	cv2.waitKey()

	return None

if __name__=='__main__':

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
