#!/usr/bin/env python3
import logging
import dronecan
import os
import signal
import yaml
from functools import partial
from dronecan import uavcan

import argparse

_MAX_REQ_ERR_ = """Node Request Error:
Exide maximum number of attemp per parameter during requesting operation.
For more information launch with "--debug" flag"""


class Logger:
    def __init__(self, file : str, debug : bool) -> None:
        self.logger = logging.getLogger("ParamWriter")
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.ch = logging.StreamHandler()
        if debug:
            self.ch.setLevel(logging.DEBUG)
        else:
            self.ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.ch.setFormatter(formatter)
        self.logger.addHandler(self.ch)

    def writeInfo(self, msg : str) -> None:
        self.logger.info(msg)

    def writeDebug(self, msg : str) -> None:
        self.logger.debug(msg)
    
    def witeWarning(self, msg : str) -> None:
        self.logger.warning(msg)

    def writeError(self, msg : str) -> None:
        self.logger.error(msg)


class UNodeParamReader:
    def __init__(self, node, target_node_id : int, logger, max_request_number : int) -> None:
        self.node = node
        self.target_node_id = target_node_id
        self.logger = logger
        self.params = []
        self.isReadFinished = False
        self.max_request_number = max_request_number

    def _extract_value(self, value):
        """
        Given UAVCAN Value object, returns the value and its type
        """
        if   hasattr(value, 'boolean_value'): return (bool(value.boolean_value), bool)
        elif hasattr(value, 'integer_value'): return (int(value.integer_value), int)
        elif hasattr(value, 'real_value'):    return (float(value.real_value), float)
        elif hasattr(value, 'string_value'):  return (str(value.string_value), str)
        else:                                 return (None, None)

    def _handleErrorCase(self, attempt) -> None:
        if attempt == self.max_request_number:
            self.logger.writeError(_MAX_REQ_ERR_)
            self.isReadFinished = True
        else:
            self.logger.writeDebug(f"Cannot receive param with index {len(self.params)}. Starting {attempt+1} attempt")
            req_handler = partial(self._readNodeParams, attempt=attempt+1)
            req = uavcan.protocol.param.GetSet.Request(index=(len(self.params)))
            self.node.request(req, self.target_node_id, req_handler)

    def _parseNodeParam(self, msg) -> bool:
        param_type  = None
        param_value = None
        param_name  = "" 
        for field_name, field in dronecan.get_fields(msg.response).items():
            if field_name == "value":
                param_value, param_type = self._extract_value(msg.response.value)
            elif field_name == "name":
                    param_name = field.decode()
        
        if param_name != "":
            str1 = f"Received parameter \"{param_name}\""
            str2 = f" with index: {len(self.params)}"
            str3 = f" of type \"{param_type}\""
            str4 = f" with value \"{param_value}\""
            self.logger.writeDebug(f"{str1:<70}{str2:<20}{str3:<30}{str4}")

            self.params.append({
                "param_type":param_type, 
                "param_value" : param_value, 
                "param_name" : param_name}
            )
            return True
        return False

    def _readNodeParams(self, msg, attempt):
        if msg is None:
            self._handleErrorCase(attempt)

        if self._parseNodeParam(msg):
            req_handler = partial(self._readNodeParams, attempt=1)
            req = uavcan.protocol.param.GetSet.Request(index=(len(self.params)))
            self.node.request(req, self.target_node_id, req_handler)
        else:
            self.isReadFinished = True

    def readNodeParams(self) -> list:
        self.logger.writeDebug(f"Starting request to uNode with ID: {self.target_node_id}")
        req_handler = partial(self._readNodeParams, attempt=1)
        req = uavcan.protocol.param.GetSet.Request(index=0)
        self.node.request(req, self.target_node_id, req_handler)

        while not self.isReadFinished:
            self.node.spin(0.1)
        
        return self.params
    
class UNodeParamsYamlReader:
    def __init__(self, file_path : str, logger) -> None:
        self.file_path = file_path
        self.logger = logger
    
    def readYamlParameters(self) -> dict:
        self.logger.writeDebug("Starting yaml parameter reading")
        with open(os.path.abspath(self.file_path), "r") as stream:
            try:
                yaml_data = yaml.safe_load(stream)
                if not all(param in yaml_data.keys() for param in ["metadata", "params"]):
                    self.logger.writeError("Yaml file missing requred sections: 'metadata', 'params' ")
                    return {}
            except yaml.YAMLError as exc:
                self.logger.writeError(f"Error during reading yaml file: {self.file_path}\n{exc}")
                return {}
            self.logger.writeDebug("Yaml parameters read successfully")
            return yaml_data

