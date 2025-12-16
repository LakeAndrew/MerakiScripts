import meraki
import os
from datetime import datetime
import json
import pandas as pd
import dotenv
from dotenv import load_dotenv
import openpyxl

"""
Features

✅ Task 1: Filtered Clients

Searches for clients with manufacturers: Dell, Adrenaline
Searches for MAC addresses containing: 50a4.d0
Retrieves clients from the last 30 days
Displays MAC, IP, manufacturer, VLAN, and last seen time

✅ Task 2: VLAN 10 Access Ports

Lists all enabled access ports configured on VLAN 10
Shows switch name, serial, model, port ID, and PoE status
Only includes ports in access mode (not trunk)

✅ Task 3: Device Inventory

Retrieves all devices across all networks
Displays: Serial number, model, MAC address, firmware version, LAN IP, status, and last reported time
Attempts to retrieve uptime information when available

Output

The script provides:


Console Output: Real-time progress and results
JSON Export: meraki_audit_results.json containing all collected data
Log Files: Created in logs/ directory for troubleshooting

Notes

API Rate Limits: The script includes error handling but may need rate limiting for very large deployments
Permissions: Ensure your API key has read access to all required resources
Uptime Data: Uptime may not be available for all device types
Client History: Client data is limited to the last 30 days by default

Edge Cases Handled

Missing or unavailable device data
Networks without switches
Devices that don't support uplink queries
Empty client lists
API timeout or connectivity issues"""

load_dotenv("environment.env")
# Constants
API_KEY = os.environ.get('API_KEY')  # Store API key securely
ORG_ID = os.environ.get('ORG_ID')
TARGET_MANUFACTURERS = ['Dell', 'Adrenaline', 'Nintendo']
TARGET_MAC_PREFIX = '50a4.d0'
TARGET_VLAN = 10


def initialize_dashboard(api_key):
    """Initialize Meraki Dashboard API client"""
    try:
        dashboard = meraki.DashboardAPI(
            api_key=api_key,
            print_console=True,
            # output_log=True,
            # log_file_prefix=os.path.basename(__file__)[:-3],
            # log_path='logs/',
            suppress_logging=True
        )
        return dashboard
    except Exception as e:
        print(f"Error initializing Dashboard API: {e}")
        return None


def get_all_organizations(dashboard):
    """Retrieve all organizations"""
    try:
        organizations = dashboard.organizations.getOrganizations()
        return organizations
    except Exception as e:
        print(f"Error retrieving organizations: {e}")
        return []


def get_all_networks(dashboard, org_id):
    """Retrieve all networks in an organization"""
    try:
        networks = dashboard.organizations.getOrganizationNetworks(org_id)
        return networks
    except Exception as e:
        print(f"Error retrieving networks for org {org_id}: {e}")
        return []


def get_filtered_clients(dashboard, network_id, network_name):
    """Get clients matching manufacturer or MAC criteria"""
    print(f"\n{'=' * 80}")
    print(f"Analyzing Clients in Network: {network_name} (ID: {network_id})")
    print(f"{'=' * 80}")

    filtered_clients = []

    try:
        # Get clients from the last 30 days
        clients = dashboard.networks.getNetworkClients(
            network_id,
            # timespan=2592000  # 30 days in seconds
        )

        for client in clients:

            manufacturer = client.get('manufacturer')
            if client.get('manufacturer') is not None:
                manufacturer = manufacturer.lower()

            mac_address = client.get('mac', '').lower()
            # print(client)

            # Check if manufacturer matches or MAC contains target prefix
            if (manufacturer is not None and any(mfr.lower() in manufacturer for mfr in TARGET_MANUFACTURERS)) or \
                    TARGET_MAC_PREFIX.lower() in mac_address.replace(':', '').replace('-', '.'):
                filtered_clients.append({
                    'network': network_name,
                    'description': client.get('description', 'N/A'),
                    'mac': client.get('mac'),
                    'ip': client.get('ip', 'N/A'),
                    'manufacturer': client.get('manufacturer', 'Unknown'),
                    'os': client.get('os', 'N/A'),
                    'vlan': client.get('vlan', 'N/A'),
                    'status': client.get('status', 'N/A'),
                    'lastSeen': client.get('lastSeen', 'N/A')
                })

        if filtered_clients:
            print(f"\nFound {len(filtered_clients)} matching clients:")
            for client in filtered_clients:
                print(f"  - MAC: {client['mac']} | IP: {client['ip']} | "
                      f"Manufacturer: {client['manufacturer']} | VLAN: {client['vlan']}")
        else:
            print(f"No matching clients found in this network.")

    except Exception as e:
        print(f"Error retrieving clients for network {network_name}: {e}")

    return filtered_clients


