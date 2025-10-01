#! /usr/bin/env python3
import argparse
import configparser
import csv
import glob
import json
import os
import pathlib
import subprocess
import sys
import time
import xml.etree.ElementTree as ET  # Add import for XML parsing
from datetime import date, datetime, timedelta
from typing import Iterable, Iterator

import numpy as np

try:
    import pandas as pd
except:
    pd = False

try:
    import prettytable
except:
    prettytable = False


class JsonReader(Iterable):
    def __init__(self, iterable: Iterator):
        self.iterable = iterable
        self._iterator = None

    def __iter__(self) -> Iterator:
        self._iterator = iter(self.iterable)
        return self

    def __next__(self):
        return json.loads(next(self._iterator))


class Node(object):

    def __init__(self, node_id):
        self.node_id = node_id
        self.node_desc = node_id
        self.node_type = None
        self.children = []

    def add_child(self, obj):
        self.children.append(obj)

    def render_tree(self):
        tree = f"{self.node_desc} ({self.node_type})\n"
        parents = [{"node": self, "display_children": self.children}]
        while parents:
            if len(parents[-1]["display_children"]) == 0:
                parents.pop()
                continue
            next_node = parents[-1]["display_children"][0]
            parents[-1]["display_children"].pop(0)

            prefix = ""
            for i, _ in enumerate(parents):
                last_child = len(parents[i]["display_children"]) == 0
                if i < len(parents) - 1:  # prior level
                    prefix += "    " if last_child else "\u2502   "
                else:
                    prefix += "\u2514\u2500\u2500 " if last_child else "\u251c\u2500\u2500 "

            tree += f"{prefix}{next_node.node_desc} ({next_node.node_type})\n"
            if next_node.children:
                prior_parents = [x["node"].node_id for x in parents]
                display_children = [x for x in next_node.children if x.node_id not in prior_parents]
                parents.append({"node": next_node, "display_children": display_children})

        return tree


