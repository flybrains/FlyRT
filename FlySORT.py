
import  numpy as np
import  pandas  as  pd
import scipy.signal
import cv2
import sys
import time
from os import system
import argparse

import  tracktor  as tr

import image_patch as ip
import metrics
from global_draw import draw_global_results, add_thumbnails
from data_logging import TrialLogger, manage_history
from select_arena_roi import launch_GUI, mask_frame
from info_panel import generate_info_panel

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--rec", help="Save video to .AVI file? [T/F]", required=True)
parser.add_argument("-l", "--log", help="Save data to .CSV file? [T/F]", required=True)
parser.add_argument("--n", help="Total number of animals in trial [int]", required=True)
args = vars(parser.parse_args())

if (args['rec'] == "T") or (args['rec'] == "t") or (args['rec'] == "true") or (args['rec'] == "True"):
	recording = True
else:
	recording = False

if (args['log'] == "T") or (args['log'] == "t") or (args['log'] == "true") or (args['log'] == "True"):
	logging = True
else:
	recording = False

n_inds = int(args['n'])


#Define parameters
colours = [(0,255,0),(0,255,255),(255,0,255),(255,255,255),(255,255,0),(0,0,255),(255,0,0),(0,0,0)]

#n_inds = 2				# Number of individual flies
thresh_val = 85			# Threhold value, to be calculated automatically later
scaling = 0.8			# Scaling: Reduce dimensions
p2a = 0.6				# Perimeter to area ratio to eliminate non-fly contours
mot=True

# name of source video and paths
video = 'short'
input_vidpath = 'C:/Users/Patrick/Desktop/fly_videos/' + video + '.mp4'
output_vidpath = 'C:/Users/Patrick/Documents/fly_sort/' + video + '_tracked.avi'
output_filepath = 'C:/Users/Patrick/Documents/fly_sort/' + video + '_tracked.csv'

# Individual location(s) measured in the last and current step [x,y]
meas_last = list(np.zeros((n_inds,4)))
meas_now = list(np.zeros((n_inds,4)))

# Initialize 
time0 = time.time()
frame_count = 0
fps_calc = 0

system('cls')

# Launch ROI selection GUI
mask, r, crop = launch_GUI(input_vidpath)

system('cls')

## Open video
cap = cv2.VideoCapture(input_vidpath)
if cap.isOpened() == False:
    sys.exit('Video file cannot be read! Please check input_vidpath to ensure it is correctly pointing to the video file')


# Determine final output frame size
info = np.zeros((crop.shape[0], int((crop.shape[0])*0.5), 3), np.uint8)
h1, w1 = crop.shape[:2]
h2, w2 = info.shape[:2]

vis = np.zeros((max(h1, h2), w1+w2,3), np.uint8)
vis[:h1, :w1,:3] = crop
vis[:h2, w1:w1+w2,:3] = info

vis = cv2.resize(vis, None, fx = scaling, fy = scaling, interpolation = cv2.INTER_LINEAR)
vis_shape = vis.shape

# Use calculated shape to initialize writer
if recording==True:
	out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'MJPG'), 30, (vis.shape[1], vis.shape[0]), True)

# Diff calculation initialization
last = 0
df = []

# Initialize backup values for error-prone functions
last_good_list = None
old_meas = [[meas_last, meas_now]]
old_ind = [None]
old_ifd = 0
old_angles = [0,0]

# Start csv logger
if logging==True:
	logger = TrialLogger()
	logger.create_outfile()
	logger.write_header(frame_count, n_inds)

# Pause and wait for user start after ROI select
#system('cls')
go_bit = input("Start Tracking:[Y/n]?")
if go_bit=='y' or go_bit=="Y":


	while(True):
	    # Capture frame-by-frame
		ret, frame = cap.read()
		this = cap.get(1)
		
		if ret == True:

			#ROI Selection
			frame = mask_frame(frame, mask, r, mask_on=False, crop_on=True)

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
				history = manage_history(None, pixel_meas, 200, init=True)
			else:
				history = manage_history(history, pixel_meas, 200, init=False)



			# Create patches and Pass/Fail signal for each detected centroid
			#patches, rets = ip.extract_image_patches(cl_frame, pixel_meas, [40,40])
			
			global_results = None
			new_frame = draw_global_results(cl_frame, meas_now, colours, history, DL=False, traces=True, heading=False)

			#new_frame = add_thumbnails(cl_frame, patches, results, colours)

			ifd, old_ifd = metrics.ifd(pixel_meas, old_ifd, 0.5)

			angles, old_angles = metrics.relative_angle(meas_now, old_angles)

			info_dict ={"frame_count": frame_count,
						"fps_calc": fps_calc,
						"logging":logging,
						"ifd": ifd,
						"recording": recording,
						"heading": angles}

			vis = generate_info_panel(new_frame, info_dict, vis_shape)

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
				logger.write_meas(frame_count, time1, pixel_meas, ifd)


			if fps==True:
				#print(fps_calc)
				pass


			frame_count+=1
			# Video keyboard interrupt
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break
		else:
			break

	cap.release()
	if recording==True:
		out.release()
	cv2.destroyAllWindows()
	cv2.waitKey()