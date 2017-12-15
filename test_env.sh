#!/bin/bash

# https://raw.githubusercontent.com/tigelane/spring-petclinic/master/test_env.sh

source envv.sh
echo $IGNW_InstallURL > setup.log
echo $MasterAddress >> setup.log
