#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023 Dmitry Ponomarev.
# Author: CyberTDan
import os
import argparse
import logging
from functools import partial
import yaml
import dronecan
# pylint: disable=no-name-in-module
from dronecan import uavcan


_MAX_REQ_ERR_ = """Node Request Error:
Exide maximum number of attemp per parameter during requesting operation.
For more information launch with "--debug" flag"""


class Logger:
    def __init__(self, debug : bool) -> None:
        self.logger = logging.getLogger("ParamsWriter")
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.stream_handler = logging.StreamHandler()
        if debug:
            self.stream_handler.setLevel(logging.DEBUG)
        else:
            self.stream_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.stream_handler.setFormatter(formatter)
        self.logger.addHandler(self.stream_handler)

    def write_info(self, msg : str) -> None:
        self.logger.info(msg)

    def write_debug(self, msg : str) -> None:
        self.logger.debug(msg)

    def write_warning(self, msg : str) -> None:
        self.logger.warning(msg)

    def write_error(self, msg : str) -> None:
        self.logger.error(msg)


class ParamsReader:
    def __init__(self, node, target_node_id : int, logger, max_request_number : int) -> None:
        self.node = node
        self.target_node_id = target_node_id
        self.logger = logger
        self.params = []
        self.is_read_finished = False
        self.max_request_number = max_request_number

    def read_node_params(self) -> list:
        self.logger.write_debug(f"Starting request to uNode with ID: {self.target_node_id}")
        req_handler = partial(self._read_node_params, attempt=1)
        req = uavcan.protocol.param.GetSet.Request(index=0)
        self.node.request(req, self.target_node_id, req_handler)

        while not self.is_read_finished:
            self.node.spin(0.1)

        return self.params

    @staticmethod
    def _extract_value(value):
        """
        Given UAVCAN Value object, returns the value and its type
        """
        if hasattr(value, 'boolean_value'):
            return (bool(value.boolean_value), bool)
        if hasattr(value, 'integer_value'):
            return (int(value.integer_value), int)
        if hasattr(value, 'real_value'):
            return (float(value.real_value), float)
        if hasattr(value, 'string_value'):
            return (str(value.string_value), str)
        return (None, None)

    def _handle_error(self, attempt) -> None:
        if attempt == self.max_request_number:
            self.logger.write_error(_MAX_REQ_ERR_)
            self.is_read_finished = True
        else:
            self.logger.write_debug(f"Cannot receive param with index {len(self.params)}. Starting {attempt+1} attempt")
            req_handler = partial(self._read_node_params, attempt=attempt+1)
            req = uavcan.protocol.param.GetSet.Request(index=(len(self.params)))
            self.node.request(req, self.target_node_id, req_handler)

    def _parse_node_param(self, msg) -> bool:
        param_type = None
        param_value = None
        param_name = ""
        for field_name, field in dronecan.get_fields(msg.response).items():
            if field_name == "value":
                param_value, param_type = ParamsReader._extract_value(msg.response.value)
            elif field_name == "name":
                param_name = field.decode()

        if param_name != "":
            str1 = f"Received parameter \"{param_name}\""
            str2 = f" with index: {len(self.params)}"
            str3 = f" of type \"{param_type}\""
            str4 = f" with value \"{param_value}\""
            self.logger.write_debug(f"{str1:<70}{str2:<20}{str3:<30}{str4}")

            self.params.append({
                "param_type" : param_type,
                "param_value" : param_value,
                "param_name" : param_name}
            )
            return True
        return False

    def _read_node_params(self, msg, attempt):
        if msg is None:
            self._handle_error(attempt)

        if self._parse_node_param(msg):
            req_handler = partial(self._read_node_params, attempt=1)
            req = uavcan.protocol.param.GetSet.Request(index=(len(self.params)))
            self.node.request(req, self.target_node_id, req_handler)
        else:
            self.is_read_finished = True

class YamlParamsReader:
    def __init__(self, file_path : str, logger) -> None:
        self.file_path = file_path
        self.logger = logger

    def read_yaml_parameters(self) -> dict:
        self.logger.write_debug("Starting yaml parameter reading")
        with open(os.path.abspath(self.file_path), "r", encoding='UTF-8') as stream:
            try:
                yaml_data = yaml.safe_load(stream)
                if not all(param in yaml_data.keys() for param in ["metadata", "params"]):
                    self.logger.write_error("Yaml file missing requred sections: 'metadata', 'params' ")
                    return {}
            except yaml.YAMLError as exc:
                self.logger.write_error(f"Error during reading yaml file: {self.file_path}\n{exc}")
                return {}
            self.logger.write_debug("Yaml parameters read successfully")
            return yaml_data

