echo export IGNW_INSTALLURL=@@{IGNW_InstallURL}@@ > envv.sh

curl @@{IGNW_INSTALLURL}@@ > setup_server.sh
chmod 766 setup_server.sh
./setup_server.sh