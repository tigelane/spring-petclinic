echo export IGNW_INSTALLURL=@@{IGNW_INSTALLURL}@@ > envv.sh
echo export IGNW_BRANCH=@@{IGNW_BRANCH}@@ >> envv.sh

curl @@{IGNW_INSTALLURL}@@ > setup_server.sh
chmod 766 setup_server.sh
./setup_server.sh