class ParamsChecker:
    def __init__(self, logger, target_node_id : int, node_id_param_name : str) -> None:
        self.node_id_param_name = node_id_param_name
        self.logger = logger
        self.target_node_id = target_node_id

    def check_parameters(self, yaml_param_dict : dict, node_param_list : list) -> list:
        for param in node_param_list:
            if param["param_type"] is None or \
                param["param_value"] is None or \
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

        if err_str != "":
            raise ValueError(err_str)

        return params_to_update

class ParamsWriter:
    def __init__(self, node, target_node_id : int, params_to_write : list,
                 yaml_param_dict : dict, logger, max_request_number : int) -> None:
        self.node = node
        self.target_node_id = target_node_id
        self.params_to_write = params_to_write
        self.yaml_param_dict = yaml_param_dict
        self.logger = logger
        self.is_write_finished = False
        self.max_request_number = max_request_number

    def write_params(self) -> None:
        debug_str = "Parameters requred to write: "
        for param in self.params_to_write:
            debug_str += f"{param}, "
        self.logger.write_debug(debug_str)

        req_handler = partial(self._write_params,
                            curr_param_index = 0,
                            attempt=1)
        req = uavcan.protocol.param.GetSet.Request()
        req.name = self.params_to_write[0]
        req.value = ParamsWriter._value_to_uavcan(self.yaml_param_dict[self.params_to_write[0]])
        self.node.request(req, self.target_node_id, req_handler)

        while not self.is_write_finished:
            self.node.spin(0.1)

    @staticmethod
    def _value_to_uavcan(value):
        """
        Given a value and its type, returns a UAVCAN Value object
        """
        if type(value) == bool:
            return uavcan.protocol.param.Value(boolean_value=bool(value))
        if type(value) == int:
            return uavcan.protocol.param.Value(integer_value=int(value))
        if type(value) == float:
            return uavcan.protocol.param.Value(real_value=float(value))
        if type(value) == str:
            return uavcan.protocol.param.Value(string_value=str(value))
        return uavcan.protocol.param.Value()

    def _save_params(self, event, attempt : int) -> None:
        if not event:
            if attempt == self.max_request_number:
                self.logger.write_error(_MAX_REQ_ERR_)
                self.is_write_finished = True
            else:
                self.logger.write_debug("Error during saving parameters, retrying...")
                req_handler = partial(self._save_params, attempt=attempt+1)
                req = uavcan.protocol.param.ExecuteOpcode.Request()
                req.opcode = uavcan.protocol.param.ExecuteOpcode.Request().OPCODE_SAVE
                self.node.request(req, self.target_node_id, req_handler)
            return

        self.logger.write_info("Written successfully")
        self.is_write_finished = True

    def _handle_error(self, curr_param_index : int, attempt : int) -> None:
        if attempt == self.max_request_number:
            self.logger.write_error(_MAX_REQ_ERR_)
            self.is_write_finished = True
        else:
            self.logger.write_debug(f"Error during writing parameter {self.params_to_write[curr_param_index]}, retryin...")
            req_handler = partial(self._write_params,
                                  curr_param_index=curr_param_index,
                                  attempt=attempt+1)
            req = uavcan.protocol.param.GetSet.Request()
            req.name = self.params_to_write[curr_param_index]
            req.value = ParamsWriter._value_to_uavcan(self.yaml_param_dict[self.params_to_write[curr_param_index]])
            self.node.request(req, self.target_node_id, req_handler)

    def _write_params(self, event, curr_param_index: int, attempt : int) -> None:
        if not event:
            self._handle_error(curr_param_index, attempt)
            return

        if len(self.params_to_write)-1 == curr_param_index:
            self.logger.write_info("Saving parameters")
            req_handler = partial(self._save_params, attempt=1)
            req = uavcan.protocol.param.ExecuteOpcode.Request()
            req.opcode = uavcan.protocol.param.ExecuteOpcode.Request().OPCODE_SAVE
            self.node.request(req, self.target_node_id, req_handler)
            return

        self.logger.write_debug(f"Value of parameter '{self.params_to_write[curr_param_index]}' is updated")
        req_handler = partial(self._write_params,
                            curr_param_index = curr_param_index+1,
                            attempt=1)
        req = uavcan.protocol.param.GetSet.Request()
        req.name = self.params_to_write[curr_param_index+1]
        req.value = ParamsWriter._value_to_uavcan(self.yaml_param_dict[self.params_to_write[curr_param_index+1]])
        self.node.request(req, self.target_node_id, req_handler)

