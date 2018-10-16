
import  numpy as np
import  pandas  as  pd
import scipy.signal
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
import cv2
import sys
import time
from os import system
import config

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
import PyCapture2

def color_to_thresh(frame, thresh_val):
    ret, thresh = cv2.threshold(frame, thresh_val,255,0)
    return thresh

def detect_blobs(frame, thresh, meas_last, meas_now, p2a_thresh):
    img, contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    final = frame.copy()

    i = 0
    meas_last = meas_now.copy()

    del meas_now[:]


    while i < len(contours):
        area = cv2.contourArea(contours[i])

        if area==0:
            area=0.001
        p2a = float((cv2.arcLength(contours[i],True))/(area))

        if (p2a > p2a_thresh):
            del contours[i]

        elif (area > 1000):
            del contours[i]

        else:
            M = cv2.moments(contours[i])
            if M['m00'] != 0:
                cx = M['m10']/M['m00']
                cy = M['m01']/M['m00']

                vx,vy, _, _ = cv2.fitLine(contours[i], cv2.DIST_L2,0,0.01,0.01)

            else:
                cx = 0
                cy = 0

                vx,vy,_,_ = 0,0,0,0

            try:
                meas_now.append([cx, cy, vx[0], vy[0]])
            except TypeError:
                meas_now.append([cx, cy, vx, vy])

            i += 1

    return final, contours, meas_last, meas_now


def hungarian_algorithm(meas_last, meas_now, old_meas, old_ind):

    meas_last = np.array(meas_last)
    meas_now = np.array(meas_now)

    if meas_now.shape != meas_last.shape:
        if meas_now.shape[0] < meas_last.shape[0]:
            while meas_now.shape[0] != meas_last.shape[0]:
                meas_last = np.delete(meas_last, meas_last.shape[0]-1, 0)
        else:
            try:
                result = np.zeros(meas_now.shape)
                result[:meas_last.shape[0],:meas_last.shape[1]] = meas_last
                meas_last = result
            except IndexError:
                print("Handle: IndexError")
                meas_last = old_meas[-1][0]

    meas_last = list(meas_last)
    meas_now = list(meas_now)

    # Hacky way to keep shape errors from occurring by using last valid entry
    old_meas.append([meas_last, meas_now])

    if len(old_meas)>2:
        old_meas.pop(0)

    if (len(meas_last) == 0):
        meas_last = old_meas[-1][0]

    if len(meas_now)==0:
        meas_now = old_meas[-1][1]

    try:
        cost = cdist(meas_last, meas_now)
        row_ind, col_ind = linear_sum_assignment(cost)

        old_ind.append([row_ind, col_ind])
        if len(old_ind)>3:
            old_ind.pop(0)

    except ValueError:
        print("Handle: ValueError")
        row_ind, col_ind = old_ind[-1][0], old_ind[-1][1]

    return row_ind, col_ind, old_meas, old_ind


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


	def capIm():
		try:
			img = cam.retrieveBuffer()
		except PyCapture2.Fc2error as fc2Err:
			print("Error retrieving buffer :", fc2Err)
			return False, []

		data = np.asarray(img.getData(), dtype=np.uint8)
		data = data.reshape((img.getRows(), img.getCols()))

		return True, data


	## Open video
	if FLIR==True:
		bus = PyCapture2.BusManager()
		cam = PyCapture2.Camera()
		uid = bus.getCameraFromIndex(0)
		cam.connect(uid)

		cam.startCapture()
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


			thresh = color_to_thresh(bw_frame, thresh_val)

			# Contour detection
			final, contours, meas_last, meas_now = detect_blobs(cl_frame, thresh, meas_last, meas_now, p2a)

			# Operations to preserve identity and extract centroid coords
			row_ind, col_ind, old_meas, old_ind = hungarian_algorithm(meas_last, meas_now, old_meas, old_ind)
			pixel_meas = [[int(meas[0]), int(meas[1])] for meas in meas_now]


			# Manage centroid tracking history 
			if frame_count==0:
				history = dl.manage_history(None, pixel_meas, 200, init=True)
			else:
				history = dl.manage_history(history, pixel_meas, 200, init=False)

			
			global_results = None
			new_frame = draw_global_results(cl_frame, meas_now, colors, history, DL=False, traces=True, heading=False)

			#new_frame = add_thumbnails(cl_frame, patches, results, colors)

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



