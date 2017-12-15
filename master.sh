echo export IGNW_1=@@{IGNW_1}@@ > envv.sh
echo export IGNW_InstallURL=@@{IGNW_InstallURL}@@ >> envv.sh
echo export MasterAddress=@@{Master.address}@@ >> envv.sh

curl @@{IGNW_InstallURL}@@ > setup_server.sh
chmod 766 setup_server.sh
./setup_server.sh
