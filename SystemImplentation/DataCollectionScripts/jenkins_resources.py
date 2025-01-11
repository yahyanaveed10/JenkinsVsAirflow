import requests
from requests.auth import HTTPBasicAuth

JENKINS_URL = '<jenkins>'
FOLDER_NAME = 'Test_JenkinsVsAirflow'
USERNAME = '<user>'
API_TOKEN = '<pass>'


def get_jenkins_node_info():
    response = requests.get(f"{JENKINS_URL}/computer/api/json", auth=HTTPBasicAuth(USERNAME, API_TOKEN))

    if response.status_code == 200:
        data = response.json()
        node_info = []

        for computer in data.get('computer', []):
            info = {
                'displayName': computer.get('displayName', 'N/A'),
                'numExecutors': computer.get('numExecutors', 'N/A'),
                'idle': computer.get('idle', 'N/A'),
                'monitorData': computer.get('monitorData', {}),
                'currentBuilds': []  # Initialize list to store current build details
            }

            # Initialize memory variables
            info['availablePhysicalMemory'] = 'N/A'
            info['totalPhysicalMemory'] = 'N/A'
            info['availableDiskSpace'] = 'N/A'
            info['totalDiskSpace'] = 'N/A'
            info['availableTempSpace'] = 'N/A'
            info['totalTempSpace'] = 'N/A'
            info['architecture'] = 'N/A'
            info['averageResponseTime'] = 'N/A'

            # Check for SwapSpaceMonitor data
            swap_monitor = info['monitorData'].get('hudson.node_monitors.SwapSpaceMonitor')
            if swap_monitor:
                info['availablePhysicalMemory'] = swap_monitor.get('availablePhysicalMemory', 'N/A')
                info['totalPhysicalMemory'] = swap_monitor.get('totalPhysicalMemory', 'N/A')

            # Check for DiskSpaceMonitor data
            disk_monitor = info['monitorData'].get('hudson.node_monitors.DiskSpaceMonitor')
            if disk_monitor:
                info['availableDiskSpace'] = disk_monitor.get('size', 'N/A')
                info['totalDiskSpace'] = disk_monitor.get('totalSize', 'N/A')

            # Check for TemporarySpaceMonitor data
            temp_monitor = info['monitorData'].get('hudson.node_monitors.TemporarySpaceMonitor')
            if temp_monitor:
                info['availableTempSpace'] = temp_monitor.get('size', 'N/A')
                info['totalTempSpace'] = temp_monitor.get('totalSize', 'N/A')

            # Check for ArchitectureMonitor data
            architecture_monitor = info['monitorData'].get('hudson.node_monitors.ArchitectureMonitor')
            if architecture_monitor:
                info['architecture'] = architecture_monitor

            # Check for ResponseTimeMonitor data
            response_time_monitor = info['monitorData'].get('hudson.node_monitors.ResponseTimeMonitor')
            if response_time_monitor:
                info['averageResponseTime'] = response_time_monitor.get('average', 'N/A')

            # Get current builds on each executor
            for executor in computer.get('executors', []):
                current_executable = executor.get('currentExecutable')
                if current_executable:
                    build_info = {
                        'jobName': current_executable.get('fullDisplayName', 'N/A'),
                        'url': current_executable.get('url', 'N/A'),
                        'buildNumber': current_executable.get('number', 'N/A'),
                    }
                    info['currentBuilds'].append(build_info)

            node_info.append(info)

        return node_info
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

if __name__ == '__main__':
    nodes = get_jenkins_node_info()
    if nodes is not None:
        for node in nodes:
            print(f"Node Name: {node['displayName']}")
            print(f"Number of Executors: {node['numExecutors']}")
            print(f"Idle: {node['idle']}")
            print(f"Available Physical Memory: {node['availablePhysicalMemory']}")
            print(f"Total Physical Memory: {node['totalPhysicalMemory']}")
            print(f"Available Disk Space: {node['availableDiskSpace']}")
            print(f"Total Disk Space: {node['totalDiskSpace']}")
            print(f"Available Temporary Space: {node['availableTempSpace']}")
            print(f"Total Temporary Space: {node['totalTempSpace']}")
            print(f"Architecture: {node['architecture']}")
            print(f"Average Response Time: {node['averageResponseTime']}")
            print("Current Builds:")
            for build in node['currentBuilds']:
                print(f"  - Job Name: {build['jobName']}")
                print(f"    URL: {build['url']}")
                print(f"    Build Number: {build['buildNumber']}")
            print('-' * 30)