class FileAnalyzer:

    def __init__(self, file_name, file_type, group_by_attr=None, enumerate_config=None):
        self.record_count = 0
        self.root_node = Node("root")
        self.root_node.node_desc = file_name
        self.root_node.node_type = file_type
        self.file_name = file_name
        self.file_type = file_type
        self.nodes = {"root": self.root_node}
        self.top_value_count = 10
        self.group_by_attr = group_by_attr
        self.group_by_filter = None  # Can be set after initialization
        
        # Handle both old and new enumeration formats
        if enumerate_config:
            if isinstance(enumerate_config, dict):
                # New pivot enumeration format
                self.enumerate_config = enumerate_config
                self.enumerate_attrs = []  # Keep for compatibility
                self.is_pivot_enumeration = True
            else:
                # Legacy enumeration format (list of attributes)
                self.enumerate_attrs = enumerate_config
                self.enumerate_config = None
                self.is_pivot_enumeration = False
        else:
            self.enumerate_attrs = []
            self.enumerate_config = None
            self.is_pivot_enumeration = False
        
        # For grouped analysis: track nodes and record counts per group
        if group_by_attr:
            self.groups = {}  # group_value -> {nodes: {}, record_count: 0}
            self.group_record_counts = {}  # group_value -> count
        else:
            self.groups = None
            self.group_record_counts = None
            
        # For code enumeration: track code statistics
        if self.enumerate_attrs or self.is_pivot_enumeration:
            if self.is_pivot_enumeration:
                # Pivot enumeration: track combinations of grouping attributes and their value stats
                if group_by_attr:
                    self.pivot_stats = {}  # group_value -> {(attr1_val, attr2_val, ...): {value_attr_val: {count, records}}}
                else:
                    self.pivot_stats = {}  # {(attr1_val, attr2_val, ...): {value_attr_val: {count, records}}}
                self.enumeration_stats = None  # Not used for pivot enumeration
            else:
                # Legacy enumeration
                if group_by_attr:
                    # Group-aware enumeration: group_value -> attr_path -> {code_value -> {count, records}}
                    self.enumeration_stats = {}  
                else:
                    # Standard enumeration: attr_path -> {code_value -> {count, records}}
                    self.enumeration_stats = {}  
                    for attr in self.enumerate_attrs:
                        self.enumeration_stats[attr] = {}
                self.pivot_stats = None  # Not used for legacy enumeration
        else:
            self.enumeration_stats = None
            self.pivot_stats = None

    def process_record(self, obj):
        """Process a single record, handling grouping and enumeration if enabled"""
        # Apply group_by filtering if specified
        if self.group_by_attr and self.group_by_filter and isinstance(obj, dict):
            group_value = obj.get(self.group_by_attr, "unknown")
            if str(group_value) != str(self.group_by_filter):
                return  # Skip this record
        
        # Handle enumeration if enabled
        if (self.enumerate_attrs or self.is_pivot_enumeration) and isinstance(obj, dict):
            try:
                if self.is_pivot_enumeration:
                    self.process_pivot_enumeration(obj)
                elif self.enumerate_attrs:
                    if self.group_by_attr:
                        group_value = obj.get(self.group_by_attr, "unknown")
                        self.process_enumeration_for_group(obj, group_value)
                    else:
                        self.process_enumeration(obj)
            except Exception as e:
                print(f"Error processing record {obj.get('id', 'unknown')}: {e}")
                # Continue processing other records
                pass
            
        if self.group_by_attr and isinstance(obj, dict):
            group_value = obj.get(self.group_by_attr, "unknown")
            
            # Initialize group if not exists
            if group_value not in self.groups:
                self.groups[group_value] = {
                    "nodes": {"root": Node("root")},
                    "record_count": 0
                }
                # Initialize root node for this group
                root_node = self.groups[group_value]["nodes"]["root"]
                root_node.node_desc = f"root ({group_value})"
                root_node.node_type = self.root_node.node_type
            
            # Process this record for the group
            self.groups[group_value]["record_count"] += 1
            self.iterate_obj_for_group(group_value, "root", obj)
        else:
            # Non-grouped processing (original behavior)
            self.iterate_obj("root", obj)

    def process_enumeration_for_group(self, obj, group_value):
        """Process enumeration attributes for a single record within a group"""
        # Initialize group enumeration if not exists
        if group_value not in self.enumeration_stats:
            self.enumeration_stats[group_value] = {}
            for attr in self.enumerate_attrs:
                self.enumeration_stats[group_value][attr] = {}
        
        for attr_path in self.enumerate_attrs:
            values = self.extract_nested_values(obj, attr_path)
            if values:
                for value in values:
                    if value is not None and value != "":  # Skip None and empty string, but keep False
                        value_str = str(value)
                        if value_str not in self.enumeration_stats[group_value][attr_path]:
                            self.enumeration_stats[group_value][attr_path][value_str] = {
                                'count': 0,
                                'records': set()
                            }
                        self.enumeration_stats[group_value][attr_path][value_str]['count'] += 1
                        # Track which records contain this code (using record ID if available)
                        record_id = obj.get('id', f'record_{self.record_count}')
                        self.enumeration_stats[group_value][attr_path][value_str]['records'].add(record_id)

    def process_enumeration(self, obj):
        """Process enumeration attributes for a single record"""
        for attr_path in self.enumerate_attrs:
            values = self.extract_nested_values(obj, attr_path)
            if values:
                for value in values:
                    if value is not None and value != "":  # Skip None and empty string, but keep False
                        value_str = str(value)
                        if value_str not in self.enumeration_stats[attr_path]:
                            self.enumeration_stats[attr_path][value_str] = {
                                'count': 0,
                                'records': set()
                            }
                        self.enumeration_stats[attr_path][value_str]['count'] += 1
                        # Track which records contain this code (using record ID if available)
                        record_id = obj.get('id', f'record_{self.record_count}')
                        self.enumeration_stats[attr_path][value_str]['records'].add(record_id)

    def process_pivot_enumeration(self, obj):
        """Process pivot enumeration for a single record"""
        config = self.enumerate_config
        level = config['level']
        grouping_attrs = config['grouping_attrs']
        value_attr = config['value_attr']
        
        # Get the base object at the specified level
        if level and level != 'root':
            base_obj = self.get_nested_value(obj, level)
            if not base_obj:
                return
        else:
            base_obj = obj
        
        # Extract all attribute values (grouping + value)
        all_attrs = grouping_attrs + [value_attr]
        all_values = []
        max_length = 0
        
        for attr in all_attrs:
            values = self.extract_nested_values(base_obj, attr)
            all_values.append(values)
            if values:
                max_length = max(max_length, len(values))
        
        # Check that all attributes have consistent list lengths or are non-lists
        if max_length > 0:
            for i, values in enumerate(all_values):
                if values and len(values) != max_length and len(values) != 1:
                    # Allow single values to be repeated across the list
                    if len(values) > 1:
                        # Instead of throwing an error, just skip this record
                        return
        
        # If no values found for the value attribute, return
        value_values = all_values[-1]  # Last attribute is the value attribute  
        if not value_values:
            return
            
        # Set max_length to the length of the value attribute if no other attributes have values
        if max_length == 0:
            max_length = len(value_values)
        
        # Handle group-by organization
        if self.group_by_attr:
            group_value = obj.get(self.group_by_attr, "unknown")
            if group_value not in self.pivot_stats:
                self.pivot_stats[group_value] = {}
            group_pivot_stats = self.pivot_stats[group_value]
        else:
            group_pivot_stats = self.pivot_stats
        
        # Iterate through all combinations
        for i in range(max_length):
            # Extract grouping values for this iteration
            grouping_values = []
            for j, attr in enumerate(grouping_attrs):
                values = all_values[j]
                if values:
                    if len(values) == 1:
                        # Repeat single value across all iterations
                        grouping_values.append(str(values[0]))
                    else:
                        # Use corresponding item from the list
                        grouping_values.append(str(values[i]))
                else:
                    grouping_values.append('unknown')
            
            # Extract value for this iteration
            value_values = all_values[-1]  # Last attribute is the value attribute
            if value_values:
                if len(value_values) == 1:
                    value = value_values[0]
                else:
                    value = value_values[i]
            else:
                continue
            
            if value is None or value == "":
                continue
                
            # Create grouping key
            grouping_key = tuple(grouping_values)
            
            # Initialize grouping key if not exists
            if grouping_key not in group_pivot_stats:
                group_pivot_stats[grouping_key] = {}
            
            # Track the value
            value_str = str(value)
            if value_str not in group_pivot_stats[grouping_key]:
                group_pivot_stats[grouping_key][value_str] = {
                    'count': 0,
                    'records': set()
                }
            group_pivot_stats[grouping_key][value_str]['count'] += 1
            record_id = obj.get('id', f'record_{self.record_count}')
            group_pivot_stats[grouping_key][value_str]['records'].add(record_id)

    def extract_nested_values(self, obj, attr_path):
        """Extract values from nested attribute path like 'properties.type.type'"""
        parts = attr_path.split('.')
        current = obj
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and current:
                # Handle list of dicts - look for the part in each dict
                new_values = []
                for item in current:
                    if isinstance(item, dict) and part in item:
                        new_values.append(item[part])
                if new_values:
                    current = new_values
                else:
                    return []
            else:
                return []
        
        # Handle different types of values
        if isinstance(current, list):
            return current
        elif current is not None:
            return [current]
        else:
            return []

    def get_nested_value(self, obj, attr_path):
        """Get a single nested value (not a list) from attribute path"""
        parts = attr_path.split('.')
        current = obj
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current

    def iterate_obj_for_group(self, group_value, prior_key, obj):
        """Iterate object for a specific group"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key and key != self.group_by_attr:  # Skip the grouping attribute itself
                    self.update_node_for_group(group_value, prior_key, key, value)
                    if isinstance(value, (dict, list, np.ndarray)):
                        self.iterate_obj_for_group(group_value, f"{prior_key}.{key}", value)

        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list, np.ndarray)):
                    self.iterate_obj_for_group(group_value, prior_key, item)
                else:
                    self.update_node_for_group(group_value, prior_key, prior_key.split(".")[-1], item)

    def iterate_obj(self, prior_key, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key:  # bad csvs have blank field names!
                    self.update_node(prior_key, key, value)
                    if isinstance(value, (dict, list, np.ndarray)):
                        self.iterate_obj(f"{prior_key}.{key}", value)

        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list, np.ndarray)):
                    self.iterate_obj(prior_key, item)
                else:
                    self.update_node(prior_key, prior_key.split(".")[-1], item)

    def update_node_for_group(self, group_value, prior_key, key, value):
        """Update node for a specific group"""
        attr_key = f"{prior_key}.{key}" if key else prior_key
        group_nodes = self.groups[group_value]["nodes"]
        
        if attr_key not in group_nodes:
            group_nodes[attr_key] = Node(attr_key)
            group_nodes[attr_key].node_desc = attr_key.replace("root.", "")
            group_nodes[attr_key].node_type = "unk"
            group_nodes[attr_key].record_count = 0
            group_nodes[attr_key].unique_values = {}
            group_nodes[prior_key].add_child(group_nodes[attr_key])

        if value is not None:
            # Handle numpy arrays and other array-like objects
            try:
                if hasattr(value, '__len__') and not isinstance(value, str):
                    # Check if it's empty for arrays/lists
                    is_empty = len(value) == 0
                else:
                    # For scalar values, check truthiness normally
                    is_empty = not bool(value)
            except (ValueError, TypeError):
                # Fallback for values that can't be easily checked
                is_empty = False
                
            if not is_empty:
                if group_nodes[attr_key].node_type == "unk":
                    group_nodes[attr_key].node_type = str(type(value))[8:-2]

                if isinstance(value, (dict, list)):
                    value = f"{len(value)} items"
                elif isinstance(value, np.ndarray):
                    value = f"array({value.shape}) items"
                    
            # Ensure value is always a string for dictionary key
            value = str(value)

            group_nodes[attr_key].record_count += 1
            if value not in group_nodes[attr_key].unique_values:
                group_nodes[attr_key].unique_values[value] = 1
            else:
                group_nodes[attr_key].unique_values[value] += 1

    def update_node(self, prior_key, key, value):
        attr_key = f"{prior_key}.{key}" if key else prior_key
        if attr_key not in self.nodes:
            self.nodes[attr_key] = Node(attr_key)
            self.nodes[attr_key].node_desc = attr_key.replace("root.", "")
            self.nodes[attr_key].node_type = "unk"

            self.nodes[attr_key].record_count = 0
            self.nodes[attr_key].unique_values = {}
            self.nodes[prior_key].add_child(self.nodes[attr_key])

        if value is not None:
            # Handle numpy arrays and other array-like objects
            try:
                if hasattr(value, '__len__') and not isinstance(value, str):
                    # Check if it's empty for arrays/lists
                    is_empty = len(value) == 0
                else:
                    # For scalar values, check truthiness normally
                    is_empty = not bool(value)
            except (ValueError, TypeError):
                # Fallback for values that can't be easily checked
                is_empty = False
                
            if not is_empty:
                if self.nodes[attr_key].node_type == "unk":
                    self.nodes[attr_key].node_type = str(type(value))[8:-2]

                if isinstance(value, (dict, list)):
                    value = f"{len(value)} items"
                elif isinstance(value, np.ndarray):
                    value = f"array({value.shape}) items"
                
            # Ensure value is always a string for dictionary key
            value = str(value)

            self.nodes[attr_key].record_count += 1
            if value not in self.nodes[attr_key].unique_values:
                self.nodes[attr_key].unique_values[value] = 1
            else:
                self.nodes[attr_key].unique_values[value] += 1

    def matches_filter(self, obj, filter_attr, filter_value):
        """Check if object matches the filter criteria"""
        parts = filter_attr.split(".")
        current = obj

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False

        return str(current) == filter_value

    def generate(self, template):
        if self.group_by_attr and template == "report":
            return self.generate_grouped_report()
        elif template == "report":
            return self.generate_standard_report()
        else:
            return self.generate_code_template()

    def generate_grouped_report(self):
        """Generate a grouped report with schema as first column"""
        header = [self.group_by_attr, "attribute", "type", "record_cnt", "record_pct", "unique_cnt", "unique_pct"]
        header.extend([f"top_value{i+1}" for i in range(self.top_value_count)])
        
        rows = []
        for group_value in sorted(self.groups.keys()):
            group_data = self.groups[group_value]
            group_nodes = group_data["nodes"]
            group_record_count = group_data["record_count"]
            
            # Traverse nodes for this group
            root_node = group_nodes["root"]
            parents = [{"node": root_node, "children": root_node.children.copy()}]
            while parents:
                if len(parents[-1]["children"]) == 0:
                    parents.pop()
                    continue
                next_node = parents[-1]["children"][0]
                parents[-1]["children"].pop(0)

                attr_code = next_node.node_desc
                attr_type = next_node.node_type
                record_cnt = next_node.record_count
                record_pct = round(record_cnt / group_record_count * 100, 2) if group_record_count else 0
                unique_cnt = len(next_node.unique_values)
                unique_pct = round(unique_cnt / record_cnt * 100, 2) if record_cnt else 0

                top_values = [""] * self.top_value_count
                if self.top_value_count:
                    i = 0
                    for k, v in sorted(next_node.unique_values.items(), key=lambda v: v[1], reverse=True):
                        top_values[i] = f"{str(k)[0:50]} ({v})"
                        i += 1
                        if i == self.top_value_count:
                            break

                rows.append([group_value, attr_code, attr_type, record_cnt, record_pct, unique_cnt, unique_pct] + top_values)

                if next_node.children:
                    parents.append({"node": next_node, "children": next_node.children.copy()})
        
        return [header] + rows

    def generate_standard_report(self):
        """Generate the standard non-grouped report"""
        header = ["attribute", "type", "record_cnt", "record_pct", "unique_cnt", "unique_pct"]
        header.extend([f"top_value{i+1}" for i in range(self.top_value_count)])

        rows = []
        root_node = self.root_node
        parents = [{"node": root_node, "children": root_node.children.copy()}]
        while parents:
            if len(parents[-1]["children"]) == 0:
                parents.pop()
                continue
            next_node = parents[-1]["children"][0]
            parents[-1]["children"].pop(0)

            attr_code = next_node.node_desc
            attr_type = next_node.node_type
            record_cnt = next_node.record_count
            record_pct = round(record_cnt / self.record_count * 100, 2)
            unique_cnt = len(next_node.unique_values)
            unique_pct = round(unique_cnt / record_cnt * 100, 2) if record_cnt else 0

            top_values = [""] * self.top_value_count
            if self.top_value_count:
                i = 0
                for k, v in sorted(next_node.unique_values.items(), key=lambda v: v[1], reverse=True):
                    top_values[i] = f"{str(k)[0:50]} ({v})"
                    i += 1
                    if i == self.top_value_count:
                        break

            rows.append([attr_code, attr_type, record_cnt, record_pct, unique_cnt, unique_pct] + top_values)

            if next_node.children:
                parents.append({"node": next_node, "children": next_node.children.copy()})

        return [header] + rows

    def generate_code_template(self):
        """Generate code template (non-grouped only for now)"""
        rows = []
        root_node = self.root_node
        parents = [{"node": root_node, "children": root_node.children.copy()}]
        while parents:
            if len(parents[-1]["children"]) == 0:
                parents.pop()
                continue
            next_node = parents[-1]["children"][0]
            parents[-1]["children"].pop(0)

            attr_code = next_node.node_desc
            attr_type = next_node.node_type
            record_cnt = next_node.record_count
            record_pct = round(record_cnt / self.record_count * 100, 2)
            unique_cnt = len(next_node.unique_values)
            unique_pct = round(unique_cnt / record_cnt * 100, 2) if record_cnt else 0

            top_values = [""] * self.top_value_count
            if self.top_value_count:
                i = 0
                for k, v in sorted(next_node.unique_values.items(), key=lambda v: v[1], reverse=True):
                    top_values[i] = f"{str(k)[0:50]} ({v})"
                    i += 1
                    if i == self.top_value_count:
                        break

            attr_list = attr_code.split(".")
            last_attr = attr_list[-1]
            if len(attr_list) == 1:
                indent = ""
                prior_data = "raw_data"
            else:
                indent = "    " * (len(attr_list) - 1)
                prior_data = f"raw_data{len(attr_list) - 1}"

            rows.append("")
            rows.append(f"{indent}# attribute: {attr_code} ({attr_type})")
            rows.append(f"{indent}# {record_pct} populated, {unique_pct} unique")
            for item in (item for item in top_values if item):
                rows.append(f"{indent}#      {item}")

            if attr_type in ("list", "np.ndarray"):
                new_data = f"raw_data{len(attr_list)}"
                rows.append(f'{indent}for {new_data} in self.ensure_list({prior_data}.get("{last_attr}")):')
            elif attr_type in ("dict"):
                new_data = f"raw_data{len(attr_list)}"
                rows.append(f'{indent}if {prior_data}.get("{last_attr}"):')
                rows.append(f'{indent}    {new_data} = {prior_data}.get("{last_attr}")')
            else:
                item = f'"{last_attr}": {prior_data}["{last_attr}"]'
                rows.append(indent + "json_obj.add_payload({" + item + "})")

            if next_node.children:
                parents.append({"node": next_node, "children": next_node.children.copy()})

        return rows

    def generate_enumeration_report(self):
        """Generate enumeration report for code values"""
        if self.is_pivot_enumeration:
            return self.generate_pivot_enumeration_report()
        elif not self.enumerate_attrs or not self.enumeration_stats:
            return [["No enumeration data available"]]
        else:
            if self.group_by_attr:
                return self.generate_grouped_enumeration_report()
            else:
                return self.generate_standard_enumeration_report()

    def generate_grouped_enumeration_report(self):
        """Generate grouped enumeration report"""
        header = [self.group_by_attr, "attribute", "code_value", "record_cnt", "record_pct", "unique_records", "unique_pct"]
        header.extend([f"top_record{i+1}" for i in range(min(self.top_value_count, 5))])
        
        rows = []
        for group_value in sorted(self.enumeration_stats.keys()):
            group_enum_stats = self.enumeration_stats[group_value]
            group_record_count = self.groups[group_value]["record_count"]
            
            for attr_path in sorted(self.enumerate_attrs):
                attr_stats = group_enum_stats.get(attr_path, {})
                
                if not attr_stats:
                    continue
                    
                # Calculate total occurrences for this attribute across all codes in this group
                total_occurrences = sum(stats['count'] for stats in attr_stats.values())
                
                # Sort codes by frequency
                sorted_codes = sorted(attr_stats.items(), key=lambda x: x[1]['count'], reverse=True)
                
                for code_value, stats in sorted_codes:
                    record_cnt = stats['count']
                    record_pct = round(record_cnt / total_occurrences * 100, 2) if total_occurrences else 0
                    unique_records = len(stats['records'])
                    unique_pct = round(unique_records / group_record_count * 100, 2) if group_record_count else 0
                    
                    # Get sample record IDs (top N)
                    sample_records = [""] * min(self.top_value_count, 5)
                    for i, record_id in enumerate(sorted(stats['records'])):
                        if i >= min(self.top_value_count, 5):
                            break
                        sample_records[i] = f"{record_id}"
                    
                    rows.append([group_value, attr_path, code_value, record_cnt, record_pct, unique_records, unique_pct] + sample_records)
        
        return [header] + rows

    def generate_standard_enumeration_report(self):
        """Generate standard (non-grouped) enumeration report"""
        header = ["attribute", "code_value", "record_cnt", "record_pct", "unique_records", "unique_pct"]
        header.extend([f"top_record{i+1}" for i in range(min(self.top_value_count, 5))])
        
        rows = []
        for attr_path in sorted(self.enumerate_attrs):
            attr_stats = self.enumeration_stats[attr_path]
            
            if not attr_stats:
                continue
                
            # Calculate total occurrences for this attribute across all codes
            total_occurrences = sum(stats['count'] for stats in attr_stats.values())
            
            # Sort codes by frequency
            sorted_codes = sorted(attr_stats.items(), key=lambda x: x[1]['count'], reverse=True)
            
            for code_value, stats in sorted_codes:
                record_cnt = stats['count']
                record_pct = round(record_cnt / total_occurrences * 100, 2) if total_occurrences else 0
                unique_records = len(stats['records'])
                unique_pct = round(unique_records / self.record_count * 100, 2) if self.record_count else 0
                
                # Get sample record IDs (top N)
                sample_records = [""] * min(self.top_value_count, 5)
                for i, record_id in enumerate(sorted(stats['records'])):
                    if i >= min(self.top_value_count, 5):
                        break
                    sample_records[i] = f"{record_id}"
                
                rows.append([attr_path, code_value, record_cnt, record_pct, unique_records, unique_pct] + sample_records)
        
        return [header] + rows

    def generate_pivot_enumeration_report(self):
        """Generate pivot enumeration report"""
        if not self.pivot_stats:
            return [["No pivot enumeration data available"]]
        
        config = self.enumerate_config
        grouping_attrs = config['grouping_attrs']
        value_attr = config['value_attr']
        
        # Create header
        header = []
        if self.group_by_attr:
            header.append(self.group_by_attr)
        
        # Add grouping attribute columns
        for attr in grouping_attrs:
            header.append(f"{config['level']}.{attr}" if config['level'] != 'root' else attr)
        
        # Add value columns - changed to show aggregated statistics instead of individual values
        header.extend(["record_cnt", "record_pct", "unique_values", "unique_pct"])
        header.extend([f"top_value{i+1}" for i in range(min(self.top_value_count, 5))])
        
        rows = []
        
        if self.group_by_attr:
            # Group-based pivot enumeration - collect all rows first for proper sorting
            all_rows = []
            for group_value in self.pivot_stats.keys():
                group_pivot_stats = self.pivot_stats[group_value]
                group_record_count = self.groups[group_value]["record_count"] if self.groups else self.record_count
                
                for grouping_key, value_stats in group_pivot_stats.items():
                    # Aggregate all values within this grouping combination
                    total_record_cnt = sum(stats['count'] for stats in value_stats.values())
                    all_records = set()
                    value_counts = {}
                    
                    for value, stats in value_stats.items():
                        all_records.update(stats['records'])
                        value_counts[value] = stats['count']
                    
                    record_pct = round(total_record_cnt / group_record_count * 100, 2) if group_record_count else 0
                    unique_values = len(value_stats)
                    unique_pct = round(unique_values / total_record_cnt * 100, 2) if total_record_cnt else 0
                    
                    # Get top values by count
                    top_values = [""] * min(self.top_value_count, 5)
                    for i, (value, count) in enumerate(sorted(value_counts.items(), key=lambda x: x[1], reverse=True)):
                        if i >= min(self.top_value_count, 5):
                            break
                        top_values[i] = f"{value} ({count})"
                    
                    # Build row
                    row = [group_value]
                    row.extend(list(grouping_key))
                    row.extend([total_record_cnt, record_pct, unique_values, unique_pct])
                    row.extend(top_values)
                    all_rows.append(row)
            
            # Sort by schema (first column) and then by grouping attributes
            rows = sorted(all_rows, key=lambda x: (x[0],) + tuple(x[1:len(grouping_attrs)+1]))
        else:
            # Non-grouped pivot enumeration
            for grouping_key, value_stats in sorted(self.pivot_stats.items()):
                # Aggregate all values within this grouping combination
                total_record_cnt = sum(stats['count'] for stats in value_stats.values())
                all_records = set()
                value_counts = {}
                
                for value, stats in value_stats.items():
                    all_records.update(stats['records'])
                    value_counts[value] = stats['count']
                
                record_pct = round(total_record_cnt / self.record_count * 100, 2) if self.record_count else 0
                unique_values = len(value_stats)
                unique_pct = round(unique_values / total_record_cnt * 100, 2) if total_record_cnt else 0
                
                # Get top values by count
                top_values = [""] * min(self.top_value_count, 5)
                for i, (value, count) in enumerate(sorted(value_counts.items(), key=lambda x: x[1], reverse=True)):
                    if i >= min(self.top_value_count, 5):
                        break
                    top_values[i] = f"{value} ({count})"
                
                # Build row
                row = list(grouping_key)
                row.extend([total_record_cnt, record_pct, unique_values, unique_pct])
                row.extend(top_values)
                rows.append(row)
        
        return [header] + rows


def create_python_script(code_rows, file_type, encoding):
    """Generate Python script from template with improved modularity"""
    template_file_name = os.path.dirname(__file__) + os.path.sep + "python_template.py"
    
    # Define template replacements in a cleaner way
    template_replacements = {
        "# import csv or pandas here": lambda: get_import_statement(file_type),
        "# place column mappings here": lambda line: generate_column_mappings_block(code_rows, line),
        "# open reader here": lambda line: generate_file_reader_block(file_type, encoding, line),
        "for json_data in mapper.map(row)": lambda: get_mapper_call(file_type),
        "for row in reader": lambda: get_file_loop(file_type),
        "# close reader here": lambda: get_file_close(file_type)
    }
    
    script_rows = []
    with open(template_file_name, "r") as file:
        for line in file:
            line = line.rstrip()  # remove trailing whitespace/newlines
            
            # Check for template markers and replace them
            replacement_made = False
            for marker, replacement_func in template_replacements.items():
                if marker in line:
                    if marker == "# place column mappings here":
                        # Special handling for column mappings (needs line for indentation)
                        result = replacement_func(line)
                    elif marker in ["# open reader here"]:
                        # Special handling for blocks that need indentation
                        result = replacement_func(line)
                    else:
                        # Simple replacements
                        result = replacement_func()
                        if isinstance(result, str):
                            # For lines ending with ":", replace the whole line with proper indentation
                            if marker in ["for json_data in mapper.map(row)", "for row in reader"] and line.strip().endswith(":"):
                                indent = " " * (len(line) - len(line.lstrip()))
                                line = indent + result
                            else:
                                line = line.replace(marker, result)
                        
                    if isinstance(result, list):
                        script_rows.extend(result)
                        replacement_made = True
                        break
                    elif marker == "# place column mappings here" or marker == "# open reader here":
                        script_rows.extend(result)
                        replacement_made = True
                        break
            
            if not replacement_made:
                script_rows.append(line)
    
    return script_rows

def get_import_statement(file_type):
    """Get the appropriate import statement for the file type"""
    imports = {
        "csv": "import csv",
        "parquet": "import pandas as pd",
        "json": "import json",
        "jsonl": "import json",
        "xml": "import xml.etree.ElementTree as ET"
    }
    return imports.get(file_type, "# No additional imports needed")

def generate_column_mappings_block(code_rows, template_line):
    """Generate the column mappings block with proper indentation"""
    if not code_rows:
        return [template_line.replace("# place column mappings here", "# No column mappings generated")]
    
    indent = " " * template_line.find("# place column mappings here")
    return [indent + code for code in code_rows]

def generate_file_reader_block(file_type, encoding, template_line):
    """Generate the file reader initialization block"""
    indent = " " * template_line.find("# open reader here")
    
    if file_type == "parquet":
        return [
            indent + 'file = pd.read_parquet(file_name, engine="auto")',
            indent + 'reader = iter(file.to_dict(orient="records"))'
        ]
    elif file_type in ["json", "jsonl"]:
        return [
            indent + f'input_file = open(file_name, "r", encoding="{encoding}")'
        ]
    elif file_type == "xml":
        return [
            indent + f'input_file = open(file_name, "r", encoding="{encoding}")',
            indent + 'tree = ET.parse(input_file)',
            indent + 'root = tree.getroot()',
            indent + 'reader = [xml_to_dict(child) for child in root]'
        ]
    else:  # CSV
        return [
            indent + f'input_file = open(file_name, "r", encoding="{encoding}")',
            indent + 'csv_dialect = csv.Sniffer().sniff(input_file.read(2048), delimiters=[",", ";", "|", "\\t"])',
            indent + 'input_file.seek(0)',
            indent + 'reader = csv.DictReader(input_file, dialect=csv_dialect)'
        ]

def get_mapper_call(file_type):
    """Get the appropriate mapper call for the file type"""
    if file_type in ["json", "jsonl"]:
        return "for json_data in mapper.map(json.loads(row)):"
    else:
        return "for json_data in mapper.map(row):"

def get_file_loop(file_type):
    """Get the appropriate file reading loop for the file type"""
    if file_type in ["json", "jsonl"]:
        return "for row in input_file:"
    else:
        return "for row in reader:"

def get_file_close(file_type):
    """Get the appropriate file closing statement for the file type"""
    if file_type != "parquet":
        return "input_file.close()"
    else:
        return "# No file closing needed for parquet"

def create_python_script_legacy(code_rows, file_type, encoding):
    """Legacy method for backward compatibility"""
    script_rows = []
    template_file_name = os.path.dirname(__file__) + os.path.sep + "python_template.py"

    import_here = "# import csv or pandas here"
    mapping_start = "# place column mappings here"
    open_reader = "# open reader here"
    mapper_call = "for json_data in mapper.map(row)"
    file_loop = "for row in reader:"
    close_file = "# close reader here"
    with open(template_file_name, "r") as file:
        for line in file:
            line = line[0:-1]  # remove linefeed
            if line.startswith(import_here):
                if file_type == "csv":
                    script_rows.append("import csv")
                elif file_type == "parquet":
                    script_rows.append("import pandas as pd")
            elif line.strip().startswith(mapping_start):
                indent = " " * line.find(mapping_start)
                for code in code_rows:
                    script_rows.append(indent + code)
            elif line.strip().startswith(open_reader):
                indent = " " * line.find(open_reader)

                if file_type == "parquet":
                    script_rows.append(indent + 'file = pd.read_parquet(fileName, engine="auto")')
                    script_rows.append(indent + 'reader = iter(file.to_dict(orient="records"))')
                elif file_type.startswith("json"):
                    script_rows.append(indent + f'input_file = open(file_name, "r", encoding="{encoding}")')
                else:
                    script_rows.append(indent + f'input_file = open(file_name, "r", encoding="{encoding}")')
                    script_rows.append(
                        indent
                        + f'csv_dialect = csv.Sniffer().sniff(input_file.read(2048), delimiters=[",", ";", "|", "\t"])'
                    )
                    script_rows.append(indent + f"input_file.seek(0)")
                    script_rows.append(indent + f"reader = csv.DictReader(input_file, dialect=csv_dialect)")
            elif line.strip().startswith(mapper_call) and file_type.startswith("json"):
                script_rows.append(line.replace("(row)", "(json.loads(row))"))
            elif line.strip().startswith(file_loop) and file_type.startswith("json"):
                script_rows.append(line.replace("reader", "input_file"))
            elif line.strip().startswith(close_file):
                if file_type != "parquet":
                    script_rows.append(line.replace(close_file, "input_file.close()"))
            else:
                script_rows.append(line)

    return script_rows


def strip_namespace(tag):
    """Return XML tag without namespace info like '{ns}Tag'."""
    if isinstance(tag, str) and tag.startswith('{'):
        return tag.split('}', 1)[1]
    return tag


def element_to_dict(element):
    """Convert an XML element to a dictionary recursively."""
    result = {}
    if element.attrib:
        result.update({strip_namespace(k): v for k, v in element.attrib.items()})
    if element.text and element.text.strip():
        result['text'] = element.text.strip()

    children = {}
    for child in element:
        child_dict = element_to_dict(child)
        tag = strip_namespace(child.tag)
        if tag in children:
            if not isinstance(children[tag], list):
                children[tag] = [children[tag]]
            children[tag].append(child_dict)
        else:
            children[tag] = child_dict
    
    result.update(children)
    return result


def report_viewer(report):
    table_object = prettytable.PrettyTable()
    table_object.horizontal_char = "\u2500"
    table_object.vertical_char = "\u2502"
    table_object.junction_char = "\u253c"
    table_object.field_names = report[0]
    table_object.add_rows(report[1:])
    for column in report[0]:
        if any(column.endswith(x) for x in ["cnt", "pct"]):
            table_object.align[column] = "r"
        else:
            table_object.align[column] = "l"
    report_str = table_object.get_string()
    less = subprocess.Popen(["less", "-FMXSR"], stdin=subprocess.PIPE)
    try:
        less.stdin.write(report_str.encode("utf-8"))
        less.stdin.close()
        less.wait()
        print()
    except IOError as ex:
        print(f"\n{ex}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze file structure and generate statistics reports or code enumeration analyses.",
        epilog="""
