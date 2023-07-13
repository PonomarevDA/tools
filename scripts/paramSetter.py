import dronecan
import os
import signal
import yaml
from functools import partial
from dronecan import uavcan

DEBUG              = True
MAX_REQUEST_TIMES  = 10
NODE_ID_PARAM_NAME = "uavcan.node_id"

Termination = False
def handler(signum, frame):
    global Termination
    print("\nReceived interrupt signal (Ctrl^C). Stopped...")
    Termination = True

signal.signal(signal.SIGINT, handler)

import argparse
from argparse import ArgumentParser
parser = ArgumentParser(description='loop calling GetNodeInfo')
parser.add_argument("--bitrate", default=1000000, type=int, help="CAN bit rate")
parser.add_argument("--node-id", default=100, type=int, help="CAN node ID")
parser.add_argument("--target-node-id", default=49, type=int, help="target CAN node ID")
parser.add_argument("--device", default="slcan0", type=str, help="Can device")
parser.add_argument("--bustype", default="socketcan", type=str, help="Bustype")
parser.add_argument("--rate", default=1, type=float, help="request rate")
parser.add_argument("--canfd", default=False, action="store_true", help="send as CANFD")
parser.add_argument('--debug', action=argparse.BooleanOptionalAction)
parser.add_argument('--write', action=argparse.BooleanOptionalAction)
parser.add_argument('--file-path', default="./tools/tests/params_example.yaml", type=str, help="Path to yaml file with parameter settings")
args = parser.parse_args()


def print_max_attempt_error():
    err_str = """Node Request Error:
    Exide maximum number of attemp per parameter during requesting operation.
    For more information launch with "--debug" flag"""
    print(err_str)


def extract_value(value):
    """
    Given UAVCAN Value object, returns the value and its type
    """
    if   hasattr(value, 'boolean_value'): return (bool(value.boolean_value), bool)
    elif hasattr(value, 'integer_value'): return (int(value.integer_value), int)
    elif hasattr(value, 'real_value'):    return (float(value.real_value), float)
    elif hasattr(value, 'string_value'):  return (str(value.string_value), str)
    else:                                 return (None, None)

def value_to_uavcan(value):
    """
    Given a value and its type, returns a UAVCAN Value object
    """
    if   type(value) == bool:  return uavcan.protocol.param.Value(boolean_value=bool(value))
    elif type(value) == int:   return uavcan.protocol.param.Value(integer_value=int(value))
    elif type(value) == float: return uavcan.protocol.param.Value(real_value=float(value))
    elif type(value) == str:   return uavcan.protocol.param.Value(string_value=str(value))
    else:                      return uavcan.protocol.param.Value()


def writeHandler(event, node, params_to_write, yaml_param_dict, curr_param_index, attempt):
    global Termination
    if not event:
        if attempt == MAX_REQUEST_TIMES: 
            print_max_attempt_error()
            Termination = True
        else:
            if args.debug: print(f"Error during writing parameter {params_to_write[curr_param_index]}, retryin...")
            req_handler = partial(writeHandler, 
                                  node=node,
                                  params_to_write=params_to_write, 
                                  yaml_param_dict=yaml_param_dict, 
                                  curr_param_index=curr_param_index,
                                  attempt=attempt+1)
            req = uavcan.protocol.param.GetSet.Request()
            req.name = params_to_write[curr_param_index]
            req.value = value_to_uavcan(yaml_param_dict[params_to_write[curr_param_index]])
            node.request(req, args.target_node_id, req_handler, canfd=args.canfd)
        return
    
    if len(params_to_write)-1 == curr_param_index:
        print("Written successfully")
        Termination = True 
        return
    
    req_handler = partial(writeHandler, 
                          node=node,
                          params_to_write=params_to_write, 
                          yaml_param_dict=yaml_param_dict, 
                          curr_param_index = curr_param_index+1,
                          attempt=1)
    req = uavcan.protocol.param.GetSet.Request()
    req.name = params_to_write[curr_param_index+1]
    req.value = value_to_uavcan(yaml_param_dict[params_to_write[curr_param_index+1]])
    node.request(req, args.target_node_id, req_handler, canfd=args.canfd)


def writeParams(node, params_to_write, yaml_param_dict):
    if args.debug:
        print("    Parameters requred to write: ")
        for param in params_to_write:
            print(" "*8 + f"{param}")
        print()

    req_handler = partial(writeHandler, 
                          node=node,
                          params_to_write=params_to_write, 
                          yaml_param_dict=yaml_param_dict, 
                          curr_param_index = 0,
                          attempt=1)
    req = uavcan.protocol.param.GetSet.Request()
    req.name = params_to_write[0]
    req.value = value_to_uavcan(yaml_param_dict[params_to_write[0]])
    node.request(req, args.target_node_id, req_handler, canfd=args.canfd)


