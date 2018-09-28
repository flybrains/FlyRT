
FLYSORT_CONFIG = {
	
	# I/O
	"path":			"C:/Users/Patrick/Desktop/vids_to_analyze/full_no_cop.mp4",
	"record": 		True,
	"log": 			True,
	"arduino":		True,
	"display":		True,
	"scaling":		0.99,

	# Arduino Options
	"comm": 		"COM3",
	"baud":			9600,

	# Video Parameters
	'auto_thresh': 	False,
	"n_inds": 		2,
	"mot": 			True,
	"IR":			True,

	# Animal Metrics
	"heading":		False,
	"wings":		False,
	"IFD":			True,
	"p2a":			0.5,

	# Experiment Parameters
	'ifd_min':		90,
	'flash_dur':	1,
	'lockout_t':	10

}

# ==============================================================================================
# Description:
# ----------------------------------------------------------------------------------------------
# I/O:
# 	live:			0 if experiment is realtime, full path if using on pre-recorded video.
# 						Ex: "C:\Users\Patrick\Videos\my_video.mp4"  Must be in quotes!
# 	record:			True to save output to .avi video file for review
# 	log:			True to save data to .csv file
# 	display:		True to show realtime display. Recommended for visualizing and debugging
# 					system performance. Suppressing can have significant runtime-speedup if you
# 					are confident in the performance.
#	scaling:		Float value by which to reduce input image size to improve speed
# ----------------------------------------------------------------------------------------------
# Arduino:
# 	comm:			Comm port for arduino
# 	baud:			baudrate for arduino
# ----------------------------------------------------------------------------------------------
# Trial Parameters:
# 	auto_thresh:	False indicates the user will provide a threshold value for fly detection.
# 					True indicates this value will be automatically calculated by FlySORT program
#	n_inds:			Number of flies in recording
# 	mot:			Tracktor Parameter
# -----------------------------------------------------------------------------------------------
# Animal Metrics:
# 	heading:		True to calculate/log relative headings
# 	wings:			True to calculate/log wing angles
#	IFD:			True to calculate/log interfly distance
#	p2a:			Float value perimeter to area ration. Meant to discriminate non-fly blobs
# ================================================================================================

def get_config():
	return FLYSORT_CONFIG