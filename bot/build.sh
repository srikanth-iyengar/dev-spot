#!/bin/bash

# clean
rm -rf package
rm deploy.zip

mkdir package
source venv/bin/activate
pip install pynacl requests -t package

cd package
zip -r ../deploy.zip .
cd ..
zip deploy.zip main.py
zip deploy.zip discord_push.py
zip deploy.zip create_stack.py
zip deploy.zip self_destruct.py
zip deploy.zip push_ec2_ip.py

