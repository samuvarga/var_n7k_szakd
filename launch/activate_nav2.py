#!/usr/bin/env python3
import subprocess
import sys
import time

def main():
    # Wait for nodes to initialize
    time.sleep(6)
    
    nodes_to_activate = [
        ('/planner_server', 'planner_server'),
        ('/controller_server', 'controller_server'),
        ('/bt_navigator', 'bt_navigator'),
    ]
    
    for node_path, node_name in nodes_to_activate:
        try:
            print(f"\n[{node_name}] Configuring...")
            subprocess.run([
                'ros2', 'lifecycle', 'set', node_path, 'configure'
            ], check=True)
            time.sleep(1)
            
            print(f"[{node_name}] Activating...")
            subprocess.run([
                'ros2', 'lifecycle', 'set', node_path, 'activate'
            ], check=True)
            time.sleep(1)
        except subprocess.CalledProcessError as e:
            print(f"[{node_name}] Error: {e}", file=sys.stderr)
    
    print("\n✓ All Nav2 nodes activated!")

if __name__ == '__main__':
    main()
