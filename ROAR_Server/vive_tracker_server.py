import sys
from pathlib import Path
import os

print(Path(os.getcwd()).parent.parent.as_posix())
sys.path.append(Path(os.getcwd()).parent.parent.as_posix())

import socketserver
from typing import Any, Optional, Dict
from ROAR_Jetson.vive.triad_openvr import TriadOpenVR
import logging
from ROAR_Jetson.vive.models import ViveTrackerMessage
import json
from pprint import pprint
from ROAR_Desktop.ROAR_Server.base_server import ROARServer


class ViveTrackerServer(ROARServer):
    def __init__(self, host: str, port: int, record_data: bool = False,
                 output_file_path: Path = Path("./data/RFS_track.txt")):
        super().__init__(host, port)
        self.triad_openvr: Optional[TriadOpenVR] = self.reconnect_triad_vr(debug=True)
        self.record_data = record_data
        self.output_file_path = output_file_path
        self.output_file = None
        if record_data and self.output_file_path.exists() is False:
            self.output_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_file_path.open('w')

    def run(self):
        while True:
            for tracker_name in self.get_tracker_names():
                message = self.poll(tracker_name)
                self.logger.info(message)
                if message is not None:
                    socket_message = self.construct_socket_msg(message)
                    self.socket.sendto(socket_message.encode(), (self.host, self.port))
                    if self.record_data:
                        self.record(message)

    def poll(self, tracker_name) -> Optional[ViveTrackerMessage]:
        tracker = self.get_tracker(tracker_name=tracker_name)
        if tracker is not None:
            message: Optional[ViveTrackerMessage] = self.create_tracker_message(tracker=tracker,
                                                                                tracker_name=tracker_name)
            return message
        else:
            self.reconnect_triad_vr()
        return None

    def get_tracker(self, tracker_name):
        return self.triad_openvr.devices.get(tracker_name, None)

    def create_tracker_message(self, tracker, tracker_name):
        try:
            euler = tracker.get_pose_euler()
            vel_x, vel_y, vel_z = tracker.get_velocity()
            x, y, z, yaw, pitch, roll = euler
            message = ViveTrackerMessage(valid=True, x=-x, y=y, z=-z,
                                         yaw=yaw, pitch=pitch, roll=roll,
                                         vel_x=vel_x, vel_y=vel_y, vel_z=vel_z,
                                         device_name=tracker_name)
            return message
        except OSError as e:
            print(f"OSError: {e}. Need to restart Vive Tracker Server")
            self.reconnect_triad_vr()
        except Exception as e:
            print(f"Cannot find Tracker {tracker} is either offline or malfunctioned")
            self.reconnect_triad_vr()
            return None

    def construct_socket_msg(self, data: ViveTrackerMessage) -> str:
        json_data = json.dumps(data.json(), sort_keys=False)
        json_data = "&" + json_data
        json_data = json_data + "\r"  # * (512 - len(json_data))
        return json_data

    def reconnect_triad_vr(self, debug=False):
        from ROAR_Jetson.vive.triad_openvr import TriadOpenVR
        openvr = TriadOpenVR()
        if debug:
            self.logger.debug(
                f"Trying to reconnect to OpenVR to refresh devices. "
                f"Devices online:")
            pprint(openvr.devices)
        self.triad_openvr = openvr
        return openvr

    def get_tracker_names(self):
        result = []
        for device_name in self.triad_openvr.devices.keys():
            if "tracker" in device_name:
                result.append(device_name)
        return result

    def record(self, data: ViveTrackerMessage):
        x, y, z, roll, pitch, yaw = data.x, data.y, data.z, data.roll, data.pitch, data.yaw

        recording_data = f"{x/10000}, {y/10000},{z/10000},{roll},{pitch},{yaw}"
        m = f"Recording: {recording_data}"
        self.logger.info(m)
        self.output_file.write(recording_data+"\n")


if __name__ == "__main__":
    HOST, PORT = "192.168.1.19", 8000
    vive_tracker_server = ViveTrackerServer(host=HOST, port=PORT, record_data=False)
    logging.basicConfig(format='%(asctime)s - %(name)s '
                               '- %(levelname)s - %(message)s', level=logging.INFO)
    vive_tracker_server.run()