def checkAndCompareParams(yaml_param_dict, node_param_dict):
    param_mismach = []        #  list of parameter names
    param_type_mismach = []   #  list of tuples: ("parmeter_name", <expected_type>)
    params_to_update = []     #  list of parameter names
    for param_name in yaml_param_dict.keys():
        if not param_name in node_param_dict:
            param_mismach.append(param_name)
        elif type(yaml_param_dict[param_name]) != node_param_dict[param_name]["param_type"]:
            param_type_mismach.append((param_name, node_param_dict[param_name]["param_type"]))
        elif yaml_param_dict[param_name] != node_param_dict[param_name]["param_value"]:
            params_to_update.append(param_name)


    err_str = ""
    if param_mismach:
        for pararm in param_mismach:
            err_str += f"Parameter {pararm} are not present on uNode{os.linesep}"
    
    if param_type_mismach:
        for param in param_type_mismach:
            err_str += f"Parameter {param[0]} has type mismach with parameter in uNode: expected type \"{param[1]}\"{os.linesep}"
    
    if NODE_ID_PARAM_NAME in params_to_update:
        raise ValueError(f"Error: uNode id mismach: given {args.target_node_id},"\
                         f" but settings for {yaml_param_dict[NODE_ID_PARAM_NAME]}{os.linesep}")
    
    if err_str != "":
        raise ValueError(err_str)
    
    return params_to_update


def readYamlAndWrite(node, paramList):
    global Termination
    for param in paramList:
        if param["param_type"] == None or\
            param["param_value"] == None or\
            param["param_name"] == "" :
            print("Error during parameter check. Received invallid parameters from node")
            Termination = True
            return
        
    #  Build parameters Dict for faster acces to parameters by name
    param_dict = {}
    for param in paramList:
        param_dict[param["param_name"]] = param
        
    if args.debug:
        print(f"Parameters read finised successfully. Read {len(paramList)} parameters")


    with open(os.path.abspath(args.file_path), "r") as stream:
        try:
            yaml_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"Error during reading yaml file: {args.file_path}\n{exc}")

    paramsToWrite = []
    try:
        paramsToWrite = checkAndCompareParams(yaml_data["params"], param_dict)
    except ValueError as err:
        print("Error occured during comparing parameters on uNode and from yaml file:")
        print(err.args[0])
        Termination = True
        return

    print("Parameter check finished:")
    if not paramsToWrite:
        print("    All parameters are valid")
    elif args.write:
        print("    Writing...")
        writeParams(node, paramsToWrite, yaml_data["params"])
    else:
        msg = "    Following parameters required updating:\n"
        for param in paramsToWrite:
            msg += " "*8 + param + "\n"
        msg += "    To update parameters launch program with \"--write\" flag"
        print(msg)

    Termination = True
        

def getNameResponceHandler(msg, paramList, node, attempt):
    global Termination
    if msg is None:
        if attempt == MAX_REQUEST_TIMES:
            print_max_attempt_error()
            Termination = True
            return
        else:
            if args.debug:
                print(f"Cannot receive param with index {len(paramList)}. Starting {attempt+1} attempt")
            req_handler = partial(getNameResponceHandler, paramList=paramList, node=node, attempt=attempt+1)
            req = uavcan.protocol.param.GetSet.Request(index=(len(paramList)))
            node.request(req, args.target_node_id, req_handler, canfd=args.canfd)
            return

    param_type  = None
    param_value = None
    param_name  = "" 
    for field_name, field in dronecan.get_fields(msg.response).items():
        if field_name == "value":
            param_value, param_type = extract_value(msg.response.value)
        elif field_name == "name":
                param_name = field.decode()

        
    if param_name != "":
        if args.debug:
            str1 = f"Debug> Received parameter \"{param_name}\""
            str2 = f" with index: {len(paramList)}"
            str3 = f" of type \"{param_type}\""
            str4 = f" with value \"{param_value}\""
            print(f"{str1:<70}{str2:<20}{str3:<30}{str4}")
        paramList.append({
            "param_type":param_type, 
            "param_value" : param_value, 
            "param_name" : param_name})
        req_handler = partial(getNameResponceHandler, paramList=paramList, node=node, attempt=1)
        req = uavcan.protocol.param.GetSet.Request(index=(len(paramList)))
        node.request(req, args.target_node_id, req_handler, canfd=args.canfd)
    else:
        readYamlAndWrite(node, paramList)


def readExistingParameters(node, paramList):
    if args.debug:
        print(f"Starting request to uNode with ID: {args.target_node_id}{os.linesep}")

    req_handler = partial(getNameResponceHandler, paramList=paramList, node=node, attempt=1)
    req = uavcan.protocol.param.GetSet.Request(index=0)
    node.request(req, args.target_node_id, req_handler, canfd=args.canfd)
   

def doSomeLogic(node):
    #  List of parameters that exists in node
    paramList = []
    readExistingParameters(node, paramList)
    

def main():
    init_struct = {"can_device_name" : args.device,
          "bustype" : args.bustype,
          "bitrate" : args.bitrate,
          "node_id" : args.node_id}
    
    node = dronecan.make_node(**init_struct)
    doSomeLogic(node)

    while not Termination:
        try:
            node.spin(0.1)            # Spin for 1 second or until an exception is thrown
        except dronecan.UAVCANException as ex:
            print('Node error:', ex)


if __name__ =="__main__":
    main()