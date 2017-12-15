echo export Master_TIGE_VAR_SER=@@{Master.TIGE_VAR_SER}@@ >> .bash_profile
echo export IGNW_InstallURL=@@{IGNW_InstallURL}@@ >> .bash_profile
echo export IGNW_1=@@{IGNW_1}@@ >> .bash_profile
echo export Master_ipaddress=@@{Master.ipaddress}@@ >> .bash_profile

curl @@{IGNW_InstallURL}@@ > setup_server.sh
chmod 766 setup_server.sh
sudo ./setup_server.sh
