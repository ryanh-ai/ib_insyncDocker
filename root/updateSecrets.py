import os
import fileinput
from shutil import copyfile
import boto3
import ssm_parameter_store as ssm

CONFIG_FILE_TEMPLATE = 'config_template.ini'
CONFIG_FILE = 'config.ini'

def updateSecrets(templateFile=CONFIG_FILE_TEMPLATE, 
                  outputFile=CONFIG_FILE,
                  secretsPath='/ibc/paper/'):

    store = ssm.EC2ParameterStore()
    secrets = store.get_parameters_with_hierarchy(secretsPath)

    if secrets.get('TWS_USER', False):
        userName = secrets['TWS_USER']
    elif os.environ.get('TWS_USER', False):
        userName = os.environ['TWS_USER']
    else:
        raise Exception("ERROR: No IB Username Set")

    if secrets.get('TWS_PASSWORD', False):
        userPassword = secrets['TWS_PASSWORD']
    elif os.environ.get('TWS_PASSWORD', False):
        userPassword = os.environ['TWS_PASSWORD']
    else:
        raise Exception("ERROR: No IB Password Set")

    copyfile(templateFile, outputFile) 

    with fileinput.FileInput(outputFile, inplace=True) as file:
        for line in file:
            line = line.replace('{ib_user}', userName)
            line = line.replace('{ib_password}', userPassword)
            print(line, end='')

    return outputFile
