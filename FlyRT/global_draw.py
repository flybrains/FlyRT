import numpy as np
import cv2


def draw_global_results(img, meas_now, colours, history, n_inds, DL = False, wings=False, traces=True, heading=True):
    if DL==True:
        for idx, idv in enumerate(global_results):
            head = (idv[0][0], idv[0][1])
            tail = (idv[3][0], idv[3][1])

            if wings==True:
                for i in range(3):
                    new_frame = cv2.line(img, head, tail, colours[i], thickness=2)
            else:
                new_frame = cv2.line(img, head, tail, colours[idx], thickness=2)

            new_frame = cv2.putText(img, str(idx), (head[0] + 5, head[1] + 5), cv2.FONT_HERSHEY_DUPLEX , 0.8, colours[idx], 1, cv2.LINE_AA)
            
            if traces==True:
                for centroid in history:
                    if len(centroid)==len(global_results):
                        new_frame = cv2.circle(img, (centroid[idx][0], centroid[idx][1]), 1, colours[idx], -1, cv2.LINE_AA)
                    else:
                        pass
        return new_frame
        
    
    for i in range(n_inds):
        
        if len(history)>0:
            try:
                new_frame = cv2.putText(img, str(i+1), (history[-1][i][0] + 5, history[-1][i][1] + 5), cv2.FONT_HERSHEY_DUPLEX , 0.8, colours[i], 1, cv2.LINE_AA)
            except IndexError:
                new_frame = img

        if traces==True:
            for centroid in history:
                if len(centroid)==2:
                    new_frame = cv2.circle(img, (centroid[i][0], centroid[i][1]), 1, colours[i], -1, cv2.LINE_AA)
                else:
                    pass

        if heading==True:
            try:
                cx = meas_now[i][0]
                cy = meas_now[i][1]
                vx = meas_now[i][2]
                vy = meas_now[i][3]

                rows, cols = img.shape[:2]

                if vx==0:
                    vx = 0.0001
                if vy==0:
                    vy = 0.0001


                pt1 = (int(cx - 150*vx), int(cy - 150*vy))
                pt2 = (int(cx + 150*vx), int(cy + 150*vy))

                new_frame = cv2.line(new_frame, pt1, pt2, colours[i], 2)
            
            except IndexError:
                    pass


    return new_frame



def add_thumbnails(img, patches, results, colours, wings=False):
    patch_list = []

    for idx, idv in enumerate(results):
        head = (idv[0][0], idv[0][1])
        tail = (idv[3][0], idv[3][1])

        new_patch = cv2.putText(patches[idx], str(idx), (10, 20), cv2.FONT_HERSHEY_DUPLEX , 0.8, colours[idx], 1, cv2.LINE_AA)
        patch_list.append(new_patch)

    if len(patch_list) != 0:
      frames = patch_list[0] 
      for patch in patch_list[1:]:
          frames = np.concatenate((frames, patch), axis=1)

    img[0:frames.shape[0], 0:frames.shape[1]] = frames

    return img