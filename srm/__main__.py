"""BD AWS lab"""
# TODO: add bd-sca docker and k8s instances, and BDBA standalone k8s
# 17GB RAM sca services + 9GB postgres

import pulumi
import pulumi_aws as aws

# Create a VPC
vpc = aws.ec2.Vpc("lazarev-vpc",
    cidr_block="10.0.0.0/16")

# Create an Internet Gateway
internet_gateway = aws.ec2.InternetGateway("lazarev-gateway",
    vpc_id=vpc.id)

# Create a subnet with auto-assign public IP
subnet = aws.ec2.Subnet("lazarev-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=True)  # Enable auto-assign public IP

# Create a route table
route_table = aws.ec2.RouteTable("lazarev-route-table",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": internet_gateway.id
    }])

# Associate the route table with the subnet
route_table_association = aws.ec2.RouteTableAssociation("lazarev-route-table-association",
    subnet_id=subnet.id,
    route_table_id=route_table.id)

# Create a security group allowing inbound access on port 22 (SSH) and all outbound traffic
security_group = aws.ec2.SecurityGroup('lazarev-lab-secgrp',
    vpc_id=vpc.id,
    description='Enable SSH and HTTPS access',
    ingress=[
        {
            'protocol': 'tcp',
            'from_port': 22,
            'to_port': 22,
            'cidr_blocks': ['44.214.210.109/32'],  # SSH access
        },
        {
            'protocol': 'tcp',
            'from_port': 443,
            'to_port': 443,
            'cidr_blocks': ['44.214.210.109/32'],  # HTTPS access
        }
    ],
    egress=[
        {
            'protocol': '-1',
            'from_port': 0,
            'to_port': 0,
            'cidr_blocks': ['0.0.0.0/0'],  # Allow all outbound traffic
        }
    ])


# Read the script from the file
with open('srm-docker-inst.sh', 'r') as file:
    f_content = file.read()
    
# Problematic chars escape
# escaped_file_content = f_content.replace('"', '\\"')

# Define user data script
startup_script = f"""#!/bin/bash
echo "{f_content}" > /home/fedora/srm-docker-inst.sh | tee -a /var/log/cloud-init-output.log
"""

# Create an EC2 instance - SRM Docker
server = aws.ec2.Instance('srm-docker',
    instance_type='t3.large',
    subnet_id=subnet.id,
    vpc_security_group_ids=[security_group.id],
    #ami='ami-07df3bb06da88a158',  # Fedora Cloud 42 AMI in us-east-1
    #ami='ami-01b7e394d946843f6',  # SRM AMI lazarev-srm-docker-2025.3.5
    ami='ami-06a866213a6aa44ce',  # SRM AMI lazarev-srm-docker-2025.3.7
    key_name='lazarev-ec2',
    user_data=startup_script,
    root_block_device={
        "volume_size": 64,  # Set the root volume size to 64GB
        "volume_type": "gp3",  # General Purpose SSD
    },
    tags={
        "Name": "lazarev-srm-docker"  # Set the instance name
    })

# Allocate an Elastic IP
elastic_ip = aws.ec2.Eip("lazarev-srm-eip",
    domain="vpc")  # Use domain instead of vpc

# Associate the Elastic IP with the EC2 instance
eip_association = aws.ec2.EipAssociation("lazarev-srm-eip-association",
    instance_id=server.id,
    allocation_id=elastic_ip.id)

# Export the public IP of the instance
pulumi.export('public_ip', elastic_ip.public_ip)