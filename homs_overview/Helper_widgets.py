from PyQt5.uic import loadUiType
import os
from ophyd import EpicsSignalRO
from pyqtgraph.Qt import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtCore
import json
import numpy as np


local_path = os.path.dirname(os.path.abspath(__file__))
Ui_Status, QStatus = loadUiType(local_path+'/status_indicator.ui')
#Ui_Setpoints, QSetpoints = loadUiType(local_path+'/setpoint_dialog.ui')

#class Setpoints(QSetpoints, Ui_Setpoints):
#
#    saveSig = pyqtSignal() 
#
#    def __init__(self, parent):
#        super(Setpoints,self).__init__(parent)
#        self.setupUi(self)
#       
#        #self.parent = parent
#        self.buttonBox.accepted.connect(self.save_settings)
#
#        with open(local_path+'/mirror_info.dat') as json_file:
#            info = json.load(json_file)
#
#        self.mr1l0_1.setText(str(info['MR1L0']['Pitch'][0]))
#        self.mr1l0_2.setText(str(info['MR1L0']['Pitch'][1]))
#        self.mr2l0_1.setText(str(info['MR2L0']['Pitch'][0]))
#        self.mr2l0_2.setText(str(info['MR2L0']['Pitch'][1]))
#        self.mr1l3_1.setText(str(info['MR1L3']['Pitch'][0]))
#        self.mr1l3_2.setText(str(info['MR1L3']['Pitch'][1]))
#        self.mr2l3_1.setText(str(info['MR2L3']['Pitch'][0]))
#        self.mr2l3_2.setText(str(info['MR2L3']['Pitch'][1]))
#        self.mr1l4_mfx_1.setText(str(info['MR1L4']['MFX_Pitch'][0]))
#        self.mr1l4_mfx_2.setText(str(info['MR1L4']['MFX_Pitch'][1]))
#        self.mr1l4_mec_1.setText(str(info['MR1L4']['MEC_Pitch'][0]))
#        self.mr1l4_mec_2.setText(str(info['MR1L4']['MEC_Pitch'][1]))
#
#        self.info = info
#
#    def save_settings(self):
#       
#        try:
#            self.info['MR1L0']['Pitch'][0] = float(self.mr1l0_1.text())
#            self.info['MR1L0']['Pitch'][1] = float(self.mr1l0_2.text())
#            self.info['MR2L0']['Pitch'][0] = float(self.mr2l0_1.text())
#            self.info['MR2L0']['Pitch'][1] = float(self.mr2l0_2.text())
#            self.info['MR1L3']['Pitch'][0] = float(self.mr1l3_1.text())
#            self.info['MR1L3']['Pitch'][1] = float(self.mr1l3_2.text())
#            self.info['MR2L3']['Pitch'][0] = float(self.mr2l3_1.text())
#            self.info['MR2L3']['Pitch'][1] = float(self.mr2l3_2.text())
#            self.info['MR1L4']['MFX_Pitch'][0] = float(self.mr1l4_mfx_1.text())
#            self.info['MR1L4']['MFX_Pitch'][1] = float(self.mr1l4_mfx_2.text())
#            self.info['MR1L4']['MEC_Pitch'][0] = float(self.mr1l4_mec_1.text())
#            self.info['MR1L4']['MEC_Pitch'][1] = float(self.mr1l4_mec_2.text())
#
#            with open(local_path+'/mirror_info.dat','w') as json_file:
#                json.dump(self.info, json_file, indent=4)
#
#            self.saveSig.emit()
#        except ValueError:
#            print('Could not convert all entries to floats.')
#



class StatusIndicator(QStatus, Ui_Status):
    def __init__(self, parent=None):
        super(StatusIndicator,self).__init__()
        self.setupUi(self)
        self.moving_pvs = {}
        self.error_pvs = {}
        self.moving_status = {}
        self.error_status = {}
        self.status_names = []
        self.colors = []
        self.pitch_rbv = None
        self.nominal_pitch = None
        self.timer = None

    def connect(self,prefix, pitch_pv, moving_pvs, error_pvs, status_names,colors):
        
        self.pitch_rbv = pitch_pv
        for pv_name in moving_pvs:
            pv_name = prefix + pv_name
            self.moving_pvs[pv_name] = EpicsSignalRO(read_pv=pv_name)
            self.moving_status[pv_name] = False
        
            self.moving_pvs[pv_name].subscribe(self.update_status)

        for pv_name in error_pvs:
            pv_name = prefix + pv_name
            self.error_pvs[pv_name] = EpicsSignalRO(read_pv=pv_name)
            self.error_status[pv_name] = False
        
            self.error_pvs[pv_name].subscribe(self.update_status)


        self.status_names = status_names
        self.colors = colors
        self.timer = QtCore.QTimer()
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.update_status)
        self.timer.start()

    def update_nominal(self, nominal):
        self.nominal_pitch = nominal

    def update_status(self,**kwargs):
        #print(kwargs.keys())
        #print(kwargs['obj'])
        
        moving_status_all = []
        error_status_all = []
        if 'obj' in kwargs.keys():
            name = kwargs['obj'].name
        else:
            name = ''
        if 'Error' in name:
            self.error_status[name] = kwargs['value']
        elif 'MOVN' in name:
            self.moving_status[name] = kwargs['value']

        for key,value in self.moving_status.items():
            moving_status_all.append(value)

        for key, value in self.error_status.items():
            error_status_all.append(value)

        curr_moving_status = any(moving_status_all)
        curr_error_status = any(error_status_all)

        # check pitch
        pitch_flag = 0
        if self.nominal_pitch is not None:
            if np.abs(self.pitch_rbv.get()-self.nominal_pitch.get())>0.2:
                pitch_flag = 1

        if curr_error_status:
            self.statusLabel.setText(self.status_names[2])
            self.statusCircle.brush.setColor(QtGui.QColor(self.colors[2]))# = QtGui.QBrush(self.colors[int(status)])
        elif curr_moving_status:
            self.statusLabel.setText(self.status_names[int(curr_moving_status)])
            self.statusCircle.brush.setColor(QtGui.QColor(self.colors[int(curr_moving_status)]))
        elif pitch_flag:
            self.statusLabel.setText('Check\nPitch')
            self.statusCircle.brush.setColor(QtGui.QColor(self.colors[1]))
        else:
            self.statusLabel.setText('On\nTarget')
            self.statusCircle.brush.setColor(QtGui.QColor(self.colors[0]))

        self.statusCircle.update()
