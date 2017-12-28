#!/usr/bin/env python

from datetime import datetime
import sys, requests, re, random, os
import json, time
import urllib3

# We don't have a real SSL cert, so let's disable the warnings
urllib3.disable_warnings()

sysUser = "admin"
sysPass = "infogroup4U!"
appAddr = "10.2.1.51"

urlBaseV3 = 'https://{0}:9440/api/nutanix/v3'.format(appAddr)
dataUrl = None

processID = None

def main(argv):
    global processID
    badCommand = False

    if len(argv) > 4:
        appName = argv[2]
        appVar = argv[3]
        cloud = argv[4]
        if argv[1] == "create_pet":
            create_pet(appName, appVar, cloud)
            exit(0)
        elif argv[1] == "create_swarm":
            create_swarm(appName, appVar, cloud)
            exit(0)
        else:
            badCommand = True

    if len(argv) > 2:
        processID = argv[2]
        if argv[1] == "delete":
            delete(argv[2])
            exit(0)
        else:
            badCommand = True

    if len(argv) > 1:
        if argv[1] == "blueprints_list":
            exit (blueprints_list())
        if argv[1] == "apps_list":
            sys.exit(apps_list())
        else:
            badCommand = True
    else:
        badCommand = True

    if badCommand:
        funcReply = "USAGE:  {0} <(job)> <(app name)> <(variable)> <(aws, nutanix)>\nValid jobs: create_pet, create_swarm, delete, blueprints_list, apps_list\nValid variables: ([master, orange, siamese], swarm#)".format(argv[0])
        print (funcReply)
        return funcReply

def apps_list():
    dataUrl = '{0}/apps/list'.format(urlBaseV3)
    response = open_url(dataUrl, "post", "{}")
    myList = []

    try:
        for unit in response["entities"]:
            if unit["status"]["state"] != "deleted":
                name = unit["status"]["name"]
                uuid = unit["status"]["uuid"]
                myList.append({"name":name, "uuid":uuid})
    except:
        return ("{0}".format(response))

    return myList

def get_blueprints():
    dataUrl = '{0}/blueprints/list'.format(urlBaseV3)
    response = open_url(dataUrl, "post", "{}")
    active_blueprints = []

    try:
        for blueprint in response["entities"]:
            if blueprint["status"]["state"] == "ACTIVE":
                name = blueprint["status"]["name"]
                uuid = blueprint["status"]["uuid"]
                spec_version = blueprint["status"]["spec_version"]
                project = blueprint["metadata"]["project_reference"]["name"]
                active_blueprints.append({"name":name, "uuid":uuid, "spec_version": spec_version, "project_reference": project})
    except:
        return ("{}".format(response))

    return active_blueprints

def blueprints_list():
    funcReply = "\n=====  Active Projects  ====="
    active_blueprints = get_blueprints()

    for blueprint in active_blueprints:
        funcReply += "Name: {0}".format(blueprint["name"])
        funcReply += "UUID: {0}".format(blueprint["uuid"])
        funcReply += "Spec Version: {0}".format(blueprint["spec_version"])
        funcReply += "Project: {0}".format(blueprint["project_reference"])
        funcReply += "=============================\n"

        print (funcReply)
        return funcReply

def blueprints_single(blueprintName):
    active_blueprints = get_blueprints()

    for blueprint in active_blueprints:
        if blueprint["name"] == blueprintName:
            return blueprint

def create_pet(appName, appVar, cloud):
    blueprintData = blueprints_single("Pet Clinic")

    if cloud.lower() == "nutanix":
        body = get_pet_nutanix_body(appName, appVar, blueprintData["spec_version"])
    elif cloud.lower() == "aws":
        body = get_pet_aws_body(appName, appVar, blueprintData["spec_version"])
    elif cloud.lower() == "google":
        return "{0} cloud is not implemented yet.".format(cloud)
    else:
        return "The following is not a valid cloud: {}".format(cloud)

    body = json.dumps(body, ensure_ascii=True)

    dataUrl = '{0}/blueprints/{1}/launch'.format(urlBaseV3, blueprintData["uuid"])
    response = open_url(dataUrl, "post", body)

    try:
        myReturn = "Job created with ID: {0}".format(response["status"]["request_id"])
    except:
        myReturn = "{}".format(response)

    return myReturn

def create_swarm(appName, appVar, cloud):
    blueprintData = blueprints_single("IGNW Docker")

    if cloud.lower() == "nutanix":
        body = get_swarm_nutanix_body(appName, appVar, blueprintData["spec_version"])
    elif cloud.lower() == "aws":
        return "{0} cloud is not implemented yet.".format(cloud)
    elif cloud.lower() == "google":
        return "{0} cloud is not implemented yet.".format(cloud)
    else:
        return "The following is not a valid cloud: {}".format(cloud)

    body = json.dumps(body, ensure_ascii=True)

    dataUrl = '{0}/blueprints/{1}/launch'.format(urlBaseV3, blueprintData["uuid"])
    response = open_url(dataUrl, "post", body)

    try:
        myReturn = "Job created with ID: {0}".format(response["status"]["request_id"])
    except:
        myReturn = "{}".format(response)

    return myReturn

def get_app(appName):
    dataUrl = '{0}/apps/list'.format(urlBaseV3)
    response = open_url(dataUrl, "post", "{}")

    try:
        for app in response["entities"]:
            if app["metadata"]["name"] == appName:
                return app["metadata"]["uuid"]
    except:
        print ("{}".format(response))
        return 1

    # return empty string if appName is not found
    return ""

def delete(appName):
    uuid = ""
    uuid = get_app(appName)

    if len(uuid) < 20:
        return "Unable to find application named: {0}".format(appName)

    try:
        dataUrl = '{0}/apps/{1}'.format(urlBaseV3, uuid)
        response = open_url(dataUrl, "delete", "{}")
    except:
        # print ("{}".format(response))
        return "Unable to delete application named: {0}".format(appName)

    try:
        return "App deleted: {0} with uuid: {1}".format(appName, uuid)
    except:
        #print ("{}".format(response))
        return 1

def open_url(url, method, body=None):
    headers={'Content-Type': 'application/json'}
    auth=(sysUser, sysPass)

    if method == "get":
        try:
            result = requests.get(url, data=body, headers=headers, verify=False, auth=auth)
        except:
            error = "Application Server Failure: Not able to communicate with Server at {0} ".format(appAddr)
            return error
    elif method == "post":
        try:
            result = requests.post(url, data=body, headers=headers, verify=False, auth=auth)
        except:
             error = "Application Server Failure: Not able to communicate with Server at {0} ".format(appAddr)
             return error

    elif method == "delete":
        try:
            result = requests.delete(url, data=body, headers=headers, verify=False, auth=auth)
        except:
             error = "Application Server Failure: Not able to communicate with Server at {0} ".format(appAddr)
             return error

    if (result.status_code == 200 or result.status_code == 201 or result.status_code == 202):
        decoded_json = json.loads(result.text)
        return decoded_json

    elif (result.status_code == 401):
        return "Invalid credentials"

    elif (result.status_code == 404):
            return "URL not found on server"

    elif (result.status_code == 422):
        return "Application Name is already used."

    else:
        return {"resource" : "Unknown error code: {0} - With this error text: {1}".format(result.status_code, result.text)}

