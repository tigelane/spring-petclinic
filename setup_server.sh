#!/bin/bash

# https://raw.githubusercontent.com/tigelane/spring-petclinic/master/setup_server.sh
source envv.sh
echo "--Executing from $IGNW_INSTALLURL --" > setup.log

echo "--Updating yum--" > setup.log
sudo yum -y update
echo "--Installing git--" > setup.log
sudo yum install -y git

echo "--Installing Java 1.8--" > setup.log
cd /opt
sudo wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" "http://download.oracle.com/otn-pub/java/jdk/8u151-b12/e758a0de34e24606bca991d704f6dcbf/jdk-8u151-linux-x64.tar.gz"
sudo tar xzf jdk-8u151-linux-x64.tar.gz
cd jdk1.8.0_151/
sudo alternatives --install /usr/bin/java java /opt/jdk1.8.0_151/bin/java 2
sudo alternatives --config java <<< $'2'
sudo alternatives --install /usr/bin/jar jar /opt/jdk1.8.0_151/bin/jar 2
sudo alternatives --install /usr/bin/javac javac /opt/jdk1.8.0_151/bin/javac 2
sudo alternatives --set jar /opt/jdk1.8.0_151/bin/jar
sudo alternatives --set javac /opt/jdk1.8.0_151/bin/javac

cd ~/
git clone https://github.com/tigelane/spring-petclinic.git
cd spring-petclinic
sudo nohup ./mvnw spring-boot:run 2>&1 &
sleep 30
