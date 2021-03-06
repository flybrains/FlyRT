import cv2
import numpy as np
import numpy.ma as ma
import time
#import PyCapture2


def selectROI(input_vidpath):

	# Wait a second to let capture start
	time.sleep(1)
	cap = cv2.VideoCapture(input_vidpath)
	time.sleep(1)

	ret, frame = cap.read()
	if ret==True:
		im = frame.copy()
	cap.release()

	r = cv2.selectROI(im, fromCenter=False)
	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)

	cv2.destroyAllWindows()

	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)

	spread = int(r[3]*(0.52))

	a = cx - spread
	b = cx + spread
	c = cy - spread
	d = cy + spread

	crop =  im[c:d, a:b]

	return r, crop


def selectROIFLIR(idx):

	bus = PyCapture2.BusManager()
	cam = PyCapture2.Camera()
	uid = bus.getCameraFromIndex(0)
	cam.connect(uid)

	def capIm():
		try:
			img = cam.retrieveBuffer()
		except PyCapture2.Fc2error as fc2Err:
			print("Error retrieving buffer :", fc2Err)
			return False, []
		data = np.asarray(img.getData(), dtype=np.uint8)
		data = data.reshape((img.getRows(), img.getCols()))

		return True, data

	cam.startCapture()

	ret, im = capIm()
	im = im.copy()
	im = np.expand_dims(im, 2)

	r = cv2.selectROI(im, fromCenter=False)
	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)

	mask = np.ones((im.shape[0], im.shape[1]), np.uint8)
	mask = cv2.circle(mask, (cx,cy), int(r[3]/2), (255,255,255), -1)
	mask = np.where(mask==0).astype(bool)

	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)

	spread = int(r[3]*(0.52))
	a = cx - spread
	b = cx + spread
	c = cy - spread
	d = cy + spread

	crop =  im[c:d, a:b]
	crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
	cam.stopCapture()
	cam.disconnect()
	cv2.destroyAllWindows()

	return mask, r, crop

def crop_frame(frame, r):
	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)
	spread = int(r[3]*(0.52))
	a = cx - spread
	b = cx + spread
	c = cy - spread
	d = cy + spread
	new_frame =  frame[c:d, a:b]

	return new_frame
