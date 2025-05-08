#!/bin/bash

function install_docker {
# Update the package repository
echo "Updating package repository..."
sudo yum update -y | tee -a /var/log/cloud-init-output.log

# Install Docker Engine and wget
sudo dnf -y install dnf-plugins-core wget
sudo dnf-3 config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Install Docker (OLD)
# echo "Installing Docker..." | tee -a /var/log/cloud-init-output.log
# sudo yum install -y docker | tee -a /var/log/cloud-init-output.log

# Start Docker service
echo "Starting Docker service..."
sudo systemctl start docker

# Enable Docker service to start on boot
echo "Enabling Docker service to start on boot..."
sudo systemctl enable docker 

# Add fedora to the docker group to run Docker commands without sudo
echo "Adding fedora to the docker group..."
sudo usermod -aG docker fedora 
}

function generate_ssl_files {
    sudo openssl req -new -newkey rsa:4096 -days 3650 -nodes -x509 -subj "/C=US/ST=New York/L=Northport/O=SRM/CN=localhost" -keyout ./ssl.key -out ./ssl.crt
}

function get_running_srm_version {
    if docker ps --format '{{.Names}}' | grep -q 'tomcat'; then
       input=$(docker ps --format '{{.Names}}')
       version=${input#*-}
       version=${version%-*}
       major=${version:0:1}
       minor=${version:1:2}
       patch=${version:3:1}
       version="$major.$minor.$patch"
       echo "SRM Docker version $version is running"
    fi
}

function check_if_srm_is_running_and_stop {
    if [[ $(docker ps -q -f name=srm) ]]; then
        get_running_srm_version
        cd /opt/srm/srm-docker-$version
        echo "Stopping SRM Docker version $version"
        docker compose -f docker-compose.yml down
    fi
}

function configure_docker_compose {
    sed -i '' '/codedx-appdata-volume:/a\
\            - /opt/srm/ssl.crt:/usr/local/tomcat/conf/ssl.crt\
\            - /opt/srm/ssl.key:/usr/local/tomcat/conf/ssl.key\
\            - /opt/srm/server.xml:/usr/local/tomcat/conf/server.xml\
' docker-compose.yml
    sed -i 's/8080:8080/443:8443/g' docker-compose.yml
}

function start_srm_docker {
    #if [ -e /opt/srm/srm-docker-$SRM_VERSION ]; then
    #    echo "SRM Docker version $SRM_VERSION already installed"
    #    cd /opt/srm/srm-docker-$SRM_VERSION
    #    docker compose -f docker-compose.yml up -d 
    #else
    cd /opt/srm; 
    SRM_GH_PATH=https://github.com/codedx/srm-docker/archive/refs/tags/
    #sudo yum -y install wget
    sudo wget $SRM_GH_PATH/v$SRM_VERSION.tar.gz; 
    sudo tar xzf v$SRM_VERSION.tar.gz; 
    cd srm-docker-$SRM_VERSION
    sudo cp $SSL_KEY /opt/srm/srm-docker-$SRM_VERSION/ssl.key
    sudo cp $SSL_CERT /opt/srm/srm-docker-$SRM_VERSION/ssl.crt
    configure_docker_compose
    docker compose -f docker-compose.yml up -d
    #fi
}

function main {
    # Redirect stdout and stderr to /var/log/cloud-init-output.log
    #exec > >(tee -a /var/log/cloud-init-output.log) 2>&1

    # Enable debugging
    set -x

    mkdir /opt/srm;cd /opt/srm
    generate_ssl_files

    SSL_KEY="/opt/srm/ssl.key"
    SSL_CERT="/opt/srm/ssl.crt"
    SRM_VERSION="1.119.0"

    install_docker
    #check_if_srm_is_running_and_stop
    start_srm_docker
}

# Call main
main