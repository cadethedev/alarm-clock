#!/bin/bash
# Create test color file with proper permissions
touch /home/cadev/test_color.json
chmod 666 /home/cadev/test_color.json
echo '{"r": 0, "g": 0, "b": 0, "timestamp": 0}' > /home/cadev/test_color.json
echo "Test color file created"
