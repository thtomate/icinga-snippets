#!/usr/bin/env python3
import argparse
from pysnmp.error import PySnmpError
from pysnmp.hlapi import *

# This script monitors optical power levels using SNMP.
# 1. get instanceID where 1.3.6.1.2.1.47.1.1.1.1.3 is 1.3.6.1.4.1.9.12.3.1.8.47 or 1.3.6.1.4.1.9.12.3.1.8.46
# 2. get 1.3.6.1.2.1.47.1.1.1.1.7.instanceID and 1.3.6.1.4.1.9.9.91.1.1.1.1.2/3/4.instanceID 

# Parse command-line arguments
parser = argparse.ArgumentParser(description="SNMP Optical Power Monitoring")
parser.add_argument("--host", help="Hostname or IP address of the SNMP target")
args = parser.parse_args()

community = 'public'
host = args.host

target_oids = [
    '1.3.6.1.4.1.9.12.3.1.8.47',
    '1.3.6.1.4.1.9.12.3.1.8.46'
]

string = ""
exitCode = 0
metrics = {}

try:
    try:
        transporttarget = Udp6TransportTarget((host, 161))
    except PySnmpError:
        transporttarget = UdpTransportTarget((host, 161))
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        transporttarget,
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.47.1.1.1.1.3')),
        lexicographicMode=False
    )


    instance_ids = []
    for errorIndication, errorStatus, errorIndex, varBinds in iterator: 
        if errorIndication:
            string += f"Error: {errorIndication}\n"
            exitCode = 3
            break
        elif errorStatus:
            string += f"Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}\n"
            exitCode = 3
            break
        else:
            for varBind in varBinds:
                if str(varBind[1]).strip() in target_oids:
                    # Collect instance IDs for the specified OIDs
                    instance_ids.append(str(varBind[0].getOid())[25:])

    # Iterate over the collected instance IDs
    for instance_id in instance_ids:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),
            transporttarget,
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.47.1.1.1.1.7.' + instance_id)),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.91.1.1.1.1.4.' + instance_id)),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.91.1.1.1.1.2.' + instance_id)),  # scale
            ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.91.1.1.1.1.3.' + instance_id))  # precision
        )

        for errorIndication, errorStatus, errorIndex, varBinds in iterator:
            if errorIndication:
                string += f"Error: {errorIndication}\n"
                exitCode = 3
                break
            elif errorStatus:
                string += f"Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}\n"
                exitCode = 3
                break
            else:
                # "Get" interface name
                key = str(varBinds[0][1]).replace('Power', '').replace('Sensor', '').replace(' Transceiver', '').replace('Lane 1', '').strip().replace(' ', '_')
                # Convert to dBm, I made this up as Nexus and Catalyst differ here
                value = float(varBinds[1][1]) * 10.0**(int(varBinds[2][1])+int(varBinds[3][1])-11 if varBinds[2][1] else 0)
                # Hardcorded for now, sry
                if value < -9.5:
                    string += f"Warning: {key} is below threshold: {value:.1f}\n"
                    exitCode = 1
                metrics[key] = value

except Exception as e:
    string += f"Exception occurred: {str(e)}\n"
    if exitCode == 0:
        exitCode = 3

if string == "" and exitCode == 0:
    string += "Optical values okay"


if len(metrics) == 0:
    string += "No values found\n"
else:
    string += " | "
    for key, value in metrics.items():
        string += f"{key}={value:.1f} "

print(string)
exit(exitCode)