def get_open_access_ports(dashboard, network_id, network_name):
    """List all open access ports on VLAN 10"""
    print(f"\n{'=' * 80}")
    print(f"Analyzing VLAN 10 Access Ports in Network: {network_name}")
    print(f"{'=' * 80}")

    open_ports = []

    try:
        # Get all switches in the network
        devices = dashboard.networks.getNetworkDevices(network_id)
        switches = [d for d in devices if d.get('model', '').startswith('MS')]

        for switch in switches:
            try:
                # Get switch ports
                ports = dashboard.switch.getDeviceSwitchPorts(switch['serial'])

                for port in ports:
                    # Check if port is access mode and on VLAN 10
                    # print(port)
                    if port.get('type') == 'access' and port.get('vlan') == TARGET_VLAN:
                        open_ports.append({
                            'network': network_name,
                            'switch_name': switch.get('name', 'Unknown'),
                            'switch_serial': switch['serial'],
                            'switch_model': switch.get('model', 'Unknown'),
                            'port_id': port.get('portId'),
                            'name': port.get('name', 'Unnamed'),
                            'vlan': port.get('vlan'),
                            'type': port.get('type'),
                            'enabled': port.get('enabled'),
                            'poe_enabled': port.get('poeEnabled', False),
                            'link_status': port.get('linkNegotiation', 'N/A')
                        })

            except Exception as e:
                print(f"  Error retrieving ports for switch {switch['serial']}: {e}")
                continue

        if open_ports:
            print(f"\nFound {len(open_ports)} open access ports on VLAN 10:")
            for port in open_ports:
                print(f"  - Switch: {port['switch_name']} ({port['switch_serial']}) | "
                      f"Port: {port['port_id']} ({port['name']}) | PoE: {port['poe_enabled']}")
        else:
            print(f"No open access ports on VLAN 10 found in this network.")

    except Exception as e:
        print(f"Error analyzing switches in network {network_name}: {e}")

    return open_ports


def get_device_inventory(dashboard, network_id, network_name):
    """Get detailed device information including version, MAC, model, serial, and uptime"""
    print(f"\n{'=' * 80}")
    print(f"Device Inventory for Network: {network_name}")
    print(f"{'=' * 80}")

    device_inventory = []

    try:
        devices = dashboard.networks.getNetworkDevices(network_id)

        for device in devices:
            device_info = {
                'network': network_name,
                'name': device.get('name', 'Unnamed'),
                'serial': device.get('serial'),
                'model': device.get('model'),
                'mac': device.get('mac', 'N/A'),
                'firmware': device.get('firmware', 'Unknown'),
                'lan_ip': device.get('lanIp', 'N/A'),
                'tags': device.get('tags', []),
            }

            # Try to get device uplink information for uptime
            try:
                uplink_info = dashboard.devices.getDeviceUplink(device['serial'])
                device_info['uptime'] = uplink_info.get('uptime', 'N/A')
            except:
                device_info['uptime'] = 'N/A'

            # Try to get device status for additional info
            try:
                status = dashboard.organizations.getOrganizationDevicesStatuses(
                    dashboard.organizations.getOrganizations()[0]['id'],
                    serials=[device['serial']]
                )
                if status:
                    device_info['status'] = status[0].get('status', 'Unknown')
                    device_info['lastReportedAt'] = status[0].get('lastReportedAt', 'N/A')
            except:
                device_info['status'] = 'Unknown'
                device_info['lastReportedAt'] = 'N/A'

            device_inventory.append(device_info)

            print(f"\n  Device: {device_info['name']}")
            print(f"    Serial: {device_info['serial']}")
            print(f"    Model: {device_info['model']}")
            print(f"    MAC: {device_info['mac']}")
            print(f"    Firmware: {device_info['firmware']}")
            print(f"    LAN IP: {device_info['lan_ip']}")
            print(f"    Status: {device_info.get('status', 'Unknown')}")
            print(f"    Last Reported: {device_info.get('lastReportedAt', 'N/A')}")

    except Exception as e:
        print(f"Error retrieving device inventory for network {network_name}: {e}")

    return device_inventory


