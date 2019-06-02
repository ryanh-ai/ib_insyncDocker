import os
import fileinput
from shutil import copyfile

CONFIG_FILE_TEMPLATE = 'config_template.ini'
CONFIG_FILE = 'config.ini'

def updateSecrets(templateFile=CONFIG_FILE_TEMPLATE, 
                  outputFile=CONFIG_FILE):
    if False:
        #Add AWS Secrets Manager Extract
        pass
    elif os.environ.get('IB_USER', False):
        userName = os.environ['IB_USER']
    else:
        raise Exception("ERROR: No IB Username Set")

    if False:
        #Add AWS Secrets Manager Extract
        pass
    elif os.environ.get('IB_PASSWORD', False):
        userPassword = os.environ['IB_PASSWORD']
    else:
        raise Exception("ERROR: No IB Password Set")

    copyfile(templateFile, outputFile) 

    with fileinput.FileInput(outputFile, inplace=True) as file:
        for line in file:
            line = line.replace('{ib_user}', userName)
            line = line.replace('{ib_password}', userPassword)
            print(line, end='')

    return outputFile
