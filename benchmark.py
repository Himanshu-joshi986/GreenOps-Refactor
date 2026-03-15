from codecarbon import EmissionsTracker
import time
import numpy as np

tracker = EmissionsTracker()
tracker.start()
#Training Workload goes here  

time.sleep(2)   

tracker.stop()