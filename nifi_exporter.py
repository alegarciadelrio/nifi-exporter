#!/usr/bin/env python3
import time
import json
import requests
import os
import http.server
import threading
from prometheus_client import Gauge, REGISTRY
from prometheus_client.exposition import MetricsHandler

# Custom HTTP handler to serve index.html at the root URL
class NifiExporterHandler(MetricsHandler):
    def do_GET(self):
        if self.path == '/':
            # Serve the index.html file
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'rb') as file:
                self.wfile.write(file.read())
        else:
            # Let the MetricsHandler handle other paths (like /metrics)
            super().do_GET()

# Define metrics
class NifiCollector:
    def __init__(self, nifi_url):
        self.nifi_url = nifi_url
        self.controller_api_endpoint = f"{nifi_url}/nifi-api/flow/status"
        self.process_group_api_endpoint = f"{nifi_url}/nifi-api/flow/process-groups/root/status"
        
        # Controller metrics
        self.active_thread_count = Gauge('nifi_active_thread_count', 'Number of active threads in NiFi')
        self.terminated_thread_count = Gauge('nifi_terminated_thread_count', 'Number of terminated threads in NiFi')
        self.files_queued = Gauge('nifi_files_queued', 'Number of flow files queued in NiFi')
        self.bytes_queued = Gauge('nifi_bytes_queued', 'Number of bytes queued in NiFi')
        self.running_count = Gauge('nifi_running_count', 'Number of running components in NiFi')
        self.stopped_count = Gauge('nifi_stopped_count', 'Number of stopped components in NiFi')
        self.invalid_count = Gauge('nifi_invalid_count', 'Number of invalid components in NiFi')
        self.disabled_count = Gauge('nifi_disabled_count', 'Number of disabled components in NiFi')
        self.active_remote_port_count = Gauge('nifi_active_remote_port_count', 'Number of active remote ports in NiFi')
        self.inactive_remote_port_count = Gauge('nifi_inactive_remote_port_count', 'Number of inactive remote ports in NiFi')
        self.up_to_date_count = Gauge('nifi_up_to_date_count', 'Number of up-to-date components in NiFi')
        self.locally_modified_count = Gauge('nifi_locally_modified_count', 'Number of locally modified components in NiFi')
        self.stale_count = Gauge('nifi_stale_count', 'Number of stale components in NiFi')
        self.locally_modified_and_stale_count = Gauge('nifi_locally_modified_and_stale_count', 'Number of locally modified and stale components in NiFi')
        self.sync_failure_count = Gauge('nifi_sync_failure_count', 'Number of sync failure components in NiFi')
        
        # Process Group metrics (only the ones requested by the user)
        self.pg_flowfiles_received = Gauge('nifi_process_group_flowfiles_received', 'Number of flowfiles received by the process group')
        self.pg_flowfiles_sent = Gauge('nifi_process_group_flowfiles_sent', 'Number of flowfiles sent by the process group')
        self.pg_flowfiles_queued = Gauge('nifi_process_group_flowfiles_queued', 'Number of flowfiles queued in the process group')
        
        # API health metrics
        self.api_up = Gauge('nifi_api_up', 'Whether the NiFi API is up (1) or down (0)')

    def collect(self):
        """Collect metrics from NiFi API"""
        try:
            # Collect controller metrics
            self._collect_controller_metrics()
            
            # Collect process group metrics
            self._collect_process_group_metrics()
            
            # Set API up status
            self.api_up.set(1)
            
        except Exception as e:
            self.api_up.set(0)
            print(f"Error collecting metrics: {e}")
    
    def _collect_controller_metrics(self):
        """Collect metrics from the controller status endpoint"""
        response = requests.get(self.controller_api_endpoint, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        controller_status = data.get('controllerStatus', {})
        
        # Update controller metrics
        self.active_thread_count.set(controller_status.get('activeThreadCount', 0))
        self.terminated_thread_count.set(controller_status.get('terminatedThreadCount', 0))
        self.files_queued.set(controller_status.get('flowFilesQueued', 0))
        self.bytes_queued.set(controller_status.get('bytesQueued', 0))
        self.running_count.set(controller_status.get('runningCount', 0))
        self.stopped_count.set(controller_status.get('stoppedCount', 0))
        self.invalid_count.set(controller_status.get('invalidCount', 0))
        self.disabled_count.set(controller_status.get('disabledCount', 0))
        self.active_remote_port_count.set(controller_status.get('activeRemotePortCount', 0))
        self.inactive_remote_port_count.set(controller_status.get('inactiveRemotePortCount', 0))
        self.up_to_date_count.set(controller_status.get('upToDateCount', 0))
        self.locally_modified_count.set(controller_status.get('locallyModifiedCount', 0))
        self.stale_count.set(controller_status.get('staleCount', 0))
        self.locally_modified_and_stale_count.set(controller_status.get('locallyModifiedAndStaleCount', 0))
        self.sync_failure_count.set(controller_status.get('syncFailureCount', 0))
    
    def _collect_process_group_metrics(self):
        """Collect metrics from the process group status endpoint"""
        response = requests.get(self.process_group_api_endpoint, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        process_group_status = data.get('processGroupStatus', {})
        
        # Get the aggregate snapshot
        snapshot = process_group_status.get('aggregateSnapshot', {})
        
        # Update only the requested process group metrics
        self.pg_flowfiles_received.set(snapshot.get('flowFilesReceived', 0))
        self.pg_flowfiles_sent.set(snapshot.get('flowFilesSent', 0))
        self.pg_flowfiles_queued.set(snapshot.get('flowFilesQueued', 0))


def start_http_server_with_index(port, addr=''):
    """Start an HTTP server with a custom handler that serves index.html at the root URL"""
    server_address = (addr, port)
    httpd = http.server.HTTPServer(server_address, NifiExporterHandler)
    httpd.daemon = True
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()


def main():
    # Get NiFi URL from environment variable or use default
    nifi_url = os.environ.get("NIFI_URL", "http://nifi-hostname:8080")
    
    # Start HTTP server with custom handler
    start_http_server_with_index(9100)
    print(f"Server started on port 9100")
    print(f"Collecting metrics from {nifi_url}")
    
    # Initialize collector
    collector = NifiCollector(nifi_url)
    
    # Collect metrics periodically
    while True:
        collector.collect()
        time.sleep(5)  # Collect every 5 seconds


if __name__ == "__main__":
    main()
