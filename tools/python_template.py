#! /usr/bin/env python3

import argparse
import glob
import hashlib
import json
import random
import sys
import time
from datetime import datetime

import numpy as np

# import csv or pandas here


def xml_to_dict(element):
    """Convert XML element to dictionary"""
    result = {}
    
    # Handle text content
    if element.text and element.text.strip():
        if len(element) == 0:  # Leaf node
            return element.text.strip()
        result['text'] = element.text.strip()
    
    # Handle attributes
    if element.attrib:
        result.update(element.attrib)
    
    # Handle child elements
    for child in element:
        child_data = xml_to_dict(child)
        if child.tag in result:
            # If tag already exists, convert to list
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data
    
    return result


class Mapper:
    """mapper class"""

    def __init__(self):
        """initialization method"""
        self.load_reference_data()
        self.stat_pack = {}

    def map(self, raw_data):
        """primary mapping function"""
        json_list = []

        # place any filters needed here

        # place any calculations needed here

        # initialize
        json_obj = SenzingJson()
        json_obj.set_data_source("")  # supply a value for this data source
        json_obj.set_record_id(raw_data[""])  # supply a 100% unique attribute
        json_obj.set_record_type("")  # should be PERSON or ORGANIZATION

        # place column mappings here

        json_data = json_obj.render()
        self.capture_mapped_stats(json_data)
        json_list.append(json_data)

        return json_list

    def load_reference_data(self):
        """loading any conversion data needed"""
        self.variant_data = {}
        self.variant_data["GARBAGE_VALUES"] = ["NULL", "NUL", "N/A"]

    def clean_value(self, raw_value):
        """clean values from garbage data spacing issues etc"""
        if not raw_value:
            return ""
        new_value = " ".join(str(raw_value).strip().split())
        if new_value.upper() in self.variant_data["GARBAGE_VALUES"]:
            return ""
        return new_value

    def not_empty(self, _val):
        if _val is None:
            return False
        if isinstance(_val, (dict, list, np.ndarray)):
            return len(_val) > 0
        return len(str(_val)) > 0

    def compute_record_hash(self, target_dict, attr_list=None):
        """compute a hash to use for record_id if needed"""
        if attr_list:
            string_to_hash = ""
            for attr_name in sorted(attr_list):
                string_to_hash += (
                    " ".join(str(target_dict[attr_name]).split()).upper()
                    if attr_name in target_dict and target_dict[attr_name]
                    else ""
                ) + "|"
        else:
            string_to_hash = json.dumps(target_dict, sort_keys=True)
        return hashlib.md5(bytes(string_to_hash, "utf-8")).hexdigest()

    def ensure_list(self, _list):
        return _list if _list is not None else []

    def update_stat(self, cat1, cat2, example=None):
        """update stats for analysis"""

        if cat1 not in self.stat_pack:
            self.stat_pack[cat1] = {}
        if cat2 not in self.stat_pack[cat1]:
            self.stat_pack[cat1][cat2] = {}
            self.stat_pack[cat1][cat2]["count"] = 0

        self.stat_pack[cat1][cat2]["count"] += 1
        if example:
            if "examples" not in self.stat_pack[cat1][cat2]:
                self.stat_pack[cat1][cat2]["examples"] = []
            if example not in self.stat_pack[cat1][cat2]["examples"]:
                if len(self.stat_pack[cat1][cat2]["examples"]) < 5:
                    self.stat_pack[cat1][cat2]["examples"].append(example)
                else:
                    self.stat_pack[cat1][cat2]["examples"][random.randint(2, 4)] = example

    def capture_mapped_stats(self, json_data):
        """capture mapped stats"""
        data_source = json_data.get("DATA_SOURCE", "UNKNOWN_DSRC")
        for key1 in json_data:
            if isinstance(json_data[key1], list):
                for subrecord in json_data[key1]:
                    for key2 in subrecord:
                        self.update_stat(data_source, key2, subrecord[key2])
            else:
                self.update_stat(data_source, key1, json_data[key1])


class SenzingJson:
    """senzing json class"""

    def __init__(self):
        """initialization method"""
        self._json = {"DATA_SOURCE": "", "RECORD_ID": "", "RECORD_TYPE": ""}
        self.features = []
        self.payload = {}

    def set_data_source(self, _value):
        """set the data source"""
        if _value:
            self._json["DATA_SOURCE"] = _value

    def set_record_id(self, _value):
        """set the record_id"""
        self._json["RECORD_ID"] = _value

    def set_record_type(self, _value):
        """set the record_type"""
        if _value:
            self._json["RECORD_TYPE"] = _value

    def add_feature(self, _dict, **kwargs):
        """add a feature"""
        feature = {k: v for k, v in _dict.items() if self.not_empty(v)}
        if feature:
            self.features.append(feature)

    def add_payload(self, _dict):
        """add payload attributes"""
        for k, v in _dict.items():
            if self.not_empty(v):
                if k not in self.payload:
                    self.payload[k] = str(v)
                else:
                    self.payload[k] += " | " + str(v)

    def not_empty(self, _value):
        if _value is None:
            return False
        if isinstance(_value, (list, dict, np.ndarray)):
            return len(_value) > 0
        return len(str(_value).strip()) > 0

    def render(self):
        self._json["FEATURES"] = self.features
        self._json.update(self.payload)
        return self._json


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", dest="input_file", help="the name of the input file")
    parser.add_argument("-o", "--output_file", dest="output_file", help="the name of the output file")
    parser.add_argument("-l", "--log_file", dest="log_file", help="optional name of the statistics log file")
    args = parser.parse_args()

    if not args.input_file or not glob.glob(args.input_file):
        print("\nPlease supply a valid input file specification on the command line\n")
        sys.exit(1)
    file_list = glob.glob(args.input_file)

    if not args.output_file:
        print("\nPlease supply a valid output file name on the command line\n")
        sys.exit(1)

    output_file = open(args.output_file, "w", encoding="utf-8")

    proc_start_time = time.time()
    shut_down = False
    input_row_count = 0
    output_row_count = 0
    mapper = Mapper()

    try:
        file_num = 0
        for file_name in file_list:
            file_num += 1
            print(f"reading file {file_num} of {len(file_list)}: {file_name}")
            # open reader here
            for row in reader:
                for json_data in mapper.map(row):
                    output_file.write(json.dumps(json_data) + "\n")
                    output_row_count += 1

                input_row_count += 1
                if input_row_count % 10000 == 0:
                    print(f"{input_row_count} rows processed, {output_row_count} rows written")
            # close reader here

    except KeyboardInterrupt:
        print("\nUSER INTERUPT! Shutting down ... (please wait)\n")
        shut_down = True

    elapsed_mins = round((time.time() - proc_start_time) / 60, 1)
    run_status = ("completed in" if not shut_down else "aborted after") + f" {elapsed_mins} minutes"
    print(f"{input_row_count} rows processed, {output_row_count} rows written, {run_status}\n")

    output_file.close()

    # --write statistics file
    if args.log_file:
        with open(args.log_file, "w") as outfile:
            json.dump(mapper.stat_pack, outfile, indent=4, sort_keys=True)
        print("Mapping stats written to %s\n" % args.log_file)

    sys.exit(0)