class ParamsChecker:
    def __init__(self, logger, target_node_id : int, node_id_param_name : str) -> None:
        self.node_id_param_name = node_id_param_name
        self.logger = logger
        self.target_node_id = target_node_id
    
    def checkParameters(self, yaml_param_dict : dict, node_param_list : list) -> list:
        for param in node_param_list:
            if param["param_type"] == None or\
                param["param_value"] == None or\
                param["param_name"] == "" :
                raise ValueError("Error during parameter check. Received invallid parameters from node")
        
        node_param_dict = {}
        for param in node_param_list:
            node_param_dict[param["param_name"]] = param


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
        
        if self.node_id_param_name in params_to_update:
            raise ValueError(f"Error: uNode id mismach: given {self.target_node_id},"\
                            f" but settings for {yaml_param_dict[self.node_id_param_name]}{os.linesep}")
        
        if err_str != "":
            raise ValueError(err_str)
        
        return params_to_update
    
class UNodeParamWriter:
    def __init__(self, node, target_node_id : int, params_to_write : list, 
                 yaml_param_dict : dict, logger, max_request_number : int) -> None:
        self.node = node
        self.target_node_id = target_node_id
        self.params_to_write = params_to_write
        self.yaml_param_dict = yaml_param_dict
        self.logger = logger
        self.isWriteFinished = False
        self.max_request_number = max_request_number

    def _value_to_uavcan(self, value):
        """
        Given a value and its type, returns a UAVCAN Value object
        """
        if   type(value) == bool:  return uavcan.protocol.param.Value(boolean_value=bool(value))
        elif type(value) == int:   return uavcan.protocol.param.Value(integer_value=int(value))
        elif type(value) == float: return uavcan.protocol.param.Value(real_value=float(value))
        elif type(value) == str:   return uavcan.protocol.param.Value(string_value=str(value))
        else:                      return uavcan.protocol.param.Value()

    def _saveParams(self, event, attempt : int) -> None:
        if not event:
            if attempt == self.max_request_number: 
                self.logger.writeError(_MAX_REQ_ERR_)
                self.isWriteFinished = True
            else:
                self.logger.writeDebug(f"Error during saving uNode parameters, retryin...")
                req_handler = partial(self._saveParams, attempt=attempt+1)
                req = uavcan.protocol.param.ExecuteOpcode.Request()
                req.opcode = uavcan.protocol.param.ExecuteOpcode.Request().OPCODE_SAVE
                self.node.request(req, self.target_node_id, req_handler) 
            return
            
        self.logger.writeInfo("Written successfully")
        self.isWriteFinished = True

    def _handleErrorCase(self, event, curr_param_index : int, attempt : int) -> None:
        if attempt == self.max_request_number: 
            self.logger.writeError(_MAX_REQ_ERR_)
            self.isWriteFinished = True
        else:
            self.logger.writeDebug(f"Error during writing parameter {self.params_to_write[curr_param_index]}, retryin...")
            req_handler = partial(self._writeParams,  
                                  curr_param_index=curr_param_index,
                                  attempt=attempt+1)
            req = uavcan.protocol.param.GetSet.Request()
            req.name = self.params_to_write[curr_param_index]
            req.value = self._value_to_uavcan(self.yaml_param_dict[self.params_to_write[curr_param_index]])
            self.node.request(req, self.target_node_id, req_handler)

    def _writeParams(self, event, curr_param_index: int, attempt : int) -> None:
        if not event:
            self._handleErrorCase(event, curr_param_index, attempt)
            return
        
        if len(self.params_to_write)-1 == curr_param_index:
            self.logger.writeInfo("Saving parameters")
            req_handler = partial(self._saveParams, attempt=1)
            req = uavcan.protocol.param.ExecuteOpcode.Request()
            req.opcode = uavcan.protocol.param.ExecuteOpcode.Request().OPCODE_SAVE
            self.node.request(req, self.target_node_id, req_handler) 
            return
        
        self.logger.writeDebug(f"Value of parameter '{self.params_to_write[curr_param_index]}' is updated")
        req_handler = partial(self._writeParams,
                            curr_param_index = curr_param_index+1,
                            attempt=1)
        req = uavcan.protocol.param.GetSet.Request()
        req.name = self.params_to_write[curr_param_index+1]
        req.value = self._value_to_uavcan(self.yaml_param_dict[self.params_to_write[curr_param_index+1]])
        self.node.request(req, self.target_node_id, req_handler)


    def writeParams(self) -> None:
        debug_str = "Parameters requred to write: "
        for param in self.params_to_write:
            debug_str += f"{param}, "
        self.logger.writeDebug(debug_str)

        req_handler = partial(self._writeParams,
                            curr_param_index = 0,
                            attempt=1)
        req = uavcan.protocol.param.GetSet.Request()
        req.name = self.params_to_write[0]
        req.value = self._value_to_uavcan(self.yaml_param_dict[self.params_to_write[0]])
        self.node.request(req, self.target_node_id, req_handler)

        while not self.isWriteFinished:
            self.node.spin(0.1  )

