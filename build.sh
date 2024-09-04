#!/bin/bash

# Install system dependencies
apt-get update && apt-get install -y libjpeg-dev zlib1g-dev

# Install Python dependencies
pip install -r requirements.txt