from PyQt5.uic import loadUiType
import os
from ophyd import EpicsSignalRO
from pyqtgraph.Qt import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
import json
import numpy as np
import time


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
        self.pvs = {}
        self.status = {}
        self.status_names = []
        self.colors = []

    def connect(self,prefix, pv_names, status_names,colors):
        for pv_name in pv_names:
            pv_name = prefix + pv_name
            self.pvs[pv_name] = EpicsSignalRO(read_pv=pv_name)
            self.status[pv_name] = False
        
            self.pvs[pv_name].subscribe(self.update_status)

        self.status_names = status_names
        self.colors = colors

    def update_status(self,**kwargs):
        #print(kwargs.keys())
        #print(kwargs['obj'])


        all_status = []
        name = kwargs['obj'].name
        self.status[name] = kwargs['value']

        for key,value in self.status.items():
            all_status.append(value)

        status = any(all_status)

        self.statusLabel.setText(self.status_names[int(status)])
        self.statusCircle.brush.setColor(QtGui.QColor(self.colors[int(status)]))# = QtGui.QBrush(self.colors[int(status)])
        self.statusCircle.update()
