#! /usr/bin/env python3

import argparse
import csv
import glob
import hashlib
import json
import random
import sys
import time
from datetime import datetime

import numpy as np


class Mapper:
    """mapper class"""

    def __init__(self):
        """initialization method"""
        self.load_reference_data()
        self.stat_pack = {}
        self.employer_cache = {}

    def map(self, raw_data):
        """primary mapping function"""
        self.json_list = []

        # place any filters needed here

        # place any calculations needed here

        # initialize
        json_obj = SenzingJson()
        json_obj.set_data_source("EMPLOYEE")  # supply a value for this data source
        json_obj.set_record_id(raw_data["emp_num"])  # supply a 100% unique attribute
        json_obj.set_record_type("PERSON")  # should be PERSON or ORGANIZATION

        json_obj.add_feature({"REL_ANCHOR_DOMAIN": "EMPLOYEE", "REL_ANCHOR_KEY": raw_data["emp_num"]})

        json_obj.add_feature(
            {
                "NAME_LAST": raw_data["last_name"],
                "NAME_FIRST": raw_data["first_name"],
                "NAME_MIDDLE": raw_data["middle_name"],
            }
        )

        json_obj.add_feature(
            {
                "ADDR_LINE1": raw_data["addr1"],
                "ADDR_CITY": raw_data["city"],
                "ADDR_STATE": raw_data["state"],
                "ADDR_POSTAL_CODE": raw_data["zip"],
            }
        )

        json_obj.add_feature({"PHONE_TYPE": "HOME", "PHONE_NUMBER": raw_data["home_phone"]})
        json_obj.add_feature({"DATE_OF_BIRTH": raw_data["dob"]})
        json_obj.add_feature({"SSN_NUMBER": raw_data["ssn"]})

        json_obj.add_payload({"job_category": raw_data["job_category"]})
        json_obj.add_payload({"job_title": raw_data["job_title"]})
        json_obj.add_payload({"hire_date": raw_data["hire_date"]})

        if self.not_empty(raw_data["id_number"]):
            id_type = raw_data["id_type"].upper()
            id_number = raw_data["id_number"]
            id_country = raw_data["id_country"]
            if id_type == "DL":
                json_obj.add_feature({"DRIVERS_LICENSE_NUMBER": id_number, "DRIVERS_LICENSE_STATE": id_country})
            elif id_type == "PP":
                json_obj.add_feature({"PASSPORT_NUMBER": id_number, "PASSPORT_COUNTRY": id_country})
            else:
                json_obj.add_feature(
                    {
                        "OTHER_ID_TYPE": id_type,
                        "OTHER_ID_NUMBER": id_number,
                        "OTHER_ID_COUNTRY": id_country,
                    }
                )

        if self.not_empty(raw_data["sherrifs_card"]):
            for card in raw_data["sherrifs_card"].split(","):
                json_obj.add_feature(
                    {
                        "OTHER_ID_TYPE": "SHERRIFS_CARD",
                        "OTHER_ID_NUMBER": card,
                    }
                )

        if self.not_empty(raw_data["manager_id"]):
            json_obj.add_feature(
                {
                    "REL_POINTER_DOMAIN": "EMPLOYEE",
                    "REL_POINTER_KEY": raw_data["manager_id"],
                    "REL_POINTER_ROLE": "REPORTS_TO",
                }
            )

        if self.not_empty(raw_data["employer_name"]):
            json_obj.add_feature({"EMPLOYER_NAME": raw_data["employer_name"]})
            employer_id = self.map_employer(raw_data)
            json_obj.add_feature(
                {
                    "REL_POINTER_DOMAIN": "EMPLOYER",
                    "REL_POINTER_KEY": employer_id,
                    "REL_POINTER_ROLE": "EMPLOYED_BY",
                }
            )


        json_data = json_obj.render()
        self.capture_mapped_stats(json_data)
        self.json_list.append(json_data)

        return self.json_list

    def map_employer(self, raw_data):
        """map the employer if haven't yet"""
        employer_features = {"employer_name": raw_data["employer_name"], "employer_addr": raw_data["employer_addr"]}
        employer_id = self.compute_record_hash(employer_features)
        if employer_id not in self.employer_cache:
            self.employer_cache[employer_id] = True
            json_obj2 = SenzingJson()
            json_obj2.set_data_source("EMPLOYER")  # supply a value for this data source
            json_obj2.set_record_id(employer_id)  # supply a 100% unique attribute
            json_obj2.set_record_type("ORGANIZATION")  # should be PERSON or ORGANIZATION
            json_obj2.add_feature({"REL_ANCHOR_DOMAIN": "EMPLOYER", "REL_ANCHOR_KEY": employer_id})
            json_obj2.add_feature({"NAME_ORG": raw_data["employer_name"]})
            json_obj2.add_feature({"ADDR_TYPE": "BUSINESS", "ADDR_FULL": raw_data["employer_addr"]})

            json_data = json_obj2.render()
            self.capture_mapped_stats(json_data)
            self.json_list.append(json_data)
        return employer_id

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
    parser.add_argument("input_file", help="the name of the input file")
    parser.add_argument("-o", "--output_file", help="the name of the output file")
    parser.add_argument("-l", "--log_file", help="optional name of the statistics log file")
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
            input_file = open(file_name, "r", encoding="utf-8")
            csv_dialect = csv.Sniffer().sniff(input_file.read(2048), delimiters=[",", ";", "|", "	"])
            input_file.seek(0)
            reader = csv.DictReader(input_file, dialect=csv_dialect)
            for row in reader:
                for json_data in mapper.map(row):
                    output_file.write(json.dumps(json_data) + "\n")
                    output_row_count += 1

                input_row_count += 1
                if input_row_count % 10000 == 0:
                    print(f"{input_row_count} rows processed, {output_row_count} rows written")
            input_file.close()

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
