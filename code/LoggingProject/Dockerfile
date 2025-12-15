# Use the official Python runtime image
FROM python:3.13  

ENV PYTHONUNBUFFERED=1 

# install autossh
RUN apt-get update && apt-get install -y \
    autossh \
    openssh-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /loggingproject
  
COPY requirements.txt .
 
RUN pip install -r requirements.txt
 
COPY . .

# create ssh directory and set perms
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

RUN apt-get update && apt-get install -y sshpass && rm -rf /var/lib/apt/lists/*

# Copy the startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh
EXPOSE 8000
EXPOSE 3307
# Use the startup script as entrypoint instead of direct CMD
ENTRYPOINT ["/start.sh"]

# OLD start method (no autossh)
# CMD python manage.py runserver 0.0.0.0:8000