def get_pet_aws_body(newName, appVar, spec_version):
    body = {
        "api_version": "3.0",
        "metadata": {
            "categories": {
            },
            "creation_time": "1513203430452577",
            "kind": "blueprint",
            "last_update_time": "1513876786334140",
            "name": "Pet Clinic",
            "owner_reference": {
                "kind": "user",
                "name": "admin",
                "uuid": "00000000-0000-0000-0000-000000000000"
            },
            "project_reference": {
                "kind": "project",
                "name": "Nutanix_Demo1",
                "uuid": "caddfb46-bb7f-4fda-9290-46fb1de64c3c"
            },
            "spec_version": spec_version,
            "uuid": "eb836433-88cc-3f9e-8de2-c5e6a634635b"
        },
        "spec": {
            "app_profile_reference": {
                "kind": "app_profile",
                "uuid": "c9d1adc7-2279-6fd8-e443-7968a6eaef60"
            },
            "application_name": newName,
            "resources": {
                "app_profile_list": [
                    {
                        "action_list": [
                        ],
                        "deployment_create_list": [
                            {
                                "action_list": [
                                ],
                                "editables": {
                                },
                                "max_replicas": "1",
                                "min_replicas": "1",
                                "name": "218e961a_deployment",
                                "package_local_reference_list": [
                                    {
                                        "kind": "app_package",
                                        "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5"
                                    }
                                ],
                                "substrate_local_reference": {
                                    "kind": "app_substrate",
                                    "uuid": "7af1c09e-2c84-c0a0-3460-b0559a7f4eda"
                                },
                                "uuid": "c5d37072-a4ef-98d4-b4a2-a5062894695a",
                                "variable_list": [
                                ]
                            }
                        ],
                        "name": "aws_ap",
                        "uuid": "c9d1adc7-2279-6fd8-e443-7968a6eaef60",
                        "variable_list": [
                            {
                                "attrs": {
                                },
                                "description": "",
                                "label": "",
                                "name": "IGNW_INSTALLURL",
                                "type": "LOCAL",
                                "uuid": "4121985b-d393-d3fb-cd96-574f751181a3",
                                "val_type": "STRING",
                                "value": "https://raw.githubusercontent.com/tigelane/spring-petclinic/master/setup_server.sh"
                            },
                            {
                                "attrs": {
                                },
                                "description": "",
                                "editables": {
                                    "value": True
                                },
                                "label": "",
                                "name": "IGNW_BRANCH",
                                "type": "LOCAL",
                                "uuid": "24f5824d-5911-b177-ed99-8440e0f9f5b5",
                                "val_type": "STRING",
                                "value": appVar
                            }
                        ]
                    },
                    {
                        "action_list": [
                        ],
                        "deployment_create_list": [
                            {
                                "action_list": [
                                ],
                                "max_replicas": "1",
                                "min_replicas": "1",
                                "name": "218e961a_deployment_cloned_1",
                                "package_local_reference_list": [
                                    {
                                        "kind": "app_package",
                                        "uuid": "02a9f80f-d693-62c8-7775-498909904bec"
                                    }
                                ],
                                "substrate_local_reference": {
                                    "kind": "app_substrate",
                                    "uuid": "5ed28fcf-b92e-923a-640b-206d0dce940a"
                                },
                                "uuid": "2e695e24-aff1-2c8a-987b-732a73c28524",
                                "variable_list": [
                                ]
                            }
                        ],
                        "name": "nut_ap",
                        "uuid": "52df6135-8bec-f0b3-224f-7734b24c9cad",
                        "variable_list": [
                            {
                                "attrs": {
                                },
                                "description": "",
                                "label": "",
                                "name": "IGNW_INSTALLURL",
                                "type": "LOCAL",
                                "uuid": "b00e5fc4-539a-5a24-58b3-490cc22ea1b4",
                                "val_type": "STRING",
                                "value": "https://raw.githubusercontent.com/tigelane/spring-petclinic/master/setup_server.sh"
                            },
                            {
                                "attrs": {
                                },
                                "description": "",
                                "editables": {
                                    "value": True
                                },
                                "label": "",
                                "name": "IGNW_BRANCH",
                                "type": "LOCAL",
                                "uuid": "5fd315fe-3364-111e-e4da-535b19547612",
                                "val_type": "STRING",
                                "value": ""
                            }
                        ]
                    }
                ],
                "client_attrs": {
                    "166f0e95-8a51-493c-f6ce-032dd02eb1ad": {
                        "x": 400,
                        "y": 280
                    }
                },
                "credential_definition_list": [
                    {
                        "name": "AWS",
                        "secret": {
                            "attrs": {
                                "is_secret_modified": False
                            }
                        },
                        "type": "KEY",
                        "username": "ec2-user",
                        "uuid": "97969849-a39c-fad6-c0c9-a044aa2aed34"
                    },
                    {
                        "name": "ignw",
                        "secret": {
                            "attrs": {
                                "is_secret_modified": False
                            }
                        },
                        "type": "PASSWORD",
                        "username": "ignw",
                        "uuid": "8549b4a1-d06d-1d45-c850-0ca3604d702a"
                    }
                ],
                "default_credential_local_reference": {
                    "kind": "app_credential",
                    "name": "default_credential",
                    "uuid": "97969849-a39c-fad6-c0c9-a044aa2aed34"
                },
                "package_definition_list": [
                    {
                        "name": "package",
                        "options": {
                            "install_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "5a17adba-e735-95f4-1ac8-9b947d997fca"
                                },
                                "name": "15e3bbf6_runbook",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                            {
                                                "kind": "app_task",
                                                "uuid": "110be21f-fc1b-cefc-7edb-251f42c1572c"
                                            }
                                        ],
                                        "name": "7f891ab9_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5"
                                        },
                                        "type": "DAG",
                                        "uuid": "5a17adba-e735-95f4-1ac8-9b947d997fca",
                                        "variable_list": [
                                        ]
                                    },
                                    {
                                        "attrs": {
                                            "login_credential_local_reference": {
                                                "kind": "app_credential",
                                                "uuid": "97969849-a39c-fad6-c0c9-a044aa2aed34"
                                            },
                                            "script": "echo export IGNW_INSTALLURL=@@{IGNW_INSTALLURL}@@ > envv.sh\necho export IGNW_BRANCH=@@{IGNW_BRANCH}@@ >> envv.sh\n\ncurl @@{IGNW_INSTALLURL}@@ > setup_server.sh\nchmod 766 setup_server.sh\n./setup_server.sh",
                                            "script_type": "sh"
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "PackageInstallTask",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5"
                                        },
                                        "type": "EXEC",
                                        "uuid": "110be21f-fc1b-cefc-7edb-251f42c1572c",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "41767ffd-5c09-bbe5-299a-fd9d78295e02",
                                "variable_list": [
                                ]
                            },
                            "uninstall_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "6cdc6b91-2288-951b-26e4-784c3d5fe48c"
                                },
                                "name": "5e5fb7ed_runbook",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "2e9826ad_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5"
                                        },
                                        "type": "DAG",
                                        "uuid": "6cdc6b91-2288-951b-26e4-784c3d5fe48c",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "8145c76e-3b63-504d-e6a2-b1199dfe7bea",
                                "variable_list": [
                                ]
                            }
                        },
                        "service_local_reference_list": [
                            {
                                "kind": "app_service",
                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                            }
                        ],
                        "type": "DEB",
                        "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5",
                        "variable_list": [
                        ]
                    },
                    {
                        "name": "package_nut",
                        "options": {
                            "install_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "0b4a4b20-eb54-93af-67e4-4df67c66d56b"
                                },
                                "name": "15e3bbf6_runbook_cloned_1",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                            {
                                                "kind": "app_task",
                                                "uuid": "dd27f562-dd77-dcfc-44a2-37361464ee39"
                                            }
                                        ],
                                        "name": "7f891ab9_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "02a9f80f-d693-62c8-7775-498909904bec"
                                        },
                                        "type": "DAG",
                                        "uuid": "0b4a4b20-eb54-93af-67e4-4df67c66d56b",
                                        "variable_list": [
                                        ]
                                    },
                                    {
                                        "attrs": {
                                            "login_credential_local_reference": {
                                                "kind": "app_credential",
                                                "uuid": "8549b4a1-d06d-1d45-c850-0ca3604d702a"
                                            },
                                            "script": "echo export IGNW_INSTALLURL=@@{IGNW_INSTALLURL}@@ > envv.sh\necho export IGNW_BRANCH=@@{IGNW_BRANCH}@@ >> envv.sh\n\ncurl @@{IGNW_INSTALLURL}@@ > setup_server.sh\nchmod 766 setup_server.sh\n./setup_server.sh",
                                            "script_type": "sh"
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "PackageInstallTask",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "02a9f80f-d693-62c8-7775-498909904bec"
                                        },
                                        "type": "EXEC",
                                        "uuid": "dd27f562-dd77-dcfc-44a2-37361464ee39",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "6fd1515b-abce-c59a-e99a-44fba8ed4a0d",
                                "variable_list": [
                                ]
                            },
                            "uninstall_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "56e1ddb8-237f-a91a-36d1-52c52136bb47"
                                },
                                "name": "5e5fb7ed_runbook_cloned_1",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "2e9826ad_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "02a9f80f-d693-62c8-7775-498909904bec"
                                        },
                                        "type": "DAG",
                                        "uuid": "56e1ddb8-237f-a91a-36d1-52c52136bb47",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "c22105d4-03ba-5e49-8721-2b7286a60dd4",
                                "variable_list": [
                                ]
                            }
                        },
                        "service_local_reference_list": [
                            {
                                "kind": "app_service",
                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                            }
                        ],
                        "type": "DEB",
                        "uuid": "02a9f80f-d693-62c8-7775-498909904bec",
                        "variable_list": [
                        ]
                    }
                ],
                "service_definition_list": [
                    {
                        "action_list": [
                            {
                                "critical": False,
                                "name": "action_create",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "c19d6abe-6fd0-665a-8304-232d8b3237a7"
                                    },
                                    "name": "f894c047_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "895b19a6_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "c19d6abe-6fd0-665a-8304-232d8b3237a7",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "3f12a589-0d2c-7d83-ef84-0d69a45c0013",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "a8c79579-ed6f-59ef-3524-0d27180f37f6"
                            },
                            {
                                "critical": False,
                                "name": "action_delete",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "aa066a5e-7cc1-ff2c-20b3-5242a852be4b"
                                    },
                                    "name": "80b1769f_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "aacc0d91_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "aa066a5e-7cc1-ff2c-20b3-5242a852be4b",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "b72cb73d-deac-5f96-cc08-bf1413a59aca",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "e899503c-4063-9cc7-c0a6-a56b27d37787"
                            },
                            {
                                "critical": False,
                                "name": "action_start",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "ac09e5d6-cde8-4bc6-3402-5c512162c4fb"
                                    },
                                    "name": "0347d817_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "820484d2_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "ac09e5d6-cde8-4bc6-3402-5c512162c4fb",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "11117dbd-9e34-5f4c-6303-a0241e70ace0",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "aebc41a8-d414-e1d8-aee2-ec72d9aece13"
                            },
                            {
                                "critical": False,
                                "name": "action_stop",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "eb150869-8073-1404-bc97-bc491c7066de"
                                    },
                                    "name": "589d4a52_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "5019dc25_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "eb150869-8073-1404-bc97-bc491c7066de",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "a2ec7f36-e64e-a296-7af3-8cf65abe68ac",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "9c11bbab-fdee-d189-0d15-cebe28b8ffed"
                            },
                            {
                                "critical": False,
                                "name": "action_restart",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "9fbd3008-b098-28ea-77e1-f667407b4c9d"
                                    },
                                    "name": "32fbb0ec_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "ceba1eb1_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "9fbd3008-b098-28ea-77e1-f667407b4c9d",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "80c2f6cd-5b2f-3879-2063-42931d1a4a37",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "354e13c1-20a3-25c1-b744-6e2979f42ae3"
                            }
                        ],
                        "depends_on_list": [
                        ],
                        "name": "PetServer",
                        "port_list": [
                        ],
                        "singleton": False,
                        "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad",
                        "variable_list": [
                        ]
                    }
                ],
                "substrate_definition_list": [
                    {
                        "action_list": [
                        ],
                        "create_spec": {
                            "name": "@@{calm_blueprint_name}@@-@@{calm_random}@@",
                            "resources": {
                                "account_uuid": "f0b79f8a-c1d8-3090-a367-56ae3d230917",
                                "associate_public_ip_address": True,
                                "availability_zone": "us-west-2a",
                                "block_device_map": {
                                    "root_disk": {
                                        "delete_on_termination": True,
                                        "device_name": "/dev/sdb",
                                        "size_gb": 8,
                                        "volume_type": "GP2"
                                    }
                                },
                                "image_id": "ami-39802141",
                                "instance_initiated_shutdown_behavior": "TERMINATE",
                                "instance_profile_name": None,
                                "instance_type": "t2.small",
                                "key_name": "ignw_dev-west2",
                                "region": "us-west-2",
                                "security_group_list": [
                                    {
                                        "security_group_id": "sg-7523a309"
                                    }
                                ],
                                "subnet_id": "subnet-de2aaab9",
                                "vpc_id": "vpc-0a11796d"
                            },
                            "type": "PROVISION_AWS_VM"
                        },
                        "name": "pet server",
                        "os_type": "Linux",
                        "readiness_probe": {
                            "address": "@@{public_ip_address}@@",
                            "connection_port": 22,
                            "connection_type": "SSH",
                            "disable_readiness_probe": False,
                            "login_credential_local_reference": {
                                "kind": "app_credential",
                                "uuid": "97969849-a39c-fad6-c0c9-a044aa2aed34"
                            }
                        },
                        "type": "AWS_VM",
                        "uuid": "7af1c09e-2c84-c0a0-3460-b0559a7f4eda",
                        "variable_list": [
                        ]
                    },
                    {
                        "action_list": [
                        ],
                        "create_spec": {
                            "name": "@@{calm_blueprint_name}@@-@@{calm_random}@@",
                            "resources": {
                                "boot_config": {
                                    "boot_device": {
                                        "disk_address": {
                                            "adapter_type": "IDE",
                                            "device_index": 0
                                        }
                                    }
                                },
                                "disk_list": [
                                    {
                                        "data_source_reference": {
                                            "kind": "image",
                                            "name": "dockeree-centos7",
                                            "uuid": "50c738a8-5ad2-427b-a347-b34a6a966212"
                                        },
                                        "device_properties": {
                                            "device_type": "DISK",
                                            "disk_address": {
                                                "adapter_type": "IDE",
                                                "device_index": 0
                                            }
                                        }
                                    }
                                ],
                                "memory_size_mib": 2048,
                                "nic_list": [
                                    {
                                        "ip_endpoint_list": [
                                        ],
                                        "subnet_reference": {
                                            "uuid": "a40db72c-d40e-4783-b213-c7fbd72cb134"
                                        }
                                    }
                                ],
                                "num_sockets": "1",
                                "num_vcpus_per_socket": "1"
                            }
                        },
                        "name": "pet server_nut",
                        "os_type": "Linux",
                        "readiness_probe": {
                            "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
                            "connection_port": 22,
                            "connection_type": "SSH",
                            "disable_readiness_probe": False,
                            "login_credential_local_reference": {
                                "kind": "app_credential",
                                "uuid": "8549b4a1-d06d-1d45-c850-0ca3604d702a"
                            },
                            "timeout_secs": "60"
                        },
                        "type": "AHV_VM",
                        "uuid": "5ed28fcf-b92e-923a-640b-206d0dce940a",
                        "variable_list": [
                        ]
                    }
                ]
            }
        }
    }

    return body

