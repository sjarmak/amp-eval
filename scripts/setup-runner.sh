#!/bin/bash
# Self-hosted runner setup script for EC2/cloud instances
# This script configures a machine to run GitHub Actions for amp-eval

set -e

# Configuration
RUNNER_USER="runner"
WORK_DIR="/actions-runner"
REPO_URL="https://github.com/YOUR_ORG/amp-eval"  # Replace with your repo
RUNNER_TOKEN="${GITHUB_RUNNER_TOKEN}"  # Passed as environment variable

# System updates
apt-get update
apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install Python 3.10
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update
apt-get install -y python3.10 python3.10-pip python3.10-venv python3.10-dev

# Create runner user
useradd -m -s /bin/bash $RUNNER_USER
usermod -aG sudo $RUNNER_USER

# Setup runner directory
mkdir -p $WORK_DIR
chown $RUNNER_USER:$RUNNER_USER $WORK_DIR

# Download and setup GitHub Actions runner
cd $WORK_DIR
wget -O actions-runner-linux-x64.tar.gz \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
tar xzf actions-runner-linux-x64.tar.gz
chown -R $RUNNER_USER:$RUNNER_USER $WORK_DIR

# Install dependencies
sudo -u $RUNNER_USER ./bin/installdependencies.sh

# Configure runner (requires GITHUB_RUNNER_TOKEN)
if [ -n "$RUNNER_TOKEN" ]; then
    sudo -u $RUNNER_USER ./config.sh \
        --url $REPO_URL \
        --token $RUNNER_TOKEN \
        --name "$(hostname)-runner" \
        --work _work \
        --labels "self-hosted,amp-eval,cost-optimized" \
        --runasservice \
        --unattended
        
    # Install and start the service
    ./svc.sh install $RUNNER_USER
    ./svc.sh start
else
    echo "Warning: GITHUB_RUNNER_TOKEN not provided, runner not configured"
fi

# Install amp-eval dependencies
sudo -u $RUNNER_USER python3.10 -m pip install --user --upgrade pip
sudo -u $RUNNER_USER python3.10 -m pip install --user -r /actions-runner/_work/amp-eval/amp-eval/requirements.txt

# Setup monitoring
cat > /etc/systemd/system/runner-monitor.service << EOF
[Unit]
Description=GitHub Actions Runner Monitor
After=network.target

[Service]
Type=simple
User=$RUNNER_USER
ExecStart=/usr/bin/python3.10 /actions-runner/monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create monitoring script
cat > /actions-runner/monitor.py << 'EOF'
#!/usr/bin/env python3
"""
Monitor runner health and auto-shutdown when idle.
Helps control costs by shutting down unused runners.
"""

import time
import subprocess
import os
import requests
from datetime import datetime, timedelta

def get_runner_status():
    """Check if runner is currently executing jobs."""
    try:
        # Check if any GitHub Actions processes are running
        result = subprocess.run(['pgrep', '-f', 'Runner.Listener'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def should_shutdown():
    """Determine if runner should shutdown due to inactivity."""
    # Shutdown after 30 minutes of inactivity
    idle_threshold = timedelta(minutes=30)
    
    # Check system load and last activity
    try:
        uptime = subprocess.run(['uptime'], capture_output=True, text=True)
        # Parse load average and decide based on your criteria
        return False  # Customize this logic
    except:
        return False

def main():
    """Main monitoring loop."""
    print(f"Starting runner monitor at {datetime.now()}")
    
    while True:
        try:
            if not get_runner_status() and should_shutdown():
                print("Runner idle, initiating shutdown...")
                # Notify webhook before shutdown
                requests.post(os.environ.get('SLACK_WEBHOOK_URL', ''), 
                            json={'text': f'Runner {os.uname().nodename} shutting down due to inactivity'})
                subprocess.run(['sudo', 'shutdown', '-h', '+1'])
                break
                
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
EOF

chmod +x /actions-runner/monitor.py
chown $RUNNER_USER:$RUNNER_USER /actions-runner/monitor.py

# Enable and start monitoring
systemctl enable runner-monitor
systemctl start runner-monitor

echo "Self-hosted runner setup complete!"
echo "Runner name: $(hostname)-runner"
echo "Labels: self-hosted,amp-eval,cost-optimized"
