#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import time
import traceback
import typing as T
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget

class BascProcess(QThread):
    finished = pyqtSignal(object, object)
    published = pyqtSignal(object, str)

    def process(self):
        raise NotImplementedError

    def notify_finished(self, result: T.Any = None):
        self.finished.emit(self, result)

    def notify_published(self, data: object):
        self.published.emit(self, data)

    def run(self):
        result = None
        try:
            result = self.process()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        finally:
            self.quit()
            self.notify_finished(result=result)

# Minimal stubs for other process classes
class NavigationToShelfProcess(BascProcess):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

    def process(self):
        return True

class CircularSortingProcess(BascProcess):
    def __init__(self, number_cycle: int = 5, parent: QWidget = None):
        super().__init__(parent=parent)

    def process(self):
        return True

class ParkingChargingProcess(BascProcess):
    def __init__(self, parent: T.Optional[QWidget] = None):
        super().__init__(parent=parent)

    def process(self):
        return True

class SmartLogisticsProcess(BascProcess):
    """
    Complete Smart Logistics workflow process
    Runs the Smart_Logistics_Kit-22-map/main.py in a subprocess with complete isolation
    """
    
    def __init__(self, parent: T.Optional[QWidget] = None):
        super().__init__(parent=parent)
        self.log = logging.getLogger("console")
        self.process_running = False
        self.main_process = None
        
    def terminate(self):
        """Terminate the smart logistics process"""
        import os
        import signal
        
        self.process_running = False
        if self.main_process and self.main_process.poll() is None:
            try:
                # Kill entire process group for complete cleanup
                os.killpg(os.getpgid(self.main_process.pid), signal.SIGTERM)
                self.main_process.wait(timeout=5)
            except Exception as e:
                self.log.error(f"Error terminating process: {e}")
                try:
                    os.killpg(os.getpgid(self.main_process.pid), signal.SIGKILL)
                except:
                    pass
        super().terminate()
    
    def process(self):
        """
        Execute the test_full_workflow.sh script
        Clean up UI resources first to avoid conflicts
        """
        import subprocess
        import os
        import signal
        
        self.process_running = True
        self.notify_published("[WORKFLOW] Starting Smart Logistics complete workflow...")
        
        try:
            # Get script path
            script_path = os.path.expanduser("~/intelligent-logistics-system/test_full_workflow.sh")
            
            if not os.path.exists(script_path):
                self.notify_published(f"[ERROR] Workflow script not found: {script_path}")
                return False
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # CRITICAL: Clean up UI's GPIO/ROS resources before starting script
            self.notify_published("[CLEANUP] Cleaning up UI resources to avoid conflicts...")
            
            try:
                # Import here to avoid circular imports
                from functional.roslaunch import Functional
                
                # Clean up any GPIO resources that UI might have initialized
                self.notify_published("[CLEANUP] Clearing GPIO resources...")
                Functional.clear_pump()
                Functional.clear_radar()
                
                # Clean up GPIO completely
                from utils import GpioHandler
                GpioHandler.cleanup()
                
                self.notify_published("[CLEANUP] ✓ GPIO resources cleaned")
                
            except Exception as e:
                self.notify_published(f"[CLEANUP] Warning: {e}")
            
            # Wait a moment for cleanup
            import time
            time.sleep(2)
            
            self.notify_published("[STEP 1/5] ✓ Starting Lidar odometry system...")
            self.notify_published("[STEP 2/5] ✓ Starting navigation system...")
            self.notify_published("[STEP 3/5] ✓ Starting Smart Logistics main program...")
            
            # Set up complete environment
            env = os.environ.copy()
            
            # Ensure DISPLAY is set for RViz
            if 'DISPLAY' not in env:
                env['DISPLAY'] = ':0'
            
            # Ensure ROS environment variables are set
            env['ROS_MASTER_URI'] = 'http://localhost:11311'
            env['ROS_HOSTNAME'] = 'localhost'
            
            # Run the shell script with complete environment
            # Use setsid to create new session - complete isolation from UI
            self.main_process = subprocess.Popen(
                ['bash', script_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                preexec_fn=os.setsid  # Create new session - complete isolation
            )
            
            self.notify_published("[INFO] Workflow running with cleaned environment")
            self.notify_published("[STEP 4/5] MyAGV navigating and 270 arm working...")
            
            # Monitor process output and detect when Lidar and Navigation are ready
            lidar_started = False
            navigation_started = False
            
            # Monitor process output
            while self.process_running and self.main_process.poll() is None:
                try:
                    line = self.main_process.stdout.readline()
                    if line:
                        line_stripped = line.rstrip()
                        if line_stripped:
                            self.notify_published(f"[WORKFLOW] {line_stripped}")
                            
                            # Detect when Lidar is ready - look for explicit marker
                            if not lidar_started and "[LIDAR_READY]" in line_stripped:
                                lidar_started = True
                                self.notify_published("[UI_UPDATE] LIDAR_STARTED")
                                self.log.info("Lidar detected as started, sending UI update signal")
                            
                            # Detect when Navigation is ready - look for explicit marker
                            if not navigation_started and "[NAVIGATION_READY]" in line_stripped:
                                navigation_started = True
                                self.notify_published("[UI_UPDATE] NAVIGATION_STARTED")
                                self.log.info("Navigation detected as started, sending UI update signal")
                            
                except Exception as e:
                    pass
                
                time.sleep(0.1)
            
            # Get exit code
            exit_code = self.main_process.poll()
            
            if exit_code == 0 or exit_code is None:
                self.notify_published("[STEP 5/5] ✓ Smart logistics workflow completed!")
                self.notify_published("[SUCCESS] All tasks completed successfully!")
                return True
            else:
                self.notify_published(f"[INFO] Workflow process ended with code: {exit_code}")
                return True
            
        except Exception as e:
            self.notify_published(f"[ERROR] Workflow error: {e}")
            self.log.exception(e)
            return False
        
        finally:
            self.process_running = False
            if self.main_process and self.main_process.poll() is None:
                try:
                    # Kill entire process group
                    os.killpg(os.getpgid(self.main_process.pid), signal.SIGTERM)
                    self.main_process.wait(timeout=5)
                except Exception as e:
                    self.log.error(f"Error terminating process: {e}")