def get_pet_nutanix_body(newName, appVar, spec_version):
    body = {
        "api_version": "3.0",
        "metadata": {
            "categories": {
            },
            "creation_time": "1513203430452577",
            "kind": "blueprint",
            "last_update_time": "1513876786334140",
            "name": "Pet Clinic",
            "owner_reference": {
                "kind": "user",
                "name": "admin",
                "uuid": "00000000-0000-0000-0000-000000000000"
            },
            "project_reference": {
                "kind": "project",
                "name": "Nutanix_Demo1",
                "uuid": "caddfb46-bb7f-4fda-9290-46fb1de64c3c"
            },
            "spec_version": spec_version,
            "uuid": "84922775-5fbc-fd8d-af76-57b8181c60e4"
        },
        "spec": {
            "app_profile_reference": {
                "kind": "app_profile",
                "uuid": "52df6135-8bec-f0b3-224f-7734b24c9cad"
            },
            "application_name": newName,
            "resources": {
                "app_profile_list": [
                    {
                        "action_list": [
                        ],
                        "deployment_create_list": [
                            {
                                "action_list": [
                                ],
                                "editables": {
                                },
                                "max_replicas": "1",
                                "min_replicas": "1",
                                "name": "218e961a_deployment",
                                "package_local_reference_list": [
                                    {
                                        "kind": "app_package",
                                        "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5"
                                    }
                                ],
                                "substrate_local_reference": {
                                    "kind": "app_substrate",
                                    "uuid": "7af1c09e-2c84-c0a0-3460-b0559a7f4eda"
                                },
                                "uuid": "c5d37072-a4ef-98d4-b4a2-a5062894695a",
                                "variable_list": [
                                ]
                            }
                        ],
                        "name": "aws_ap",
                        "uuid": "c9d1adc7-2279-6fd8-e443-7968a6eaef60",
                        "variable_list": [
                            {
                                "attrs": {
                                },
                                "description": "",
                                "label": "",
                                "name": "IGNW_INSTALLURL",
                                "type": "LOCAL",
                                "uuid": "4121985b-d393-d3fb-cd96-574f751181a3",
                                "val_type": "STRING",
                                "value": "https://raw.githubusercontent.com/tigelane/spring-petclinic/master/setup_server.sh"
                            },
                            {
                                "attrs": {
                                },
                                "description": "",
                                "editables": {
                                    "value": True
                                },
                                "label": "",
                                "name": "IGNW_BRANCH",
                                "type": "LOCAL",
                                "uuid": "24f5824d-5911-b177-ed99-8440e0f9f5b5",
                                "val_type": "STRING",
                                "value": ""
                            }
                        ]
                    },
                    {
                        "action_list": [
                        ],
                        "deployment_create_list": [
                            {
                                "action_list": [
                                ],
                                "max_replicas": "1",
                                "min_replicas": "1",
                                "name": "218e961a_deployment_cloned_1",
                                "package_local_reference_list": [
                                    {
                                        "kind": "app_package",
                                        "uuid": "02a9f80f-d693-62c8-7775-498909904bec"
                                    }
                                ],
                                "substrate_local_reference": {
                                    "kind": "app_substrate",
                                    "uuid": "5ed28fcf-b92e-923a-640b-206d0dce940a"
                                },
                                "uuid": "2e695e24-aff1-2c8a-987b-732a73c28524",
                                "variable_list": [
                                ]
                            }
                        ],
                        "name": "nut_ap",
                        "uuid": "52df6135-8bec-f0b3-224f-7734b24c9cad",
                        "variable_list": [
                            {
                                "attrs": {
                                },
                                "description": "",
                                "label": "",
                                "name": "IGNW_INSTALLURL",
                                "type": "LOCAL",
                                "uuid": "b00e5fc4-539a-5a24-58b3-490cc22ea1b4",
                                "val_type": "STRING",
                                "value": "https://raw.githubusercontent.com/tigelane/spring-petclinic/master/setup_server.sh"
                            },
                            {
                                "attrs": {
                                },
                                "description": "",
                                "editables": {
                                    "value": True
                                },
                                "label": "",
                                "name": "IGNW_BRANCH",
                                "type": "LOCAL",
                                "uuid": "5fd315fe-3364-111e-e4da-535b19547612",
                                "val_type": "STRING",
                                "value": appVar
                            }
                        ]
                    }
                ],
                "client_attrs": {
                    "166f0e95-8a51-493c-f6ce-032dd02eb1ad": {
                        "x": 400,
                        "y": 280
                    }
                },
                "credential_definition_list": [
                    {
                        "name": "AWS",
                        "secret": {
                            "attrs": {
                                "is_secret_modified": False
                            }
                        },
                        "type": "KEY",
                        "username": "ec2-user",
                        "uuid": "97969849-a39c-fad6-c0c9-a044aa2aed34"
                    },
                    {
                        "name": "ignw",
                        "secret": {
                            "attrs": {
                                "is_secret_modified": False
                            }
                        },
                        "type": "PASSWORD",
                        "username": "ignw",
                        "uuid": "8549b4a1-d06d-1d45-c850-0ca3604d702a"
                    }
                ],
                "default_credential_local_reference": {
                    "kind": "app_credential",
                    "name": "default_credential",
                    "uuid": "97969849-a39c-fad6-c0c9-a044aa2aed34"
                },
                "package_definition_list": [
                    {
                        "name": "package",
                        "options": {
                            "install_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "5a17adba-e735-95f4-1ac8-9b947d997fca"
                                },
                                "name": "15e3bbf6_runbook",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                            {
                                                "kind": "app_task",
                                                "uuid": "110be21f-fc1b-cefc-7edb-251f42c1572c"
                                            }
                                        ],
                                        "name": "7f891ab9_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5"
                                        },
                                        "type": "DAG",
                                        "uuid": "5a17adba-e735-95f4-1ac8-9b947d997fca",
                                        "variable_list": [
                                        ]
                                    },
                                    {
                                        "attrs": {
                                            "login_credential_local_reference": {
                                                "kind": "app_credential",
                                                "uuid": "97969849-a39c-fad6-c0c9-a044aa2aed34"
                                            },
                                            "script": "echo export IGNW_INSTALLURL=@@{IGNW_INSTALLURL}@@ > envv.sh\necho export IGNW_BRANCH=@@{IGNW_BRANCH}@@ >> envv.sh\n\ncurl @@{IGNW_INSTALLURL}@@ > setup_server.sh\nchmod 766 setup_server.sh\n./setup_server.sh",
                                            "script_type": "sh"
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "PackageInstallTask",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5"
                                        },
                                        "type": "EXEC",
                                        "uuid": "110be21f-fc1b-cefc-7edb-251f42c1572c",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "41767ffd-5c09-bbe5-299a-fd9d78295e02",
                                "variable_list": [
                                ]
                            },
                            "uninstall_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "6cdc6b91-2288-951b-26e4-784c3d5fe48c"
                                },
                                "name": "5e5fb7ed_runbook",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "2e9826ad_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5"
                                        },
                                        "type": "DAG",
                                        "uuid": "6cdc6b91-2288-951b-26e4-784c3d5fe48c",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "8145c76e-3b63-504d-e6a2-b1199dfe7bea",
                                "variable_list": [
                                ]
                            }
                        },
                        "service_local_reference_list": [
                            {
                                "kind": "app_service",
                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                            }
                        ],
                        "type": "DEB",
                        "uuid": "0fbdc976-389a-3a93-76f8-8d3fcde546c5",
                        "variable_list": [
                        ]
                    },
                    {
                        "name": "package_nut",
                        "options": {
                            "install_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "0b4a4b20-eb54-93af-67e4-4df67c66d56b"
                                },
                                "name": "15e3bbf6_runbook_cloned_1",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                            {
                                                "kind": "app_task",
                                                "uuid": "dd27f562-dd77-dcfc-44a2-37361464ee39"
                                            }
                                        ],
                                        "name": "7f891ab9_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "02a9f80f-d693-62c8-7775-498909904bec"
                                        },
                                        "type": "DAG",
                                        "uuid": "0b4a4b20-eb54-93af-67e4-4df67c66d56b",
                                        "variable_list": [
                                        ]
                                    },
                                    {
                                        "attrs": {
                                            "login_credential_local_reference": {
                                                "kind": "app_credential",
                                                "uuid": "8549b4a1-d06d-1d45-c850-0ca3604d702a"
                                            },
                                            "script": "echo export IGNW_INSTALLURL=@@{IGNW_INSTALLURL}@@ > envv.sh\necho export IGNW_BRANCH=@@{IGNW_BRANCH}@@ >> envv.sh\n\ncurl @@{IGNW_INSTALLURL}@@ > setup_server.sh\nchmod 766 setup_server.sh\n./setup_server.sh",
                                            "script_type": "sh"
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "PackageInstallTask",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "02a9f80f-d693-62c8-7775-498909904bec"
                                        },
                                        "type": "EXEC",
                                        "uuid": "dd27f562-dd77-dcfc-44a2-37361464ee39",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "6fd1515b-abce-c59a-e99a-44fba8ed4a0d",
                                "variable_list": [
                                ]
                            },
                            "uninstall_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "56e1ddb8-237f-a91a-36d1-52c52136bb47"
                                },
                                "name": "5e5fb7ed_runbook_cloned_1",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "2e9826ad_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "02a9f80f-d693-62c8-7775-498909904bec"
                                        },
                                        "type": "DAG",
                                        "uuid": "56e1ddb8-237f-a91a-36d1-52c52136bb47",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "c22105d4-03ba-5e49-8721-2b7286a60dd4",
                                "variable_list": [
                                ]
                            }
                        },
                        "service_local_reference_list": [
                            {
                                "kind": "app_service",
                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                            }
                        ],
                        "type": "DEB",
                        "uuid": "02a9f80f-d693-62c8-7775-498909904bec",
                        "variable_list": [
                        ]
                    }
                ],
                "service_definition_list": [
                    {
                        "action_list": [
                            {
                                "critical": False,
                                "name": "action_create",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "c19d6abe-6fd0-665a-8304-232d8b3237a7"
                                    },
                                    "name": "f894c047_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "895b19a6_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "c19d6abe-6fd0-665a-8304-232d8b3237a7",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "3f12a589-0d2c-7d83-ef84-0d69a45c0013",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "a8c79579-ed6f-59ef-3524-0d27180f37f6"
                            },
                            {
                                "critical": False,
                                "name": "action_delete",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "aa066a5e-7cc1-ff2c-20b3-5242a852be4b"
                                    },
                                    "name": "80b1769f_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "aacc0d91_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "aa066a5e-7cc1-ff2c-20b3-5242a852be4b",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "b72cb73d-deac-5f96-cc08-bf1413a59aca",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "e899503c-4063-9cc7-c0a6-a56b27d37787"
                            },
                            {
                                "critical": False,
                                "name": "action_start",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "ac09e5d6-cde8-4bc6-3402-5c512162c4fb"
                                    },
                                    "name": "0347d817_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "820484d2_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "ac09e5d6-cde8-4bc6-3402-5c512162c4fb",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "11117dbd-9e34-5f4c-6303-a0241e70ace0",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "aebc41a8-d414-e1d8-aee2-ec72d9aece13"
                            },
                            {
                                "critical": False,
                                "name": "action_stop",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "eb150869-8073-1404-bc97-bc491c7066de"
                                    },
                                    "name": "589d4a52_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "5019dc25_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "eb150869-8073-1404-bc97-bc491c7066de",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "a2ec7f36-e64e-a296-7af3-8cf65abe68ac",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "9c11bbab-fdee-d189-0d15-cebe28b8ffed"
                            },
                            {
                                "critical": False,
                                "name": "action_restart",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "9fbd3008-b098-28ea-77e1-f667407b4c9d"
                                    },
                                    "name": "32fbb0ec_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "ceba1eb1_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad"
                                            },
                                            "type": "DAG",
                                            "uuid": "9fbd3008-b098-28ea-77e1-f667407b4c9d",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "80c2f6cd-5b2f-3879-2063-42931d1a4a37",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "354e13c1-20a3-25c1-b744-6e2979f42ae3"
                            }
                        ],
                        "depends_on_list": [
                        ],
                        "name": "PetServer",
                        "port_list": [
                        ],
                        "singleton": False,
                        "uuid": "166f0e95-8a51-493c-f6ce-032dd02eb1ad",
                        "variable_list": [
                        ]
                    }
                ],
                "substrate_definition_list": [
                    {
                        "action_list": [
                        ],
                        "create_spec": {
                            "name": "@@{calm_blueprint_name}@@-@@{calm_random}@@",
                            "resources": {
                                "account_uuid": "f0b79f8a-c1d8-3090-a367-56ae3d230917",
                                "associate_public_ip_address": True,
                                "availability_zone": "us-west-2a",
                                "block_device_map": {
                                    "root_disk": {
                                        "delete_on_termination": True,
                                        "device_name": "/dev/sdb",
                                        "size_gb": 8,
                                        "volume_type": "GP2"
                                    }
                                },
                                "image_id": "ami-39802141",
                                "instance_initiated_shutdown_behavior": "TERMINATE",
                                "instance_profile_name": None,
                                "instance_type": "t2.small",
                                "key_name": "ignw_dev-west2",
                                "region": "us-west-2",
                                "security_group_list": [
                                    {
                                        "security_group_id": "sg-7523a309"
                                    }
                                ],
                                "subnet_id": "subnet-de2aaab9",
                                "vpc_id": "vpc-0a11796d"
                            },
                            "type": "PROVISION_AWS_VM"
                        },
                        "name": "pet server",
                        "os_type": "Linux",
                        "readiness_probe": {
                            "address": "@@{public_ip_address}@@",
                            "connection_port": 22,
                            "connection_type": "SSH",
                            "disable_readiness_probe": False,
                            "login_credential_local_reference": {
                                "kind": "app_credential",
                                "uuid": "97969849-a39c-fad6-c0c9-a044aa2aed34"
                            }
                        },
                        "type": "AWS_VM",
                        "uuid": "7af1c09e-2c84-c0a0-3460-b0559a7f4eda",
                        "variable_list": [
                        ]
                    },
                    {
                        "action_list": [
                        ],
                        "create_spec": {
                            "name": "@@{calm_blueprint_name}@@-@@{calm_random}@@",
                            "resources": {
                                "boot_config": {
                                    "boot_device": {
                                        "disk_address": {
                                            "adapter_type": "IDE",
                                            "device_index": 0
                                        }
                                    }
                                },
                                "disk_list": [
                                    {
                                        "data_source_reference": {
                                            "kind": "image",
                                            "name": "dockeree-centos7",
                                            "uuid": "50c738a8-5ad2-427b-a347-b34a6a966212"
                                        },
                                        "device_properties": {
                                            "device_type": "DISK",
                                            "disk_address": {
                                                "adapter_type": "IDE",
                                                "device_index": 0
                                            }
                                        }
                                    }
                                ],
                                "memory_size_mib": 2048,
                                "nic_list": [
                                    {
                                        "ip_endpoint_list": [
                                        ],
                                        "subnet_reference": {
                                            "uuid": "a40db72c-d40e-4783-b213-c7fbd72cb134"
                                        }
                                    }
                                ],
                                "num_sockets": "1",
                                "num_vcpus_per_socket": "1"
                            }
                        },
                        "name": "pet server_nut",
                        "os_type": "Linux",
                        "readiness_probe": {
                            "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
                            "connection_port": 22,
                            "connection_type": "SSH",
                            "disable_readiness_probe": False,
                            "login_credential_local_reference": {
                                "kind": "app_credential",
                                "uuid": "8549b4a1-d06d-1d45-c850-0ca3604d702a"
                            },
                            "timeout_secs": "60"
                        },
                        "type": "AHV_VM",
                        "uuid": "5ed28fcf-b92e-923a-640b-206d0dce940a",
                        "variable_list": [
                        ]
                    }
                ]
            }
        }
    }

    return body