USAGE EXAMPLES:

Schema Analysis (discover file structure):
  %(prog)s data.jsonl -o schema.csv
  %(prog)s data.jsonl --group_by schema -o schema_by_type.csv
  
Code Enumeration (analyze specific attribute values):
  %(prog)s data.jsonl --enumerate "properties:type,country:number" -o analysis.csv
  %(prog)s data.jsonl --group_by schema=Identification --enumerate "properties:type:number" -o id_types.csv
  
Legacy Enumeration (backward compatibility):
  %(prog)s data.jsonl --enumerate "properties.type" -o codes.csv
  
Filtering:
  %(prog)s data.jsonl --filter "status=active" -o filtered_schema.csv
  %(prog)s data.jsonl --group_by schema=Person --enumerate "properties:name:identifier" -o person_names.csv

ENUMERATION FORMATS:
  Legacy: --enumerate "attr1,attr2"          (lists code values in specified attributes)
  Pivot:  --enumerate "level:dims:value"     (cross-tabulates dimensions against values)
  
  Example: --enumerate "properties:type,country:number"
    - Level: properties (base object level)
    - Dimensions: type,country (grouping attributes) 
    - Value: number (attribute being analyzed)
    
GROUP_BY FORMATS:
  Basic:     --group_by schema               (group statistics by schema)
  Filtered:  --group_by schema=Person        (group by schema, show only Person records)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input_file", 
                       help="Input file path (supports CSV, JSON, JSONL, Parquet, XML)")
    parser.add_argument("-t", "--file_type", 
                       help='File type: "csv", "jsonl", "json", "parquet", "xml" (auto-detected if not specified)')
    parser.add_argument("-e", "--encoding", default="utf-8", 
                       help="File encoding (default: utf-8)")
    parser.add_argument("-o", "--output_file", 
                       help="Output CSV file path (required for --enumerate, optional for schema analysis)")
    parser.add_argument("-p", "--python_file_name", 
                       help="Generate Python code file for processing the input data")
    parser.add_argument("--top_values", type=int, default=5, 
                       help="Number of top values to display/analyze (default: 5)")
    parser.add_argument("--filter", 
                       help="Filter records: 'attribute=value' (e.g., 'status=active', 'type=Person')")
    parser.add_argument("--group_by", 
                       help="Group analysis by attribute. Formats: 'attr' or 'attr=value' (e.g., 'schema' or 'schema=Person')")
    parser.add_argument("--enumerate", 
                       help="""Enumerate code values. Formats:
Legacy: 'attr1,attr2' - list codes in attributes
Pivot: 'level:dimensions:value' - cross-tabulate dimensions vs values
Example: 'properties:type,country:number'""")
    args = parser.parse_args()

    if not args.input_file or not glob.glob(args.input_file):
        print("\nPlease supply a valid input file specification on the command line\n")
        sys.exit(1)
    file_list = glob.glob(args.input_file)

    if not args.file_type:
        ext = pathlib.Path(file_list[0]).suffix.lower()
        if ext in (".parquet", ".json", ".jsonl", ".xml", ".xmls"):  # Add .xmls to detection
            args.file_type = ext[1:] if ext != ".xmls" else "xml"  # Map .xmls to 'xml'
        else:
            args.file_type = "csv"
    else:
        args.file_type = args.file_type.lower()

    if args.file_type.lower() == "parquet" and not pd:
        print("\nPandas must be installed to analyze parquet files, try: pip3 install pandas\n")
        sys.exit(1)
    if args.file_type.lower() in ("xml", "xmls") and not hasattr(ET, 'parse'):  # Update check to include xmls
        print("\nxml.etree.ElementTree is required for XML files.\n")
        sys.exit(1)

    proc_start_time = time.time()
    shut_down = 0
    
    # Parse group_by parameter - check for filtering syntax
    group_by_attr = None
    group_by_filter = None
    if args.group_by:
        if '=' in args.group_by:
            group_by_attr, group_by_filter = args.group_by.split('=', 1)
        else:
            group_by_attr = args.group_by
    
    # Parse enumeration parameter - check for new pivot syntax
    enumerate_config = None
    if args.enumerate:
        if ':' in args.enumerate and args.enumerate.count(':') == 2:
            # New pivot syntax: level:grouping_attributes:value_attribute
            level, grouping_attrs, value_attr = args.enumerate.split(':')
            enumerate_config = {
                'level': level.strip(),
                'grouping_attrs': [attr.strip() for attr in grouping_attrs.split(',')],
                'value_attr': value_attr.strip()
            }
        else:
            # Legacy syntax for backward compatibility
            enumerate_config = [attr.strip() for attr in args.enumerate.split(',')]
    
    # Check for conflicting options
    if enumerate_config and not args.output_file:
        print("\nError: When using --enumerate, you must specify -o/--output_file for the enumeration CSV output.\n")
        sys.exit(1)
    
    analyzer = FileAnalyzer(args.input_file, args.file_type, group_by_attr, enumerate_config)
    analyzer.top_value_count = args.top_values
    
    # Set group_by filter if specified
    if group_by_filter:
        analyzer.group_by_filter = group_by_filter

    try:
        file_num = 0
        for file_name in file_list:
            file_num += 1
            print(f"reading file {file_num} of {len(file_list)}: {file_name}")
            if args.file_type == "parquet":
                file = pd.read_parquet(file_name, engine="auto")  # Fix typo: fileName -> file_name
                reader = iter(file.to_dict(orient="records"))
            elif args.file_type.startswith("json"):
                file = open(file_name, "r", encoding=args.encoding)
                reader = JsonReader(file)
            elif args.file_type in ("xml", "xmls"):  # Update to include xmls
                tree = ET.parse(file_name)
                root = tree.getroot()
                reader = (element_to_dict(child) for child in root)  # Assume children of root are records
            else:
                file = open(file_name, "r", encoding=args.encoding)
                sample = file.read(8192)  # Larger sample size
                file.seek(0)
                try:
                    csv_dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "|", "\t"])
                    reader = csv.DictReader(file, dialect=csv_dialect)
                except csv.Error:
                    # Fallback: try tab delimiter
                    reader = csv.DictReader(file, delimiter="\t")
            if args.filter:
                filter_attr, filter_value = args.filter.split("=")

            for row in reader:
                if args.filter and not analyzer.matches_filter(row, filter_attr, filter_value):
                    continue

                analyzer.record_count += 1
                if analyzer.record_count % 10000 == 0:
                    print(f"{analyzer.record_count:,} rows read")
                
                # Use the new process_record method that handles grouping
                analyzer.process_record(row)

    except KeyboardInterrupt:
        shut_down = 9

    status = "complete" if shut_down == 0 else "interrupted"
    print(f"\n{analyzer.record_count:,} rows read, file {status}\n")

    # If enumeration is requested, only generate enumeration report
    if enumerate_config:
        has_enumeration_data = (analyzer.enumeration_stats and any(analyzer.enumeration_stats.values())) or \
                              (analyzer.pivot_stats and any(analyzer.pivot_stats.values()))
        if has_enumeration_data:
            enum_report = analyzer.generate_enumeration_report()
            if len(enum_report) > 1:  # Has data beyond header
                if args.output_file:
                    with open(args.output_file, "w") as file:
                        writer = csv.writer(file)
                        writer.writerows(enum_report)
                    print(f"enumeration report saved to {args.output_file}\n")
                else:
                    print("\n" + "="*60)
                    print("CODE ENUMERATION REPORT")
                    print("="*60)
                    
                    if prettytable:
                        report_viewer(enum_report)
                    else:
                        # Simple text output for enumeration
                        header = enum_report[0]
                        print(f"{'Attribute':<30} {'Code Value':<20} {'Count':<8} {'Pct':<8} {'Records':<8} {'Sample Records':<50}")
                        print("-" * 120)
                        for row in enum_report[1:]:
                            if len(row) >= 6:
                                sample_records = " | ".join(str(r) for r in row[6:] if r)
                                print(f"{row[0]:<30} {row[1]:<20} {row[2]:<8} {row[3]:<8} {row[4]:<8} {sample_records:<50}")
                        print()
            else:
                print("No enumeration data found for the specified attributes.\n")
        else:
            print("No enumeration data found for the specified attributes and filters.\n")
            print("This could be because:")
            print("- No records matched the group filter criteria")
            print("- The specified attribute paths don't exist in the data")
            print("- The data structure doesn't match the expected format")
            print("\nTip: Try running without --enumerate first to see the schema structure.\n")
            sys.exit(1)
        
        # Exit after enumeration - don't generate schema report
        if args.python_file_name:
            code_rows = analyzer.generate("code")
            script_rows = create_python_script(code_rows, args.file_type, args.encoding)
            with open(args.python_file_name, "w") as file:
                file.write("\n".join(script_rows) + "\n")
            print(f"python code saved to {args.python_file_name}\n")
        sys.exit(shut_down)
    else:
        # Generate main schema report
        report_rows = analyzer.generate("report")
        if args.output_file:
            with open(args.output_file, "w") as file:
                writer = csv.writer(file)
                metadata_rows = [
                    ["file_name", analyzer.file_name],
                    ["file_type", analyzer.file_type],
                    []
                ]
                writer.writerows(metadata_rows + report_rows)
            print(f"statistical report saved to {args.output_file}\n")
        elif prettytable:
            report_viewer(report_rows)
        else:
            # Fallback: simple text output when prettytable is not available
            output_lines = []
            output_lines.append("Statistical Analysis Report:")
            output_lines.append("=" * 100)
            header = report_rows[0] if report_rows else []
            if header:
                output_lines.append(f"{'Attribute':<25} {'Type':<15} {'Count':<8} {'Pct':<8} {'Unique':<8} {'Top Value':<30}")
                output_lines.append("-" * 100)
                for row in report_rows[1:]:  # Skip header row
                    if len(row) >= 7:  # Ensure we have enough columns
                        output_lines.append(f"{row[0]:<25} {row[1]:<15} {row[2]:<8} {row[3]:<8} {row[4]:<8} {row[6]:<30}")
            output_lines.append("")
            output_lines.append("Note: Install prettytable for better formatted output: pip install prettytable")
            output_lines.append("Or use -o filename.csv to save report to CSV file")
            output_lines.append("")
            
            # Use less pager for better viewing experience
            report_str = "\n".join(output_lines)
            try:
                less = subprocess.Popen(["less", "-FMXSR"], stdin=subprocess.PIPE)
                less.stdin.write(report_str.encode("utf-8"))
                less.stdin.close()
                less.wait()
                print()
            except (IOError, FileNotFoundError) as ex:
                # Fallback to print if less is not available
                print(report_str)

    if args.python_file_name:
        code_rows = analyzer.generate("code")
        script_rows = create_python_script(code_rows, args.file_type, args.encoding)
        with open(args.python_file_name, "w") as file:
            file.write("\n".join(script_rows) + "\n")
        print(f"python code saved to {args.python_file_name}\n")

    sys.exit(shut_down)
