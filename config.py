
FLYSORT_CONFIG = {
	
	# I/O
	"path":		"C:/Users/Patrick/Desktop/fly_videos/test1.mp4",
	"record": 	True,
	"log": 		True,
	"arduino":	False,
	"display":	True,

	# Arduino Options
	"comm": 	"COM3",
	"baud":		9600,

	# Trial Parameters
	'auto_thresh': False,
	"n_inds": 2,

	# Animal Metrics
	"heading":	False,
	"wings":	False,
	"IFD":		True
}

# ======================================================================================
# Description:
# ---------------------------------------------------------------------------------------
# I/O:
# 	live:			0 if experiment is realtime, full path if using on pre-recorded video.
# 						Ex: "C:\Users\Patrick\Videos\my_video.mp4"  Must be in quotes!
# 	record:			True to save output to .avi video file for review
# 	log:			True to save data to .csv file
# 	display:		True to show realtime display. Recommended for visualizing and debugging
# 					system performance. Suppressing can have significant runtime-speedup if you
# 					are confident in the performance.
# ---------------------------------------------------------------------------------------
# Arduino:
# 	comm:			Comm port for arduino
# 	baud:			baudrate for arduino
# ---------------------------------------------------------------------------------------
# Trial Parameters:
# 	auto_thresh:	False indicates the user will provide a threshold value for fly detection.
# 					True indicates this value will be automatically calculated by FlySORT program
#	n_inds:			Number of flies in recording
# ---------------------------------------------------------------------------------------
# Animal Metrics:
# 	heading:		True to calculate/log relative headings
# 	wings:			True to calculate/log wing angles
#	IFD:			True to calculate/log interfly distance
# ======================================================================================

def get_config():
	return FLYSORT_CONFIG