def get_swarm_aws_body(newName, appVar, spec_version):
    body = {}

    return body

def get_swarm_nutanix_body(newName, appVar, spec_version):
    body = {
        "api_version": "3.0",
        "metadata": {
            "categories": {
            },
            "creation_time": "1513378383427171",
            "kind": "blueprint",
            "last_update_time": "1513730970131118",
            "name": "IGNW Docker",
            "owner_reference": {
                "kind": "user",
                "name": "admin",
                "uuid": "00000000-0000-0000-0000-000000000000"
            },
            "project_reference": {
                "kind": "project",
                "name": "Nutanix_Demo1",
                "uuid": "caddfb46-bb7f-4fda-9290-46fb1de64c3c"
            },
            "spec_version": spec_version,
            "uuid": "1c16ecfb-6bb8-3212-261b-1d2d5967c8d2"
        },
        "spec": {
            "app_profile_reference": {
                "kind": "app_profile",
                "uuid": "808f77fc-d677-a4cd-e930-af23cd4a42da"
            },
            "application_name": newName,
            "resources": {
                "app_profile_list": [
                    {
                        "action_list": [
                        ],
                        "deployment_create_list": [
                            {
                                "action_list": [
                                ],
                                "max_replicas": "1",
                                "min_replicas": "1",
                                "name": "6f739694_deployment",
                                "package_local_reference_list": [
                                    {
                                        "kind": "app_package",
                                        "uuid": "de206472-aeb4-d2ce-b0a0-12e19f73b938"
                                    }
                                ],
                                "substrate_local_reference": {
                                    "kind": "app_substrate",
                                    "uuid": "8a1ec8f1-097c-ff99-6955-dfadf01adb79"
                                },
                                "uuid": "101968a4-f10e-62ae-38e0-292266706b3a",
                                "variable_list": [
                                ]
                            },
                            {
                                "action_list": [
                                ],
                                "editables": {
                                    "min_replicas": True
                                },
                                "max_replicas": "4",
                                "min_replicas": "4",
                                "name": "6f739694_deployment_cloned_1",
                                "package_local_reference_list": [
                                    {
                                        "kind": "app_package",
                                        "uuid": "92c44fc0-2ae6-8a22-4608-daf3e712a9b4"
                                    }
                                ],
                                "substrate_local_reference": {
                                    "kind": "app_substrate",
                                    "uuid": "8669038a-1f95-19fe-ed2f-cec1f546cd7f"
                                },
                                "uuid": "265345ae-6d68-1498-5ea3-77bf35f7fe1a",
                                "variable_list": [
                                ]
                            }
                        ],
                        "name": "Nut_Pro",
                        "uuid": "808f77fc-d677-a4cd-e930-af23cd4a42da",
                        "variable_list": [
                            {
                                "attrs": {
                                },
                                "description": "",
                                "label": "",
                                "name": "IGNW_INSTALLURL",
                                "type": "LOCAL",
                                "uuid": "aa8fb078-c64c-a634-f931-20e04d1fe549",
                                "val_type": "STRING",
                                "value": "https://raw.githubusercontent.com/IGNW/nutanix-lab/master/demos/docker-cluster/install-docker-ee.sh"
                            },
                            {
                                "attrs": {
                                },
                                "description": "",
                                "editables": {
                                    "value": True
                                },
                                "label": "",
                                "name": "IGNW_SWARMNUM",
                                "type": "LOCAL",
                                "uuid": "8c5a50eb-75b0-12d4-bbf7-291111dd6685",
                                "val_type": "STRING",
                                "value": appVar
                            }
                        ]
                    }
                ],
                "client_attrs": {
                    "956843ba-110a-d103-fc59-9ef58b3d2957": {
                        "x": 480,
                        "y": 260
                    },
                    "e752e809-37c0-5fb4-b653-b2aa24bd917f": {
                        "x": 320,
                        "y": 20
                    }
                },
                "credential_definition_list": [
                    {
                        "name": "Centos",
                        "secret": {
                            "attrs": {
                                "is_secret_modified": False
                            }
                        },
                        "type": "PASSWORD",
                        "username": "ignw",
                        "uuid": "199b46aa-1577-47c7-76a6-d42c140fc634"
                    }
                ],
                "default_credential_local_reference": {
                    "kind": "app_credential",
                    "name": "default_credential",
                    "uuid": "199b46aa-1577-47c7-76a6-d42c140fc634"
                },
                "package_definition_list": [
                    {
                        "name": "Docker_Pack_Manager",
                        "options": {
                            "install_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "ebcffe64-69ab-47be-b635-4a4ea2aa8866"
                                },
                                "name": "87e2d011_runbook",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                            {
                                                "kind": "app_task",
                                                "uuid": "9c523212-5dea-4901-4a89-a3d98636aa4c"
                                            }
                                        ],
                                        "name": "50a44b9e_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "de206472-aeb4-d2ce-b0a0-12e19f73b938"
                                        },
                                        "type": "DAG",
                                        "uuid": "ebcffe64-69ab-47be-b635-4a4ea2aa8866",
                                        "variable_list": [
                                        ]
                                    },
                                    {
                                        "attrs": {
                                            "login_credential_local_reference": {
                                                "kind": "app_credential",
                                                "uuid": "199b46aa-1577-47c7-76a6-d42c140fc634"
                                            },
                                            "script": "# This script is pasted into the package installer script\n# window of the Calm interface.\n\necho export IGNW_INSTALLURL=@@{IGNW_INSTALLURL}@@ > envv.sh\necho export IGNW_SWARMNUM=@@{IGNW_SWARMNUM}@@ >> envv.sh\necho export HOSTNAME=@@{name}@@ >> envv.sh\necho export IPADDRESS=@@{address}@@ >> envv.sh\nexport HOSTNAME=@@{name}@@\n\nsudo hostnamectl set-hostname \"@@{name}@@}\"\n\ncurl @@{IGNW_INSTALLURL}@@ > setup_server.sh\nchmod 766 setup_server.sh\n./setup_server.sh",
                                            "script_type": "sh"
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "PackageInstallTask",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "de206472-aeb4-d2ce-b0a0-12e19f73b938"
                                        },
                                        "type": "EXEC",
                                        "uuid": "9c523212-5dea-4901-4a89-a3d98636aa4c",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "de947682-678b-42dc-9b52-646b9967967f",
                                "variable_list": [
                                ]
                            },
                            "uninstall_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "7f5122d4-2f4c-4d29-0cea-ec394f585637"
                                },
                                "name": "9459fd8d_runbook",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "c45b4e8f_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "de206472-aeb4-d2ce-b0a0-12e19f73b938"
                                        },
                                        "type": "DAG",
                                        "uuid": "7f5122d4-2f4c-4d29-0cea-ec394f585637",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "9ae8d29d-dcd7-a756-089b-78b2f6c8e41a",
                                "variable_list": [
                                ]
                            }
                        },
                        "service_local_reference_list": [
                            {
                                "kind": "app_service",
                                "uuid": "e752e809-37c0-5fb4-b653-b2aa24bd917f"
                            }
                        ],
                        "type": "DEB",
                        "uuid": "de206472-aeb4-d2ce-b0a0-12e19f73b938",
                        "variable_list": [
                        ]
                    },
                    {
                        "name": "Docker_Pack_Worker",
                        "options": {
                            "install_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "3f0c7482-f29f-106d-5454-72e15f8ba262"
                                },
                                "name": "87e2d011_runbook_cloned_1",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                            {
                                                "kind": "app_task",
                                                "uuid": "1108dbde-f714-923c-a626-b00e3d11e62a"
                                            }
                                        ],
                                        "name": "50a44b9e_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "92c44fc0-2ae6-8a22-4608-daf3e712a9b4"
                                        },
                                        "type": "DAG",
                                        "uuid": "3f0c7482-f29f-106d-5454-72e15f8ba262",
                                        "variable_list": [
                                        ]
                                    },
                                    {
                                        "attrs": {
                                            "login_credential_local_reference": {
                                                "kind": "app_credential",
                                                "uuid": "199b46aa-1577-47c7-76a6-d42c140fc634"
                                            },
                                            "script": "# This script is pasted into the package installer script\n# window of the Calm interface.\n\necho export IGNW_INSTALLURL=@@{IGNW_INSTALLURL}@@ > envv.sh\necho export IGNW_SWARMNUM=@@{IGNW_SWARMNUM}@@ >> envv.sh\necho export HOSTNAME=@@{name}@@ >> envv.sh\necho export IPADDRESS=@@{address}@@ >> envv.sh\necho export SWARM_MANAGER_ADDRESS=@@{manager.address}@@ >> envv.sh\nexport HOSTNAME=@@{name}@@\n\nsudo hostnamectl set-hostname \"@@{name}@@}\"\n\ncurl @@{IGNW_INSTALLURL}@@ > setup_server.sh\nchmod 766 setup_server.sh\n./setup_server.sh\n",
                                            "script_type": "sh"
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "PackageInstallTask",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "92c44fc0-2ae6-8a22-4608-daf3e712a9b4"
                                        },
                                        "type": "EXEC",
                                        "uuid": "1108dbde-f714-923c-a626-b00e3d11e62a",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "e66277cc-4529-c815-b975-039b661ecd8e",
                                "variable_list": [
                                ]
                            },
                            "uninstall_runbook": {
                                "main_task_local_reference": {
                                    "kind": "app_task",
                                    "uuid": "45f20f56-e8ee-0cb2-d47c-e06b44fcbbc4"
                                },
                                "name": "9459fd8d_runbook_cloned_1",
                                "task_definition_list": [
                                    {
                                        "attrs": {
                                            "edges": [
                                            ]
                                        },
                                        "child_tasks_local_reference_list": [
                                        ],
                                        "name": "c45b4e8f_dag",
                                        "target_any_local_reference": {
                                            "kind": "app_package",
                                            "uuid": "92c44fc0-2ae6-8a22-4608-daf3e712a9b4"
                                        },
                                        "type": "DAG",
                                        "uuid": "45f20f56-e8ee-0cb2-d47c-e06b44fcbbc4",
                                        "variable_list": [
                                        ]
                                    }
                                ],
                                "uuid": "f8f7bef1-8621-2941-cf9b-e3e62b408f2a",
                                "variable_list": [
                                ]
                            }
                        },
                        "service_local_reference_list": [
                            {
                                "kind": "app_service",
                                "uuid": "956843ba-110a-d103-fc59-9ef58b3d2957"
                            }
                        ],
                        "type": "DEB",
                        "uuid": "92c44fc0-2ae6-8a22-4608-daf3e712a9b4",
                        "variable_list": [
                        ]
                    }
                ],
                "service_definition_list": [
                    {
                        "action_list": [
                            {
                                "critical": False,
                                "name": "action_create",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "0178b6cb-f8d7-5685-7949-0158bd8e9553"
                                    },
                                    "name": "b472408d_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "9d8a7a69_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "e752e809-37c0-5fb4-b653-b2aa24bd917f"
                                            },
                                            "type": "DAG",
                                            "uuid": "0178b6cb-f8d7-5685-7949-0158bd8e9553",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "c65340e4-9014-8f47-e9c4-c6b94288113a",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "92528429-c745-9a99-c606-d99558b1f84c"
                            },
                            {
                                "critical": False,
                                "name": "action_delete",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "3d2192d8-c93d-d227-6b41-6694d1182bf3"
                                    },
                                    "name": "0c43a4d8_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "76db5888_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "e752e809-37c0-5fb4-b653-b2aa24bd917f"
                                            },
                                            "type": "DAG",
                                            "uuid": "3d2192d8-c93d-d227-6b41-6694d1182bf3",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "383190c5-b03d-752f-b0a0-b09b20c0303d",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "d1f3474a-8589-77cf-af2a-5fa9cf385a25"
                            },
                            {
                                "critical": False,
                                "name": "action_start",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "1233de90-95e4-c8ce-9277-7bb8e71b16c7"
                                    },
                                    "name": "ba17e4b5_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "afdc2196_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "e752e809-37c0-5fb4-b653-b2aa24bd917f"
                                            },
                                            "type": "DAG",
                                            "uuid": "1233de90-95e4-c8ce-9277-7bb8e71b16c7",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "9e530bd8-4e10-5166-dd1b-c46f89eea512",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "5fe8b3a8-cdd3-ddde-964c-339c75a0a0fb"
                            },
                            {
                                "critical": False,
                                "name": "action_stop",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "baa39606-fc85-8536-4202-b0745604ca86"
                                    },
                                    "name": "6a66a999_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "e6043b97_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "e752e809-37c0-5fb4-b653-b2aa24bd917f"
                                            },
                                            "type": "DAG",
                                            "uuid": "baa39606-fc85-8536-4202-b0745604ca86",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "a6b2342c-ad79-3f21-bb88-52f264072593",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "94356105-f6cd-a49f-14ce-59c5a1bded41"
                            },
                            {
                                "critical": False,
                                "name": "action_restart",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "d9fb164a-a72c-5697-d288-ebbe7eaa3d19"
                                    },
                                    "name": "b2e5bb3b_runbook",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "530a1978_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "e752e809-37c0-5fb4-b653-b2aa24bd917f"
                                            },
                                            "type": "DAG",
                                            "uuid": "d9fb164a-a72c-5697-d288-ebbe7eaa3d19",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "59bb1283-5968-8e8f-344c-ba9fa7e084bc",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "58b53b58-85ec-5564-6045-b25f51a47337"
                            }
                        ],
                        "depends_on_list": [
                        ],
                        "name": "manager",
                        "port_list": [
                        ],
                        "singleton": False,
                        "uuid": "e752e809-37c0-5fb4-b653-b2aa24bd917f",
                        "variable_list": [
                        ]
                    },
                    {
                        "action_list": [
                            {
                                "critical": False,
                                "name": "action_create",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "74d88981-a2a7-305b-6484-8a81a189c904"
                                    },
                                    "name": "b472408d_runbook_cloned_1",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "9d8a7a69_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "956843ba-110a-d103-fc59-9ef58b3d2957"
                                            },
                                            "type": "DAG",
                                            "uuid": "74d88981-a2a7-305b-6484-8a81a189c904",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "a0196ad2-9cb0-3dd2-d920-a8109a5ab511",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "2c7fc94f-bbbf-9d30-13c7-599ff5ec94b0"
                            },
                            {
                                "critical": False,
                                "name": "action_delete",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "7fe362a6-560a-0e99-c67a-68c6282de762"
                                    },
                                    "name": "0c43a4d8_runbook_cloned_1",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "76db5888_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "956843ba-110a-d103-fc59-9ef58b3d2957"
                                            },
                                            "type": "DAG",
                                            "uuid": "7fe362a6-560a-0e99-c67a-68c6282de762",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "bba0ae98-b01e-a888-acec-47e6b0426cd0",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "59dc17dc-22ab-e102-0a34-fac8b825d735"
                            },
                            {
                                "critical": False,
                                "name": "action_start",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "60a6e462-dfc7-6ab0-182e-898deb8b909a"
                                    },
                                    "name": "ba17e4b5_runbook_cloned_1",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "afdc2196_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "956843ba-110a-d103-fc59-9ef58b3d2957"
                                            },
                                            "type": "DAG",
                                            "uuid": "60a6e462-dfc7-6ab0-182e-898deb8b909a",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "e0ba0088-b5bd-b4f3-eadd-c9db7bff67c6",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "ea21d973-9447-cd77-b7c0-be128db1b667"
                            },
                            {
                                "critical": False,
                                "name": "action_stop",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "37110049-d303-1f6e-1349-5efd3ba1c942"
                                    },
                                    "name": "6a66a999_runbook_cloned_1",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "e6043b97_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "956843ba-110a-d103-fc59-9ef58b3d2957"
                                            },
                                            "type": "DAG",
                                            "uuid": "37110049-d303-1f6e-1349-5efd3ba1c942",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "4ea44278-16d7-3d4b-e26a-50a1f14cbc0a",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "63422ff0-684f-d548-39e7-bcda99330160"
                            },
                            {
                                "critical": False,
                                "name": "action_restart",
                                "runbook": {
                                    "main_task_local_reference": {
                                        "kind": "app_task",
                                        "uuid": "a9bfa789-ef0c-f951-64c4-bbbed6e08f26"
                                    },
                                    "name": "b2e5bb3b_runbook_cloned_1",
                                    "task_definition_list": [
                                        {
                                            "attrs": {
                                                "edges": [
                                                ]
                                            },
                                            "child_tasks_local_reference_list": [
                                            ],
                                            "name": "530a1978_dag",
                                            "target_any_local_reference": {
                                                "kind": "app_service",
                                                "uuid": "956843ba-110a-d103-fc59-9ef58b3d2957"
                                            },
                                            "type": "DAG",
                                            "uuid": "a9bfa789-ef0c-f951-64c4-bbbed6e08f26",
                                            "variable_list": [
                                            ]
                                        }
                                    ],
                                    "uuid": "b321a4f5-a2f8-77bf-dbad-9ba04b8558b3",
                                    "variable_list": [
                                    ]
                                },
                                "type": "system",
                                "uuid": "86470239-0a0d-e57d-467f-fc1c6a8914cf"
                            }
                        ],
                        "depends_on_list": [
                            {
                                "kind": "app_service",
                                "uuid": "e752e809-37c0-5fb4-b653-b2aa24bd917f"
                            }
                        ],
                        "name": "worker",
                        "port_list": [
                        ],
                        "singleton": False,
                        "uuid": "956843ba-110a-d103-fc59-9ef58b3d2957",
                        "variable_list": [
                        ]
                    }
                ],
                "substrate_definition_list": [
                    {
                        "action_list": [
                        ],
                        "create_spec": {
                            "name": "swarm@@{IGNW_SWARMNUM}@@-manager",
                            "resources": {
                                "boot_config": {
                                    "boot_device": {
                                        "disk_address": {
                                            "adapter_type": "IDE",
                                            "device_index": 0
                                        }
                                    }
                                },
                                "disk_list": [
                                    {
                                        "data_source_reference": {
                                            "kind": "image",
                                            "name": "dockeree-centos7",
                                            "uuid": "50c738a8-5ad2-427b-a347-b34a6a966212"
                                        },
                                        "device_properties": {
                                            "device_type": "DISK",
                                            "disk_address": {
                                                "adapter_type": "IDE",
                                                "device_index": 0
                                            }
                                        }
                                    }
                                ],
                                "memory_size_mib": 8192,
                                "nic_list": [
                                    {
                                        "ip_endpoint_list": [
                                        ],
                                        "subnet_reference": {
                                            "uuid": "a40db72c-d40e-4783-b213-c7fbd72cb134"
                                        }
                                    }
                                ],
                                "num_sockets": "2",
                                "num_vcpus_per_socket": "2"
                            }
                        },
                        "editables": {
                            "create_spec": {
                                "resources": {
                                }
                            }
                        },
                        "name": "Docker Manager",
                        "os_type": "Linux",
                        "readiness_probe": {
                            "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
                            "connection_port": 22,
                            "connection_type": "SSH",
                            "disable_readiness_probe": False,
                            "login_credential_local_reference": {
                                "kind": "app_credential",
                                "uuid": "199b46aa-1577-47c7-76a6-d42c140fc634"
                            },
                            "timeout_secs": "60"
                        },
                        "type": "AHV_VM",
                        "uuid": "8a1ec8f1-097c-ff99-6955-dfadf01adb79",
                        "variable_list": [
                        ]
                    },
                    {
                        "action_list": [
                        ],
                        "create_spec": {
                            "name": "swarm@@{IGNW_SWARMNUM}@@-worker@@{calm_random}@@",
                            "resources": {
                                "boot_config": {
                                    "boot_device": {
                                        "disk_address": {
                                            "adapter_type": "IDE",
                                            "device_index": 0
                                        }
                                    }
                                },
                                "disk_list": [
                                    {
                                        "data_source_reference": {
                                            "kind": "image",
                                            "name": "dockeree-centos7",
                                            "uuid": "50c738a8-5ad2-427b-a347-b34a6a966212"
                                        },
                                        "device_properties": {
                                            "device_type": "DISK",
                                            "disk_address": {
                                                "adapter_type": "IDE",
                                                "device_index": 0
                                            }
                                        }
                                    }
                                ],
                                "memory_size_mib": 8192,
                                "nic_list": [
                                    {
                                        "ip_endpoint_list": [
                                        ],
                                        "subnet_reference": {
                                            "uuid": "a40db72c-d40e-4783-b213-c7fbd72cb134"
                                        }
                                    }
                                ],
                                "num_sockets": "2",
                                "num_vcpus_per_socket": "2"
                            }
                        },
                        "name": "Docker Worker",
                        "os_type": "Linux",
                        "readiness_probe": {
                            "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
                            "connection_port": 22,
                            "connection_type": "SSH",
                            "disable_readiness_probe": False,
                            "login_credential_local_reference": {
                                "kind": "app_credential",
                                "uuid": "199b46aa-1577-47c7-76a6-d42c140fc634"
                            },
                            "timeout_secs": "60"
                        },
                        "type": "AHV_VM",
                        "uuid": "8669038a-1f95-19fe-ed2f-cec1f546cd7f",
                        "variable_list": [
                        ]
                    }
                ]
            }
        }
    }


    return body


if __name__ == '__main__':
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
