import os
import cv2
import numpy as np

print("DISPLAY:", os.environ.get("DISPLAY"), flush=True)
print("WAYLAND_DISPLAY:", os.environ.get("WAYLAND_DISPLAY"), flush=True)
print("SESSION:", os.environ.get("XDG_SESSION_TYPE"), flush=True)

image = np.zeros((240, 400, 3), dtype=np.uint8)

cv2.imshow("Display test", image)
cv2.waitKey(0)
cv2.destroyAllWindows()