class UNodeParamHandler:
    def __init__(self, target_node_id : int, max_request_number : int, 
                 logger, file_path : str, node_id_param_name : str, 
                 process_write : bool) -> None:
        self.target_node_id = target_node_id
        self.max_request_number = max_request_number
        self.logger = logger
        self.file_path = file_path
        self.node_id_param_name = node_id_param_name
        self.process_write = process_write

    def run(self, init_struct : dict)->None:
        node = dronecan.make_node(**init_struct)
        
        reader = UNodeParamReader(node, self.target_node_id, self.logger, self.max_request_number)
        uNode_params = reader.readNodeParams()

        yaml_reader = UNodeParamsYamlReader(self.file_path, self.logger)
        yaml_params = yaml_reader.readYamlParameters()
        if not yaml_params:
            return

        checker = ParamsChecker(self.logger, self.target_node_id, self.node_id_param_name)
        paramsToWrite = []
        try:
            paramsToWrite = checker.checkParameters(yaml_params["params"], uNode_params)
        except ValueError as err:
            self.logger.writeError("Error occured during comparing parameters on uNode and from yaml file:")
            self.logger.writeError(err.args[0])
            return  
        
        self.logger.writeInfo("Parameter check finished")
        if not paramsToWrite:
            self.logger.writeInfo("All parameters are valid")
        elif self.process_write:
            self.logger.writeInfo("Start writing parameters to node")
            writer = UNodeParamWriter(node, self.target_node_id, 
                                      paramsToWrite, yaml_params["params"],
                                      self.logger, self.max_request_number)
            writer.writeParams()
        else:
            msg = "\n    Following parameters required updating:\n"
            for param in paramsToWrite:
                msg += " "*8 + param + "\n"
            msg += "    To update parameters launch program with \"--write\" flag"
            self.logger.witeWarning(msg)

def main():
    parser = argparse.ArgumentParser(description='loop calling GetNodeInfo')
    parser.add_argument("--bitrate", default=1000000, type=int, help="CAN bit rate")
    parser.add_argument("--node-id", default=100, type=int, help="CAN node ID")
    parser.add_argument("--target-node-id", default=49, type=int, help="target CAN node ID")
    parser.add_argument("--max-req-number", default=10, type=int, help="Maximum number of attempt for performing operation")
    parser.add_argument("--device", default="slcan0", type=str, help="Can device")
    parser.add_argument("--id-param-name", default="uavcan.node_id", type=str, help="uNode id parameter name")
    parser.add_argument("--bustype", default="socketcan", type=str, help="Bustype")
    parser.add_argument("--rate", default=1, type=float, help="request rate")
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction)
    parser.add_argument('--write', action=argparse.BooleanOptionalAction)
    parser.add_argument('--file-path', default="../tests/params_example.yaml", type=str, help="Path to yaml file with parameter settings")
    args = parser.parse_args()

    logger = Logger("", args.debug)
    handler = UNodeParamHandler(args.target_node_id, args.max_req_number, 
                                logger, args.file_path, args.id_param_name,
                                args.write)
    
    init_struct = {"can_device_name" : args.device,
          "bustype" : args.bustype,
          "bitrate" : args.bitrate,
          "node_id" : args.node_id}
    handler.run(init_struct)


if __name__ =="__main__":
    main()