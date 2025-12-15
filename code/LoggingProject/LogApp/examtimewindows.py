from django.utils import timezone
from datetime import timedelta


exam_end_buffer = timedelta(minutes=30)
checkin_window = timedelta(minutes=30)