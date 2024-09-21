import time
from os import path
from pydm import Display
from pydm.widgets.pushbutton import PyDMPushButton
from pydm.widgets import PyDMLabel
from typhos.alarm import TyphosAlarmCircle
from typhos.related_display import TyphosRelatedSuiteButton

from qtpy.QtWidgets import QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from qtpy import QtCore, QtGui
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from ophyd import Component as Cpt, Device
from ophyd import EpicsSignal, EpicsSignalRO
from pcdsdevices.state import TwinCATStatePositioner


class StateMover(Device):

    axis = Cpt(TwinCATStatePositioner, '')
    #state = Cpt(EpicsSignal, 'MR2L3:HOMS:COATING:STATE:GET_RBV')

    def __init__(self, pv, name):
        super().__init__(prefix=pv, name=name)


class MirrorScreen(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(MirrorScreen, self).__init__(parent=parent, args=args, macros=macros)
        if macros != None:
            self.x_stop = EpicsSignal(macros['BASE_PV'] + ":MMS:XUP.STOP")
            self.y_stop = EpicsSignal(macros['BASE_PV'] + ":MMS:YUP.STOP")
            self.p_stop = EpicsSignal(macros['BASE_PV'] + ":MMS:PITCH.STOP")

        parsed_pv = macros['BASE_PV'].split(":")
        self.display_name = parsed_pv[0]
        offset_type = parsed_pv[1].lower()

        coating1 = EpicsSignalRO(macros['BASE_PV'] + ":COATING:STATE:GET_RBV.ONST")
        coating2 = EpicsSignalRO(macros['BASE_PV'] + ":COATING:STATE:GET_RBV.TWST")

        alarm_box_x = QHBoxLayout()
        alarm_box_y = QHBoxLayout()
        alarm_box_p = QHBoxLayout()
        alarm_box_gantry_x = QHBoxLayout()
        alarm_box_gantry_y = QHBoxLayout()
        self.ghost = QHBoxLayout()

        alarm_x = TyphosAlarmCircle()
        alarm_x.channel = "ca://" + macros['BASE_PV'] + ":MMS:XUP"
        alarm_x.setMaximumHeight(35)
        alarm_x.setMaximumWidth(35)

        alarm_y = TyphosAlarmCircle()
        alarm_y.channel = "ca://" + macros['BASE_PV'] + ":MMS:YUP"
        alarm_y.setMaximumHeight(35)
        alarm_y.setMaximumWidth(35)

        alarm_p = TyphosAlarmCircle()
        alarm_p.channel = "ca://" + macros['BASE_PV'] + ":MMS:PITCH"
        alarm_p.setMaximumHeight(35)
        alarm_p.setMaximumWidth(35)

        label_font = QFont()
        label_font.setBold(True) 

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        x_label = QLabel("x")
        y_label = QLabel("y")
        p_label = QLabel("pitch")
        gantry_x_label = QLabel("gantry x")
        gantry_y_label = QLabel("gantry y")
        set_mirror_label = QLabel("set mirror:")
        set_mirror_label.setFont(label_font)

        x_state_RBV = PyDMLabel()
        x_state_RBV.channel = "ca://" + macros['BASE_PV'] + ":MMS:XUP:STATE:GET_RBV"

        alarm_gantry_x = TyphosAlarmCircle()
        alarm_gantry_x.channel = "ca://" + macros['BASE_PV'] + ":ALREADY_COUPLED_X_RBV"
        alarm_gantry_x.setMaximumHeight(35)
        alarm_gantry_x.setMaximumWidth(35)

        alarm_gantry_y = TyphosAlarmCircle()
        alarm_gantry_y.channel = "ca://" + macros['BASE_PV'] + ":ALREADY_COUPLED_Y_RBV"
        alarm_gantry_y.setMaximumHeight(35)
        alarm_gantry_y.setMaximumWidth(35)

        alarm_box_x.addWidget(x_label)
        alarm_box_x.setAlignment(x_label, Qt.AlignCenter)
        alarm_box_x.addWidget(alarm_x)

        alarm_box_y.addWidget(y_label)
        alarm_box_y.setAlignment(y_label, Qt.AlignCenter)
        alarm_box_y.addWidget(alarm_y)

        alarm_box_p.addWidget(p_label)
        alarm_box_p.setAlignment(p_label, Qt.AlignCenter)
        alarm_box_p.addWidget(alarm_p)

        alarm_box_gantry_x.addWidget(gantry_x_label)
        alarm_box_gantry_x.setAlignment(gantry_x_label, Qt.AlignCenter)
        alarm_box_gantry_x.addWidget(alarm_gantry_x)

        alarm_box_gantry_y.addWidget(gantry_y_label)
        alarm_box_gantry_y.setAlignment(gantry_y_label, Qt.AlignCenter)
        alarm_box_gantry_y.addWidget(alarm_gantry_y)

        # buttons
        in_state_button = PyDMPushButton(label="IN")
        in_state_button.channel = "ca://" + macros['BASE_PV'] + ":MMS:XUP:STATE:SET"
        in_state_button.pressValue = 2
        in_state_button.setMaximumWidth(50)

        out_state_button = PyDMPushButton(label="OUT")
        out_state_button.channel = "ca://" + macros['BASE_PV'] + ":MMS:XUP:STATE:SET"
        out_state_button.pressValue = 1
        out_state_button.setMaximumWidth(50)


        stop_button = PyDMPushButton(label="Stop")
        stop_button.setMaximumHeight(120)
        stop_button.setMaximumWidth(120)
        stop_button.clicked.connect(self.stop_motors)
        stop_button.setStyleSheet("background: rgb(255,0,0)")

        advanced_button = TyphosRelatedSuiteButton()
        
        advanced_button.happi_names = [self.display_name.lower() + "_" + offset_type]
        advanced_button.setText("Advanced")

        if self.display_name == "MR1L4":
            coating1_state_button = PyDMPushButton(label=coating1.get() + " MEC")
            coating2_state_button = PyDMPushButton(label=coating2.get() + " MEC")

            coating1_state_button.setMaximumWidth(55)
            coating2_state_button.setMaximumWidth(55)

            coating3_state_button = PyDMPushButton(label=coating1.get() + " MFX")
            coating3_state_button.channel = "ca://" + macros['BASE_PV'] + ":COATING:STATE:SET"
            coating3_state_button.pressValue = 1
            coating3_state_button.setMaximumWidth(55)

            coating4_state_button = PyDMPushButton(label=coating2.get() + " MFX")
            coating4_state_button.channel = "ca://" + macros['BASE_PV'] + ":COATING:STATE:SET"
            coating4_state_button.pressValue = 2
            coating4_state_button.setMaximumWidth(50)

            self.ui.horizontalLayout.addWidget(coating3_state_button)
            self.ui.horizontalLayout.addWidget(coating4_state_button)

            coating3_state_button.clicked.connect(self.compound_coating3_move)
            coating4_state_button.clicked.connect(self.compound_coating4_move)
        elif self.display_name == "MR2L3":
            coating1_state_button = PyDMPushButton(label=coating1.get())
            coating2_state_button = PyDMPushButton(label=coating2.get())
            coating1_state_button.setMaximumWidth(50)
            coating2_state_button.setMaximumWidth(50)

            coating3_state_button = PyDMPushButton(label=coating1.get() + " CCM")
            coating3_state_button.channel = "ca://" + macros['BASE_PV'] + ":COATING:STATE:SET"
            coating3_state_button.pressValue = 1
            coating3_state_button.setMaximumWidth(55)

            coating4_state_button = PyDMPushButton(label=coating2.get() + " CCM")
            coating4_state_button.channel = "ca://" + macros['BASE_PV'] + ":COATING:STATE:SET"
            coating4_state_button.pressValue = 2
            coating4_state_button.setMaximumWidth(50)

            self.ui.horizontalLayout.addWidget(coating3_state_button)
            self.ui.horizontalLayout.addWidget(coating4_state_button)

            coating3_state_button.clicked.connect(self.compound_ccm_coating3_move)
            coating4_state_button.clicked.connect(self.compound_ccm_coating4_move)
        else:
            coating1_state_button = PyDMPushButton(label=coating1.get())
            coating2_state_button = PyDMPushButton(label=coating2.get())
            coating1_state_button.setMaximumWidth(50)
            coating2_state_button.setMaximumWidth(50)
            
        coating1_state_button.channel = "ca://" + macros['BASE_PV'] + ":COATING:STATE:SET"
        coating1_state_button.pressValue = 1

        coating2_state_button.channel = "ca://" + macros['BASE_PV'] + ":COATING:STATE:SET"
        coating2_state_button.pressValue = 2

        self.ui.label_8.setText(self.display_name)
        self.ui.horizontalLayout.addWidget(coating1_state_button)
        self.ui.horizontalLayout.addWidget(coating2_state_button)
        # y axis box 

        coating1_state_button.clicked.connect(self.compound_coating1_move)
        coating2_state_button.clicked.connect(self.compound_coating2_move)

        # x axis box
        if 'OUT_STATE' in macros and macros['OUT_STATE'] == "TRUE":
            self.ui.horizontalLayout_2.addItem(spacer)
            self.ui.horizontalLayout_2.addWidget(x_state_RBV)
            self.ui.horizontalLayout_2.addItem(spacer)
            self.ui.horizontalLayout_2.addWidget(set_mirror_label)
            self.ui.horizontalLayout_2.addWidget(in_state_button)
            self.ui.horizontalLayout_2.addWidget(out_state_button)
        # no in/out state
        else:
            self.ui.horizontalLayout_2.addItem(spacer)
        
        # alarm box 
        self.ui.horizontalLayout_8.addLayout(alarm_box_x)
        self.ui.horizontalLayout_8.addLayout(alarm_box_y)
        self.ui.horizontalLayout_8.addLayout(alarm_box_p)
        self.ui.horizontalLayout_8.addLayout(alarm_box_gantry_x)
        self.ui.horizontalLayout_8.addLayout(alarm_box_gantry_y)

        # bottom button box
        self.ui.horizontalLayout_14.addWidget(advanced_button)
        self.ui.horizontalLayout_14.addSpacing(50)
        self.ui.horizontalLayout_14.addWidget(stop_button)
        self.ui.horizontalLayout_14.addSpacing(160)

        self.ui.setGeometry(QtCore.QRect(0,0, 360, 385))

    def compound_coating1_move(self):
        if self.display_name == "MR1L4":
            coating_setpoint = EpicsSignalRO(self.display_name + ":PITCH:MEC:Coating1")
        else:
            coating_setpoint = EpicsSignalRO(self.display_name + ":PITCH:Coating1")
        coating = EpicsSignal(self.display_name + ":HOMS:MMS:PITCH")
        coating.put(coating_setpoint.get())

    def compound_coating2_move(self):
        if self.display_name == "MR1L4":
            coating_setpoint = EpicsSignalRO(self.display_name + ":PITCH:MEC:Coating2")
        else:
            coating_setpoint = EpicsSignalRO(self.display_name + ":PITCH:Coating2")
        coating = EpicsSignal(self.display_name + ":HOMS:MMS:PITCH")
        coating.put(coating_setpoint.get())

    def compound_coating3_move(self):
        coating_setpoint = EpicsSignalRO(self.display_name + ":PITCH:MFX:Coating1")
        coating = EpicsSignal(self.display_name + ":HOMS:MMS:PITCH")
        coating.put(coating_setpoint.get())

    def compound_coating4_move(self):
        coating_setpoint = EpicsSignalRO(self.display_name + ":PITCH:MFX:Coating2")
        coating = EpicsSignal(self.display_name + ":HOMS:MMS:PITCH")
        coating.put(coating_setpoint.get())

    def compound_ccm_coating3_move(self):
        coating_setpoint = EpicsSignalRO(self.display_name + ":PITCH:CCM:Coating1")
        coating = EpicsSignal(self.display_name + ":HOMS:MMS:PITCH")
        coating.put(coating_setpoint.get())

    def compound_ccm_coating4_move(self):
        coating_setpoint = EpicsSignalRO(self.display_name + ":PITCH:CCM:Coating2")
        coating = EpicsSignal(self.display_name + ":HOMS:MMS:PITCH")
        coating.put(coating_setpoint.get())

    def stop_motors(self):
        self.x_stop.put(1)
        self.y_stop.put(1)
        self.p_stop.put(1)

    def ui_filename(self):
        # Point to our UI file
        return 'mirrorScreen.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())
