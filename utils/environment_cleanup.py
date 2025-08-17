#! /usr/bin/env python3
# Copyright 2025-present National University of Singapore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

def check_exercise_folder(exercise_folder):
    if not os.path.isdir(exercise_folder):
        print(f"Error: The folder '{exercise_folder}' does not exist.")
        sys.exit(1)
    try:
        folders = [f for f in os.listdir(exercise_folder) if os.path.isdir(os.path.join(exercise_folder, f))]
    except Exception as e:
        print(f"Error accessing the folder '{exercise_folder}': {e}")
        sys.exit(1)
    exercise_names = [folder.split('-')[1] for folder in folders if '-' in folder]
    return exercise_names

def delete_ovs_bridges():
    try:
        bridges = os.popen("ovs-vsctl list-br").read().strip().split('\n')
        for bridge in bridges:
            if bridge:
                os.system(f"sudo ovs-vsctl --if-exists del-br {bridge}")
    except Exception as e:
        print(f"Error deleting OVS bridges: {e}")

if __name__ == "__main__":
    exercise_folder = "../"
    exercise_names = check_exercise_folder(exercise_folder)

    if exercise_names:
        for name in exercise_names:
            os.system(f"sudo pkill --signal SIGKILL -f {name}")
        print("All DPDK processes killed.")
    delete_ovs_bridges()
    print("All OVS bridges deleted.")