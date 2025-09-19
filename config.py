import os
from gevent import queue
from gevent.queue import Queue
from enum import Enum
from enum import IntEnum


class Config:
    SECRET_KEY = "admin"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    
    
    CURRENT_PROCESS = None
    PROCESSING_CANCELLED = False



class qmanager:
    
    manual_queue = Queue()
    csv_queue = Queue()
    
    
class Priority(Enum):
    HIGH = 1
    LOW = 2

class ProcessingState:
    def __init__(self):
        self.priority_queue = queue.PriorityQueue()
        self.processing_worker = None
        self.csv_processing = False
        self.held_csv_items = []

        
processing_state = ProcessingState()

class Priority(IntEnum):
    HIGH = 1    
    LOW = 2     
