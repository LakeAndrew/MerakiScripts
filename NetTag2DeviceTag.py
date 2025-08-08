"""
Created by Andrew Dunsmoor
Solutions Engineer for Cisco Systems
Intention is to provide a basic walk-through of the Meraki API for the purposes of pushing config changes

This scipt copies all NETWORK tags and applies them to ALL DEVICES in that NETWORK

"""

from dotenv import load_dotenv
import meraki
import os
from pprint import pprint  # pprint makes printing lists and dictionaries prettier to read

# MUST CREATE environment.env FILE WITH THE FOLLOWING VARIABLES #
load_dotenv('environment.env')
API_KEY = os.getenv('API_KEY')
# I am setting Org ID based on my own network documentation
organization_id = os.getenv('ORG_ID')

# INITIALIZE DASHBOARD OBJECT
dashboard = meraki.DashboardAPI(API_KEY, print_console=False)
# dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True) # Change to true to stop log outputs

# Uncomment if you need to get your org or network ID.
# Get organizations
# orgs_list = dashboard.organizations.getOrganizations()
# pprint(orgs_list)


# Get a list of all networks : Response object is a list of dictionaries
networks_list = dashboard.organizations.getOrganizationNetworks(
    organization_id, total_pages='all'
)

### TASK ###
# Loop through all networks in networks_list.
# Copy network tags
# Get all devices in network
# Copy existing tags. Combine with network tags. Apply new set of tags.
###


# Loop through list of networks: Each network is a dictionary object
for network in networks_list:  # network is a dictionary object with that network's data
    network_tags = network['tags']  # Extract tags from dictionary
    # print(network_tags)
    network_devices = dashboard.networks.getNetworkDevices(network['id'])  # GET All Devices in the network
    for device in network_devices:  # Loop through each device. Device is a dictionary with that device's data
        device_serial = device['serial']  # Extract serial and device tags
        device_tags = device['tags']
        new_tags = list(set(network_tags + device_tags))  # Combine unique entries in network and device tags
        # Update device tags to match network tags if different
        if set(device_tags) != set(new_tags):  # Check if the device tags already match desired tags list
            print(f"Updating device {device_serial} tags from {device_tags} to {new_tags}")
            # dashboard.devices.updateDevice(device_serial, tags=new_tags)  # APPLY DEVICE TAGS
        else:
            print(f"Device {device_serial} already has matching tags: {device_tags} and {new_tags}")