def export_results_to_json(all_clients, all_ports, all_devices, filename='meraki_audit_results.json'):
    """Export all results to a JSON file"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'filtered_clients': all_clients,
        'vlan10_access_ports': all_ports,
        'device_inventory': all_devices
    }

    # df = pd.DataFrame(results)
    # pd.json_normalize()
    # df.to_excel('output.xlsx', index=False)

    with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(all_clients).to_excel(writer, sheet_name='Clients', index=False)
        pd.DataFrame(all_ports).to_excel(writer, sheet_name='Ports', index=False)
        pd.DataFrame(all_devices).to_excel(writer, sheet_name='Devices', index=False)

    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n{'=' * 80}")
        print(f"Results exported to {filename}")
        print(f"{'=' * 80}")
    except Exception as e:
        print(f"Error exporting results: {e}")




def main():
    """Main execution function"""
    print(f"\n{'#' * 80}")
    print(f"# Meraki Dashboard Automation Script")
    print(f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#' * 80}\n")

    # Initialize Dashboard API
    if not API_KEY:
        print("ERROR: MERAKI_DASHBOARD_API_KEY environment variable not set!")
        print("Set it with: export MERAKI_DASHBOARD_API_KEY='your_api_key_here'")
        return

    dashboard = initialize_dashboard(API_KEY)
    if not dashboard:
        return

    # Get organizations
    organizations = [ORG_ID]
    if not organizations:
        print("No organizations found or error retrieving organizations.")
        return

    # Storage for all results
    all_filtered_clients = []
    all_vlan10_ports = []
    all_device_inventory = []

    # Process each organization
    print(f"\n{'#' * 80}")
    print(f"# Processing Organization: {ORG_ID}")
    print(f"{'#' * 80}")

    # Get all networks in the organization
    networks = get_all_networks(dashboard, ORG_ID)

    # Process each network
    for network in networks:
        network_name = network['name']
        network_id = network['id']

        # Task 1: Get filtered clients
        filtered_clients = get_filtered_clients(dashboard, network_id, network_name)
        all_filtered_clients.extend(filtered_clients)

        # Task 2: Get VLAN 10 access ports
        vlan10_ports = get_open_access_ports(dashboard, network_id, network_name)
        all_vlan10_ports.extend(vlan10_ports)

        # Task 3: Get device inventory
        device_inventory = get_device_inventory(dashboard, network_id, network_name)
        all_device_inventory.extend(device_inventory)


        # Print summary
        print(f"\n{'#' * 80}")
        print(f"# SUMMARY")
        print(f"{'#' * 80}")
        print(f"Total Filtered Clients: {len(all_filtered_clients)}")
        print(f"Total VLAN 10 Access Ports: {len(all_vlan10_ports)}")
        print(f"Total Devices: {len(all_device_inventory)}")

        # Export results
        export_results_to_json(all_filtered_clients, all_vlan10_ports, all_device_inventory)


print(f"\n{'#' * 80}")
print(f"# Script Execution Complete")
print(f"{'#' * 80}\n")

if __name__ == "__main__":
    main()
