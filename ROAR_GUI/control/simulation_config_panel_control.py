from control.utilities import BaseWindow, PydanticModelEntry
from PyQt5 import QtCore, QtGui, QtWidgets
from view.simulation_config_panel import Ui_SimulationConfigWindow
from control.control_panel_control import ControlPanelWindow
from ROAR_Sim.configurations.configuration import Configuration as SimulationConfig
from pprint import pprint
import json
from typing import Dict, Union, Any
from pathlib import Path


class SimConfigWindow(BaseWindow):
    def __init__(self, app: QtWidgets.QApplication, sim_json_config_file_path: Path, **kwargs):
        super().__init__(app, Ui_SimulationConfigWindow, **kwargs)
        self.setting_list = []
        self.setting_dict = dict()
        self.dialogs = list()
        self.simulation_config = SimulationConfig()
        self.json_config_file_path: Path = sim_json_config_file_path
        self.model_info: Dict[str, PydanticModelEntry] = self.fill_config_list()

        # =====================================================================================================
        # create save button and add to menu

        self.ui.actionSave = QtWidgets.QAction(self)
        self.ui.actionSave.setObjectName("actionSave")
        self.ui.actionSave.setText(QtCore.QCoreApplication.translate("SimulationConfigWindow", "Save"))
        self.ui.menuFile.addAction(self.ui.actionSave)
        self.ui.actionSave.triggered.connect(self.save_config)

        # =====================================================================================================

    #  self.menubar.addAction(self.menuFile.menuAction())
    # self.text_change()
    #####
    # self.currentTextChanged.connect(self.onCurrentTextChanged)

    # def onCurrentTextChanged(self, text):
    #     print("\n text changed \n")

    def fill_config_list(self) -> Dict[str, Any]:
        model_info: Dict[str, Any] = dict()
        for key_name, entry in self.simulation_config.schema()['properties'].items():
            if "type" not in entry:
                continue
            model_info[key_name] = entry['title']  # PydanticModelEntry.parse_obj(entry)
            # pprint(entry)

        json_dict: dict = json.load(self.json_config_file_path.open('r'))
        for key_name, entry in json_dict.items():
            pass
            model_info[key_name] = entry
            # TODO update model_info, completed
            # print(key_name, entry)
        model_values = self.simulation_config.dict()
        # print("len:  ",len(model_info.items()))
        ##print(self.test_input_list)
        # print(self.setting_dict)

        for name, entry in model_values.items():
            # TODO do not populate if it is not of type [int, float, string, bool]
            if name in model_info.keys():
                entry = model_info[name]
            # type check -> present if type in ['int','float','string','bool']
            try:
                if isinstance(eval(str(entry)), dict):
                    continue
            except:
                pass
            self.add_entry_to_settings_gui(name=name,
                                           value=entry)
            # self.test_input_list.append([name,str(curr_value)])

            self.setting_dict[name] = entry
        # self.logger.debug()
        return model_info

    def add_entry_to_settings_gui(self, name: str, value: Union[str, int, float, bool]):
        label = QtWidgets.QLabel()
        label.setText(name)
        input_field = QtWidgets.QLineEdit()  # QTextEdit()
        input_field.setText(str(value))
        input_field.setObjectName(name)
        self.setting_list.append(input_field)
        # input_field.textChanged.connect(self.on_change)
        # self.test_input_list.append(str(value))

        self.ui.formLayout.addRow(label, input_field)

    def set_listener(self):
        super(SimConfigWindow, self).set_listener()
        self.ui.pushButton_confirm.clicked.connect(self.pushButton_confirm)

    # def on_change(self,text):
    #     print("text changed: ", text)
    #     print(self.setting_list[1].text())
    #     print(self.setting_list[1].objectName())
    # print(self.setting_dict)

    def isfloat(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def pushButton_confirm(self):
        self.auto_wire_window(ControlPanelWindow)
        # self.save_config()

    def save_config(self):
        """
        save config to file
        """

        sim_config_json = {}

        for widget in self.setting_list:
            # if isinstance(widget, QtWidgets.QLineEdit):
            # print(widget.objectName(),":", widget.text())
            if widget.text().isnumeric():
                sim_config_json[widget.objectName()] = int(widget.text())
            elif self.isfloat(widget.text()):
                sim_config_json[widget.objectName()] = float(widget.text())
            elif widget.text().lower() == "true":
                sim_config_json[widget.objectName()] = True
            elif widget.text().lower() == "false":
                sim_config_json[widget.objectName()] = False
            else:
                sim_config_json[widget.objectName()] = widget.text()

        json_dict: dict = json.load(self.json_config_file_path.open('r'))
        json_object = sim_config_json
        for key, entry in json_object.items():
            try:
                json_dict[key] = eval(entry)
            except:
                json_dict[key] = entry

        # current C:\Users\Zetian\Desktop\project\ROAR\ROAR_Desktop\ROAR_GUI
        # need    C:\Users\Zetian\Desktop\project\ROAR\ROAR_Sim\configurations
        # pathlib
        with open("../../ROAR_Sim/configurations/configuration.json", "w") as outfile:
            outfile.write(json.dumps(json_dict, indent = 2))

    def auto_wire_window(self, target_window):
        target_app = target_window(self.app)
        self.dialogs.append(target_app)
        target_app.show()
        self.hide()
        target_app.show()
        target_app.closeEvent = self.app_close_event

    def app_close_event(self, close_event):
        self.show()
