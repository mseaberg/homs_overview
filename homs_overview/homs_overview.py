import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QObject
from pydm import Display
import os
from mirror_module import  HOMS_state
import subprocess

class App(Display):

    def __init__(self, parent=None, args=None, macros=None):
        #print('Start of __init__ for template launcher')
        #print(f'args={args}, macros={macros}')
        # Call super after handling args/macros but before doing pyqt stuff
        super().__init__(parent=parent, args=args, macros=macros)
        # Now it is safe to refer to self.ui and access your widget objects
        # It is too late to do any macros processing
        #print('End of __init__ for template launcher')
        self.ui.hutchComboBox.addItems(['CXI','XCS','MFX','MEC'])

        self.ui.hutchComboBox.currentIndexChanged.connect(self.populate_energy_range)
        self.populate_energy_range()

        self.ui.moveButton.pressed.connect(self.move_mirrors)

        self.MR1L0 = HOMS_state('MR1L0',status=self.ui.MR1L0_status)
        self.MR2L0 = HOMS_state('MR2L0',status=self.ui.MR2L0_status)
        self.MR1L3 = HOMS_state('MR1L3',status=self.ui.MR1L3_status)
        self.MR2L3 = HOMS_state('MR2L3',status=self.ui.MR2L3_status)
        self.MR1L4 = HOMS_state('MR1L4',status=self.ui.MR1L4_status)
        self.mirror_list = [self.MR1L0, self.MR2L0, self.MR1L3, self.MR2L3, self.MR1L4]
        #self.MR1L0.connect_mirror('MR1L0')
        #self.MR2L0.connect_mirror('MR2L0')
        #self.MR1L3.connect_mirror('MR1L3')
        #self.MR2L3.connect_mirror('MR2L3')
        #self.MR1L4.connect_mirror('MR1L4')
        self.destination = 'XCS'
        self.curr_range = [0,0]
        self.bg = 'purple'
        self.color = 'white'

        self.ui.energyLabel.setStyleSheet("background-color: white")
        self.ui.beamLabel.setStyleSheet("background-color: white")
        self.ui.currEnergyLabel.setStyleSheet("background-color: white")           
        #self.actionChange_Setpoints.triggered.connect(self.change_setpoints)
        #self.ui.PyDMEmbeddedDisplay.hide()
        #self.ui.PyDMEmbeddedDisplay_2.hide()
        #self.ui.PyDMEmbeddedDisplay_3.hide()
        #self.ui.PyDMEmbeddedDisplay_4.hide()
        #self.ui.PyDMEmbeddedDisplay_5.hide()
        #self.show_mr1l0()
        #self.show_mr2l0()
        #self.show_mr1l3()
        #self.show_mr2l3()
        #self.show_mr1l4()

        #QtCore.QTimer.singleShot(500,self.do_resize)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.check_destination)
        self.timer.start()
        QtCore.QTimer.singleShot(500,self.do_resize)

    #def update_mirrors(self):
    #    self.MR1L0.update_mirror()
    #    self.MR2L0.update_mirror()
    #    self.MR1L3.update_mirror()
    #    self.MR2L3.update_mirror()
    #    self.MR1L4.update_mirror()

    #def change_setpoints(self):
    #    setpoint_window = Setpoints(self)
    #    setpoint_window.saveSig.connect(self.update_mirrors)
    #    setpoint_window.show()

    #def show_mirrors(self):
    #    self.dockWidget_2.setVisible(True)

    def do_resize(self):
        self.resize(self.ui.minimumSizeHint())

    def show_mr1l0(self):
        pass    
            
    def show_mr2l0(self):
        pass
    def show_mr1l3(self):
        pass
    def show_mr1l4(self):
        pass
    def show_mr2l3(self):
        pass
    def move_mirrors(self):

        destination = self.ui.hutchComboBox.currentText()
        energy_range = self.ui.energyComboBox.currentIndex()
        self.MR1L0.move_in_thread(energy_range)
        self.MR2L0.move_in_thread(energy_range)

        if destination=='CXI':
            self.MR1L4.move_out()
            self.MR1L3.move_out()
        elif destination=='XCS':
            self.MR1L3.move_in_thread(energy_range)
            self.MR2L3.move_in_thread(energy_range)
            self.MR1L4.move_out()
        elif destination=='MFX':
            self.MR1L3.move_out()
            self.MR1L4.move_in_thread(energy_range,destination='MFX')
        elif destination=='MEC':
            self.MR1L3.move_out()
            self.MR1L4.move_in_thread(energy_range,destination='MEC')

    def check_range(self,*args):
        minE = 0
        maxE = 1000
       
        for arg in args:
            if arg is not None:
                minE = max(minE,arg[0])
                maxE = min(maxE,arg[1])
        if maxE<minE:
            minE = 0
            maxE = 0
        return [minE, maxE]

    def check_destination(self):
        width = 100
        if self.MR1L3.is_in and self.MR1L4.is_out:
            self.destination = 'XCS'
            self.bg = 'purple'
            self.color = 'white'
            self.curr_range = self.check_range(self.MR1L0.current_range,self.MR2L0.current_range,self.MR1L3.current_range,self.MR2L3.current_range)
        elif self.MR1L4.is_in and self.MR1L3.is_out:
            self.destination = self.MR1L4.destination
            if self.destination=='MFX':
                self.bg = 'orange'
                self.color = 'white'
            elif self.destination=='MEC':
                self.bg = 'yellow'
                self.color = 'black'
            else:
                self.bg = 'white'
                self.color = 'black'
                self.destination = 'Unknown'
            self.curr_range = self.check_range(self.MR1L0.current_range,self.MR2L0.current_range,self.MR1L4.current_range)
        elif self.MR1L4.is_out and self.MR1L3.is_out:
            self.destination = 'CXI'
            self.bg = 'red'
            self.color = 'white'
            self.curr_range = self.check_range(self.MR1L0.current_range,self.MR2L0.current_range)
        else:
            self.destination = 'Unknown'
            self.bg = 'white'
            self.color = 'black'
            self.curr_range = [0,0]
            width = 200

        pitch_correct = np.zeros(5)

        for num, mirror in enumerate(self.mirror_list):
            pitch_correct[num] = mirror.check_pitch()

        if pitch_correct[0]==1:
            self.ui.pitch_status_label.setText('MR1L0 Pitch Nominal')
            self.ui.pitch_status_label.setStyleSheet('background-color: %s' % ('green'))
        else:
            self.ui.pitch_status_label.setText('Check MR1L0 Pitch')
            self.ui.pitch_status_label.setStyleSheet('background-color: %s' % ('red'))
        
        
        self.ui.beamLabel.setText(self.destination)
        self.ui.beamLabel.setStyleSheet("background-color: %s; color: %s" % (self.bg,self.color))
        self.ui.beamLabel.setFixedWidth(width)
        self.ui.energyLabel.setText('%.1f-%.1f keV' % (self.curr_range[0],self.curr_range[1]))


    def populate_energy_range(self):
        hutch = self.ui.hutchComboBox.currentText()
        if hutch=='CXI':
            energy = ['1-14','12-25']
        elif hutch=='XCS':
            energy = ['1-13.5','13-25']
        elif hutch=='MFX':
            energy = ['1-13.5','13-25']
        elif hutch=='MEC':
            energy = ['1-13.5','13-25']
        else:
            energy = ['1-14','12-25']
        self.ui.energyComboBox.clear()
        self.ui.energyComboBox.addItems(energy)


    def ui_filename(self):
        return 'homs_overview.ui'

