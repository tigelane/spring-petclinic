import subprocess
import calm_execute

class Command(object):
    def __init__(self):
        self.commands = {
            "apps" : self.apps_list,
            "build" : self.build,
            "delete" :self.delete,
            "help" : self.help
        }

    def handle_command(self, user, command):
        response = "<@" + user + ">: "
        command = command.split()

        if command[0] in self.commands:
            response += self.commands[command[0]](command)
        else:
            response += "Sorry I don't understand the command: " + command[0] + ". " + self.help()

        return response

    def apps_list(self, command):
        response = calm_execute.apps_list()
        myReturn = ""

        if len(response) > 0:
            for item in response:
                myReturn += "{0}, ".format(item["name"])

            myReturn = myReturn[:-2]
            myReturn = "The running applications are: {0}".format(myReturn)

        else:
            myReturn = "No applications found. {}".format(response)

        return myReturn

    def build(self, command):
        try:
            appName = command[2]
            appVar = command[3]
            cloud = command[4]
        except:
            return "Sorry, not enough arguments."

        if command[1] == "pet":
            response = calm_execute.create_pet(appName, appVar, cloud)

        elif command[1] == "swarm":
            response = calm_execute.create_swarm(appName, appVar, cloud)

        else:
            return "I'm sorry.  That's an unknown application."

        if len(response) > 0:
            myReturn = response
        else:
            myReturn = "Unable to build {0} on cloud {1}".format(appName, cloud)

        return myReturn

    def delete(self, command):
        if len(command) < 2:
            return "{} requrires an app name.".format(command[0])

        response = calm_execute.delete(command[1])

        if len(response) > 0:
            myReturn = response
        else:
            myReturn = "No applications found. {}".format(response)

        return myReturn

    def help(self):
        response = "I support the following commands:\r\n"

        for command in self.commands:
            response += command + "\r\n"

        return response
