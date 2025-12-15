#!/bin/bash

# SSH tunnel configuration
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
LOCAL_PORT="${LOCAL_PORT:-3307}"
SSH_USER="${SSH_USER:-passthrough}"
SSH_HOST="${SSH_HOST:-98.84.13.90}"
SSH_PORT="${SSH_PORT:-22}"

# AutoSSH configuration
AUTOSSH_POLL="${AUTOSSH_POLL:-60}"
AUTOSSH_GATETIME="${AUTOSSH_GATETIME:-30}"
AUTOSSH_FIRST_POLL="${AUTOSSH_FIRST_POLL:-30}"

export AUTOSSH_POLL AUTOSSH_GATETIME AUTOSSH_FIRST_POLL

echo "Starting SSH tunnel setup with autossh..."

# Check if sshpass is available
if ! command -v sshpass &> /dev/null; then
    echo "ERROR: sshpass is not installed!"
    echo "Please install it first:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install hudochenkov/sshpass/sshpass"
    elif command -v apt-get &> /dev/null; then
        echo "  sudo apt-get install -y sshpass"
    elif command -v yum &> /dev/null; then
        echo "  sudo yum install -y sshpass"
    elif command -v dnf &> /dev/null; then
        echo "  sudo dnf install -y sshpass"
    else
        echo "  Install sshpass using your system's package manager"
    fi
    exit 1
fi

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add SSH host to known_hosts to avoid interactive prompt
echo "Adding $SSH_HOST to known_hosts..."
ssh-keyscan -H -p $SSH_PORT $SSH_HOST >> ~/.ssh/known_hosts 2>/dev/null

# Function to check if tunnel is working
check_tunnel() {
    nc -z localhost $LOCAL_PORT 2>/dev/null
    return $?
}

# Start autossh tunnel in background
echo "Starting autossh tunnel: localhost:$LOCAL_PORT -> $SSH_HOST -> $DB_HOST:$DB_PORT"

sshpass -p 'SwiftCheckin4SDP!' autossh -M 0 \
    -o "StrictHostKeyChecking=no" \
    -o "UserKnownHostsFile=~/.ssh/known_hosts" \
    -o "ServerAliveInterval=60" \
    -o "ServerAliveCountMax=3" \
    -o "ExitOnForwardFailure=yes" \
    -o "ConnectTimeout=10" \
    -o "PasswordAuthentication=yes" \
    -N -L $LOCAL_PORT:$DB_HOST:$DB_PORT \
    -p $SSH_PORT $SSH_USER@$SSH_HOST &

AUTOSSH_PID=$!
echo "Autossh started with PID: $AUTOSSH_PID"

# Wait for tunnel to be established
echo "Waiting for SSH tunnel to be established..."
for i in {1..30}; do
    if check_tunnel; then
        echo "SSH tunnel established successfully"
        break
    fi
    echo "Waiting for SSH tunnel... (attempt $i/30)"
    sleep 2
done

if ! check_tunnel; then
    echo "Failed to establish SSH tunnel after 60 seconds"
    echo "Checking if autossh process is still running..."
    if kill -0 $AUTOSSH_PID 2>/dev/null; then
        echo "Autossh process is running but tunnel not responding"
        echo "Try checking: ssh -v passthrough@98.84.13.90"
    else
        echo "Autossh process died - check credentials and connectivity"
    fi
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo "Shutting down autossh tunnel..."
    kill $AUTOSSH_PID 2>/dev/null
    # Kill any remaining ssh processes
    pkill -f "autossh.*$SSH_HOST" 2>/dev/null
    pkill -f "ssh.*$SSH_HOST" 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

echo "SSH tunnel is ready! You can now connect to MySQL via localhost:$LOCAL_PORT"
echo "Starting Django application..."

# Start Django with your original command
python3 manage.py runserver 0.0.0.0:8000