class NodeMonitor:
    def __init__(self, node) -> None:
        self.node = node
        self.nodes = set()
        self.node.add_handler(uavcan.protocol.NodeStatus, self.node_status_callback)

    def node_status_callback(self, msg):
        # Typically, 127 corresponds to gui_tool, so skip it
        if msg.transfer.source_node_id != 127:
            self.nodes.add(msg.transfer.source_node_id)

    def wait_for_a_single_node(self):
        self.node.spin(1.5)
        return next(iter(self.nodes)) if len(self.nodes) == 1 else None

class ParamsHandler:
    def __init__(self, target_node_id : int, max_request_number : int,
                 logger, file_path : str, node_id_param_name : str,
                 process_write : bool) -> None:
        self.target_node_id = target_node_id
        self.max_request_number = max_request_number
        self.logger = logger
        self.file_path = file_path
        self.node_id_param_name = node_id_param_name
        self.process_write = process_write

    def run(self, init_struct : dict) -> None:
        node = dronecan.make_node(**init_struct)

        if self.target_node_id > 127:
            node_monitor = NodeMonitor(node)
            self.target_node_id = node_monitor.wait_for_a_single_node()
            if self.target_node_id is None:
                self.logger.write_error("Either there is no any online node or there are few of them!")
                return

        reader = ParamsReader(node, self.target_node_id, self.logger, self.max_request_number)
        node_params = reader.read_node_params()

        yaml_reader = YamlParamsReader(self.file_path, self.logger)
        yaml_params = yaml_reader.read_yaml_parameters()
        if not yaml_params:
            return

        checker = ParamsChecker(self.logger, self.target_node_id, self.node_id_param_name)
        params_to_write = []
        try:
            params_to_write = checker.check_parameters(yaml_params["params"], node_params)
        except ValueError as err:
            self.logger.write_error("Error occured during comparing parameters on node and from yaml file:")
            self.logger.write_error(err.args[0])
            return

        self.logger.write_info("Parameter check finished")
        if not params_to_write:
            self.logger.write_info("All parameters are valid")
        elif self.process_write:
            self.logger.write_info("Start writing parameters to node")
            writer = ParamsWriter(node, self.target_node_id,
                                  params_to_write, yaml_params["params"],
                                  self.logger, self.max_request_number)
            writer.write_params()
        else:
            msg = "\n    Following parameters required updating:\n"
            for param in params_to_write:
                msg += " "*8 + param + "\n"
            msg += "    To update parameters launch program with \"--write\" flag"
            self.logger.write_warning(msg)

def main():
    parser = argparse.ArgumentParser(description='loop calling GetNodeInfo')
    parser.add_argument("--bitrate", default=1000000, type=int, help="CAN bit rate")
    parser.add_argument("--node-id", default=100, type=int, help="CAN node ID")
    parser.add_argument("--target-node-id", default=255, type=int, help="target CAN node ID")
    parser.add_argument("--max-req-number", default=10, type=int, help="Maximum number of attempt for performing operation")
    parser.add_argument("--device", default="slcan0", type=str, help="Can device")
    parser.add_argument("--id-param-name", default="uavcan.node_id", type=str, help="uNode id parameter name")
    parser.add_argument("--bustype", default="socketcan", type=str, help="Bustype")
    parser.add_argument("--rate", default=1, type=float, help="request rate")
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction)
    parser.add_argument('--write', action=argparse.BooleanOptionalAction)
    parser.add_argument('--file-path', default="../tests/params_example.yaml", type=str, help="Path to yaml file with parameter settings")
    args = parser.parse_args()

    logger = Logger(args.debug)
    handler = ParamsHandler(args.target_node_id, args.max_req_number,
                            logger, args.file_path, args.id_param_name,
                            args.write)

    init_struct = {"can_device_name" : args.device,
          "bustype" : args.bustype,
          "bitrate" : args.bitrate,
          "node_id" : args.node_id}
    handler.run(init_struct)


if __name__ =="__main__":
    main()
