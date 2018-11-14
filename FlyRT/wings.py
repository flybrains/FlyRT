import numpy as np
import cv2

def get_head_coords(meas_now, img, patch_size = 40):

    centroid = meas_now[0]
    aux_points = meas_now[1:]

    global_top_left = [(centroid[0] - patch_size/2), (centroid[1] - patch_size/2)]

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, high = cv2.threshold(img, 142,255,0)
    _, low = cv2.threshold(img, 95,255,0)

    win = -1*(low - high - 255)
    win = np.expand_dims(win, 2)
    win = win.astype(np.uint8)

    _, contours, _ = cv2.findContours(win, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    my_contours = []
    for contour in contours:
        M = cv2.moments(contour)
        area = cv2.contourArea(contour)
        framesize = win.shape[0]*win.shape[1]*0.8
        if (area > 25) and (area < framesize):
            cx = np.float16(M['m10']/M['m00'])
            cy = np.float16(M['m01']/M['m00'])
            my_contours.append([[cx, cy], cv2.contourArea(contour), contour])

    areas = [elem[1] for elem in my_contours]
    col_idx = areas.index(max(areas))
    my_contour = my_contours[col_idx]

    win = cv2.cvtColor(win, cv2.COLOR_GRAY2BGR)
    colors = [(0,255,0),(0,0,255),(255,0,255),(255,255,255),(255,255,0),(255,0,0),(0,0,0)]

    cx, cy = my_contour[0]

    back_centroid = np.asarray([(global_top_left[0] + cx), (global_top_left[1] + cy)])


    point_dists = [np.linalg.norm(back_centroid - aux_points[i]) for i in range(2)]
    head_idx = point_dists.index(max(point_dists))
    head_point = aux_points[head_idx]

    new_meas_now = [centroid, head_point]

    #win = cv2.circle(win, (cx,cy), 1, (0,0,255), 3, cv2.LINE_AA )
    #win = cv2.drawContours(win, my_contour[-1], 0, (0,0,255), 3)


    # cv2.imshow('img', win)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return new_meas_now

# if __name__=="__main__"():
#     img = cv2.imread('C:/Users/Patrick/Desktop/crop2.jpg', 1)
#     centroid = []
#
#     get_head_coords(centroid, img, aux_points)
