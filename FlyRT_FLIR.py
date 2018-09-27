
import  numpy as np
import  pandas  as  pd
import scipy.signal
import cv2
import sys
import time
from os import system

import  tracktor  as tr

import image_patch as ip
import metrics
from global_draw import draw_global_results, add_thumbnails
import data_logger as dl
from data_logger import Logger
from select_flir_gui import flirGui
from info_panel import generate_info_panel
import config
import arduino_interface as ard
from set_threshold import set_threshold
import utils
from datetime import datetime
import serial
import flycapture2 as fc2

# Read and set configs
cd = config.get_config()

input_vidpath = cd['path']
recording = 	cd['record']
logging = 		cd['log']
arduino = 		cd['arduino']
comm = 			cd['comm']
baud = 			cd['baud']
display = 		cd['display']
n_inds = 		cd['n_inds']
heading = 		cd['heading']
wings = 		cd['wings']
ifd_on = 		cd['IFD']
scaling = 		cd['scaling']
auto_thresh = 	cd['auto_thresh']
IR = 			cd['IR']
mot = 			cd['mot']
p2a = 			cd['p2a']
flash_dur = 	cd['flash_dur']
lockout_t = 	cd['lockout_t']
ifd_min = 		cd['ifd_min']


#Define parameters
colours = [(0,255,0),(0,255,255),(255,0,255),(255,255,255),(255,255,0),(0,0,255),(255,0,0),(0,0,0)]

# Individual location(s) measured in the last and current step [x,y]
meas_last = list(np.zeros((n_inds,4)))
meas_now = list(np.zeros((n_inds,4)))

system('cls')

# Launch ROI selection GUI
mask, r, crop = flirGui(0)

# Launch threshold selector utility
thresh_val = set_threshold(crop, auto_thresh, IR)

cap = fc2.Context()
cap.connect(*cap.get_camera_from_index(0))
cap.set_video_mode_and_frame_rate(fc2.VIDEOMODE_640x480Y8, fc2.FRAMERATE_30)
m, f = cap.get_video_mode_and_frame_rate()
p = cap.get_property(fc2.FRAME_RATE)
cap.set_property(**p)
cap.start_capture()


# Conditionally start Arduino Serial communication
if arduino==True:
	ser = ard.init_serial(comm, baud)
	time.sleep(2)

# Determine final output frame size
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
	logger.write_header(frame_count, n_inds)


# Use calculated shape to initialize writer
if recording==True:
	dt = datetime.now()
	out = cv2.VideoWriter("generated_data/movies/"+str(dt.month)+"_"+str(dt.day)+"_"+str(dt.year)+"_"+str(dt.hour)+str(dt.minute)+'.avi', cv2.VideoWriter_fourcc(*'MJPG'), 30, (vis.shape[1], vis.shape[0]), True)

# Diff calculation initialization
last = 0
df = []

# Initialize backup values for error-prone functions
last_good_list = None
old_meas = [[meas_last, meas_now]]
old_ind = [None]
old_ifd = 0
old_angles = [0,0]

# Pause and wait for user start after ROI select
#system('cls')


go_bit = input("Start Tracking:[Y/n]?")
if go_bit=='y' or go_bit=="Y":

	# Initialize time
	time0 = time.time()

	while(True):
	    # Capture frame-by-frame
		img = fc2.Image()
		cap.retrieve_buffer(img)
		frame = np.array(img)
		frame = np.expand_dims(frame, 2)

		cl_frame = cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)

		cl_frame = cv2.resize(cl_frame, None, fx = scaling, fy = scaling, interpolation = cv2.INTER_LINEAR)
		bw_frame = cv2.cvtColor(cl_frame, cv2.COLOR_BGR2GRAY)

		# Get thresholded frame using modified tracktor library
		thresh = tr.colour_to_thresh(bw_frame, thresh_val)

		# Contour detection
		final, contours, meas_last, meas_now = tr.detect_and_draw_contours(cl_frame, thresh, meas_last, meas_now, p2a)

		# Operations to preserve identity and extract centroid coords
		row_ind, col_ind, old_meas, old_ind = tr.hungarian_algorithm(meas_last, meas_now, old_meas, old_ind)
		final, meas_now, df = tr.reorder_and_draw(final, colours, n_inds, col_ind, meas_now, df, mot, frame_count)
		pixel_meas = [[int(meas[0]), int(meas[1])] for meas in meas_now]


		# Manage centroid tracking history 
		if frame_count==0:
			history = dl.manage_history(None, pixel_meas, 200, init=True)
		else:
			history = dl.manage_history(history, pixel_meas, 200, init=False)


		# Create patches and Pass/Fail signal for each detected centroid
		#patches, rets = ip.extract_image_patches(cl_frame, pixel_meas, [40,40])
		
		global_results = None
		new_frame = draw_global_results(cl_frame, meas_now, colours, history, DL=False, traces=True, heading=False)

		#new_frame = add_thumbnails(cl_frame, patches, results, colours)

		ifd, old_ifd = metrics.ifd(pixel_meas, old_ifd, 0.5)

		#angles, old_angles = metrics.relative_angle(meas_now, old_angles)

		info_dict ={"frame_count": frame_count,
					"fps_calc": fps_calc,
					"logging":logging,
					"ifd": ifd,
					"recording": recording}
					#"heading": angles}
		
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
			logger.write_meas(frame_count, time1, pixel_meas[0:n_inds], ifd)


		if fps==True:
			#print(fps_calc)
			pass


		frame_count+=1
		# Video keyboard interrupt
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break


	logger.close_writer()
	
	cap.stop_capture()
	cap.disconnect()

	if recording==True:
		out.release()
	cv2.destroyAllWindows()
	cv2.waitKey()