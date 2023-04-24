import argparse
import datetime
import json
import platform
import subprocess
from pathlib import Path
from typing import Dict

import pandas as pd
import plotly.express as px
from nicegui import ui
from nicegui.elements.plotly import Plotly


class Dashboard:

    def __init__(self, addresses: Dict[str, str] = None, update_frequency: float = 60., log_directory: Path = None):
        if log_directory is None:
            log_directory = Path.home() / "server_states"
            log_directory.mkdir(parents=True, exist_ok=True)

        if addresses is None:
            addresses_file = log_directory / "addresses.json"
            if not addresses_file.exists():
                addresses = dict(localhost="127.0.0.1", google="google.com")
                with addresses_file.open("w") as file:
                    json.dump(addresses, file)
            else:
                with addresses_file.open("r") as file:
                    addresses = json.load(file)

        self.addresses = addresses
        self.start_time = datetime.datetime.now()
        self._log_files = dict()
        self._df_files = dict()

        for name in addresses.keys():
            log_file = log_directory / f"{name}-downtimes.txt"
            df_file = log_directory / f"{name}-data.csv"
            if not log_file.exists():
                log_file.touch()
            self._log_files[name] = log_file
            self._df_files[name] = df_file

        with ui.header().classes(replace='row items-center') as header:
            ui.label(f'Server State Check Dashboard')

        self._state = dict()
        self._plot: Dict[str, Plotly] = dict()
        self._data: Dict[str, pd.DataFrame] = dict()
        # self._data = pd.DataFrame(columns=['name', 'ip', 'timestamp', 'reachable'])

        for name, ip in self.addresses.items():
            with ui.element('q-tab-panel').props(f'name={name}').classes('w-full'):
                ui.label(name).classes('text-2xl')
                ui.label(f"Address: {ip}").classes('text-l')
                ui.label(f"Log file: {str(self._log_files[name])}").classes('text-l')
                self._state[name] = ui.label(f'Unknown')
                if self._df_files[name].exists():
                    with self._df_files[name].open("r") as file:
                        data_frame = pd.read_csv(filepath_or_buffer=file)
                else:
                    data_frame = pd.DataFrame(columns=['name', 'ip', 'ctime', 'timestamp', 'reachable', 'color', 'one'])
                    with self._df_files[name].open("w") as file:
                        data_frame.to_csv(path_or_buf=file)
                self._data[name] = data_frame
                fig = px.bar(self._data[name], x='timestamp', y='reachable', color='color')
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
                plot = ui.plotly(fig).classes('w-full h-60')
                self._plot[name] = plot

        ui.timer(interval=update_frequency, callback=lambda: self.update_states())

    def update_states(self):
        for name, ip in self.addresses.items():
            reachable = self.ping(ip)

            now = datetime.datetime.now()
            timestamp = now.strftime("%m/%d/%Y, %H:%M:%S")
            total_seconds = (now - self.start_time).total_seconds() * 1000.0
            row = [None, name, ip, total_seconds, timestamp, reachable, 'green' if reachable else 'red',
                   1 if reachable else -1]

            if not reachable:
                with self._log_files[name].open("a") as file:
                    file.write(f"{name} was down at {timestamp}\n")
            if len(self._data[name]) < 2:
                insert_index = len(self._data[name])
            # if the last two checks had the sae reachable status
            # override the last status since we just want to know frm when to when a status was present
            elif self._data[name]['reachable'].iloc[-1] == reachable and self._data[name]['reachable'].iloc[
                -2] == reachable:
                insert_index = len(self._data[name]) - 1
            else:
                insert_index = len(self._data[name])
            self._data[name].loc[insert_index] = row

            with self._df_files[name].open("w") as file:
                self._data[name].to_csv(path_or_buf=file)

            self._plot[name].update_figure(
                figure=px.bar(self._data[name], x='ctime', y='one', color='reachable', hover_data="timestamp",
                              ))
            self._plot[name].update()

            if reachable is True:
                self._state[name].set_text(f"Reachable")
            else:
                self._state[name].set_text(f"Not Reachable")

    @staticmethod
    def ping(host):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        """

        # if host == "123.333.34.33":
        #     import random
        #     return random.random() < 0.7

        # Option for the number of packets as a function of
        param = '-n' if platform.system().lower() == 'windows' else '-c'

        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param, '1', host]

        return subprocess.call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

    def run(self):

        ui.run(title="Server State Dashboard")


def cli_run():
    parser = argparse.ArgumentParser(description='Server State Dashboard')
    parser.add_argument('--update_frequency',
                        "-f",
                        type=float,
                        default=60.,
                        help='The number of seconds between server state pings')

    args = parser.parse_args()
    dashboard = Dashboard(update_frequency=args.update_frequency)
    dashboard.run()


if __name__ in {"__main__", "__mp_main__", "server_state_dashboard.dashboard"}:
    cli_run()
