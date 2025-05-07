"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

# Create a security group allowing inbound access on port 22 (SSH)
security_group = aws.ec2.SecurityGroup('lazarev-lab-secgrp',
    description='Enable SSH access',
    ingress=[{
        'protocol': 'tcp',
        'from_port': 22,
        'to_port': 22,
        'cidr_blocks': ['44.214.210.109/32'],
    }])

# Define user data script to install Docker
startup_script = """#!/bin/bash
# Update the package repository
sudo yum update -y

# Install Docker
sudo yum install -y docker

# Start Docker service
sudo systemctl start docker

# Enable Docker service to start on boot
sudo systemctl enable docker

# Add ec2-user to the docker group to run Docker commands without sudo
sudo usermod -aG docker ec2-user
"""

# Create an EC2 instance - SRM Docker
# Sizing - t3.xlarge is likely needed, will test t3.large first
server = aws.ec2.Instance('srm-docker',
    #instance_type='t3.large',
    instance_type='t2.micro',
    security_groups=[security_group.name],
    # example login cmd: ssh -i /Users/lazarev/.ssh/lazarev-ec2.pem fedora@3.87.79.23
    ami='ami-07df3bb06da88a158',  # Fedora Cloud 42 AMI in us-east-1 - https://fedoraproject.org/cloud/download#cloud_launch
    key_name='lazarev-ec2',
    user_data=startup_script)

# Export the public IP of the instance
pulumi.export('public_ip', server.public_ip)