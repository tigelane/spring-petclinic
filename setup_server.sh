#!/bin/bash

# https://raw.githubusercontent.com/tigelane/spring-petclinic/master/setup_server.sh
sudo yum -y update
sudo yum install -y git

echo $IGNW_InstallURL > script.log
echo $IGNW_1 >> script.log

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

cd /opt
git clone https://github.com/tigelane/spring-petclinic.git
cd spring-petclinic
sudo ./mvnw spring-boot:run > pet.log 2>&1 &
sleep 10
ls
