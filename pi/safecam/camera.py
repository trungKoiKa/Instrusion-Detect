import cv2

def open_camera(cfg):
    cap = cv2.VideoCapture(cfg["device"])
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*cfg["fourcc"]))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg["height"])
    cap.set(cv2.CAP_PROP_FPS, cfg["fps"])
    return cap