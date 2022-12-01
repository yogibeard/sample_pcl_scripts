#! /usr/bin/env python3.7

"""
ONTAP 9.7 REST API Python Client Library Scripts
uthor: Vish Hulikal
This script performs the following:
        - Create a volume
        - List all volumes
        - Move a volume to another aggregate
        - Resize a volume to a new (bigger) size
        - Delete a volume

usage: python3.7 volume.py [-h] -c CLUSTER -v VOLUME_NAME -vs VSERVER_NAME -a AGGR_NAME -ma MOVE_AGGR_NAME
               -rs VOLUME_RESIZE -s VOLUME_SIZE [-u API_USER] [-p API_PASS]
The following arguments are required: -c/--cluster, -v/--volume_name, -vs/--vserver_name,
                -a/--aggr_name, -ma/--move_aggr_name, -rs/--volume_resize, -s/--volume_size
"""

import argparse
from getpass import getpass
import logging

from netapp_ontap import config, HostConnection, NetAppRestError
from netapp_ontap.resources import Qtree, QuotaRule

def create_qtree(volume_name: str, vserver_name: str, qtree_name: str ) -> None:
    """Creates a new qtree in a volume of a SVM"""

    data = {
        'name': qtree_name,
        'volume': { 'name': volume_name},
        'svm': {'name': vserver_name},
        'security_style': 'unix',
        'unix_permissions': 744,
        'export_policy.name': 'default',
        'qos_policy': {"max_throughput_iops": 1000}
    }

    qtree = Qtree(**data)

    try:
        qtree.post()
        print("Qtree %s created successfully" % qtree.name)
    except NetAppRestError as err:
        print("Error: Qtree was not created: %s" % err)
    return

def create_quota_policy_rule(volume_name: str, vserver_name: str, qtree_name: str, type: str, space_hard: int, files_hard: int) -> None:
    """Create a Quota Policy Rule """

    data = {
        'volume': {'name': volume_name},
        'svm': {'name': vserver_name},
        'qtree': {'name': qtree_name},
        'type': type,
        'space': {'hard_limit': space_hard},
        'files': {'hard_limit': files_hard}
    }
    quotarule = QuotaRule(**data)

    try:
        quotarule.post()

    except NetAppRestError as err:
        print("Error: Quota Rule was not created: %s" % err)
    return

def parse_args() -> argparse.Namespace:
    """Parse the command line arguments from the user"""

    parser = argparse.ArgumentParser(
        description="This script will create a new qtree."
    )
    parser.add_argument(
        "-c", "--cluster", required=True, help="API server IP:port details"
    )
    parser.add_argument(
        "-v", "--volume_name", required=True, help="Volume to create or clone from"
    )
    parser.add_argument(
        "-vs", "--vserver_name", required=True, help="SVM to create the volume from"
    )
    parser.add_argument(
        "-q", "--qtree_name", required=True, help="Qtree to create"
    )
    parser.add_argument(
        "-sh", "--space_hard", required=True, help="Hard limit for qtree space"
    )
    parser.add_argument(
        "-fh", "--files_hard", required=True, help="Hard limit for qtree number of files"
    )
    parser.add_argument("-u", "--api_user", default="admin", help="API Username")
    parser.add_argument("-p", "--api_pass", help="API Password")
    parsed_args = parser.parse_args()

    # collect the password without echo if not already provided
    if not parsed_args.api_pass:
        parsed_args.api_pass = getpass()

    return parsed_args


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)5s] [%(module)s:%(lineno)s] %(message)s",
    )
    args = parse_args()
    config.CONNECTION = HostConnection(
        args.cluster, username=args.api_user, password=args.api_pass, verify=False,
    )

    # Create a Qtree
    create_qtree(args.volume_name, args.vserver_name, args.qtree_name )
    
    # Create a Quota Policy Rule
    create_quota_policy_rule(args.volume_name, args.vserver_name, args.qtree_name, 'tree', args.space_hard, args.files_hard)

