from os import system
import cv2

def auto_thresholder():
	return None

def set_threshold(img, auto_thresh, IR):
	
	if img.shape[2]==3:
		img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	if IR==True:
		pass
		# Color inversion?

	if auto_thresh==True:
		thresh_val = auto_thresholder()

	system('cls')

	thresh_val = 80

	setting=True

	print("\n=============================================================")
	print("Set Threshold")
	print("=================================================================")
	print(" - Type a new value between [0, 255] and press ENTER to try new value")
	print(''' - Good threshold values are low enough that only animals are seen, and high enough that the animals are singular, fully-connected blobs.''')

	def show_img(thresh_val, thresh_img):
		cv2.imshow("Threshold Value: {}".format(thresh_val), thresh_img)
		cv2.waitKey(0)
		cv2.destroyAllWindows()

	def take_args(thresh_val):

		print(" - Current Threshold Value is: {}".format(thresh_val))
		print(" - Try new value? [Val + ENTER] or Save current val? [S/s + ENTER]")
		print("                   * Note: Must close visualization window before entering any new command.")

		ret, thresh_img = cv2.threshold(img, thresh_val, 255,0)
		
		show_img(thresh_val, thresh_img)

		new_val = input()

		system('cls')

		if (new_val == "S") or (new_val=="s"):
			setting=False
		else:
			thresh_val=int(new_val)
			setting=True
	
		print("Value Set to {}".format(thresh_val))

		return setting, thresh_val, thresh_img


	while(setting==True):
		
		setting, thresh_val, thresh_img = take_args(thresh_val)
		

	return thresh_val


