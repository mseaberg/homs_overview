from PyQt5.QtCore import Qt
from PyQt5.uic import loadUiType
import numpy as np
import json
import os
from ophyd import EpicsSignal, EpicsSignalRO
from epics import PV
from pydm.widgets.channel import PyDMChannel
from pydm.data_plugins import PyDMPlugin
import subprocess
import threading
import time
#from pcdsdevices.mirror import TwinCATMirrorStripeTuple

local_path = os.path.dirname(os.path.abspath(__file__))

class HOMS_state:
    def __init__(self, mirror_name, status=None):

        self.name = mirror_name
        with open(local_path+'/mirror_info.dat') as json_file:
            info = json.load(json_file)
       
        mirror_info = info[self.name]
        #self.y_pos = mirror_info['Y']
        #self.in_pos = mirror_info['IN']
        #self.out_pos = mirror_info['OUT']
        self.prefix = mirror_info['prefix']
        self.is_inout = mirror_info['inout']
        self.is_in = False
        self.is_out = False
        self.destination = None
       
        self.current_range = None
        
        self.nominal_pitch = None
        
        if self.name=='MR1L4':
            self.mec_ranges = mirror_info['MEC_Ranges']
            self.mfx_ranges = mirror_info['MFX_Ranges']
        else:
            self.ranges = mirror_info['Ranges']

        # connect to pv's

        self.pitch_rbvs = {}

        if self.name == 'MR1L4':
            self.pitch_rbvs['MFX_Coating1'] = EpicsSignalRO(read_pv='{}:PITCH:MFX:Coating1'.format(self.name))
            self.pitch_rbvs['MFX_Coating2'] = EpicsSignalRO(read_pv='{}:PITCH:MFX:Coating2'.format(self.name))
            self.pitch_rbvs['MEC_Coating1'] = EpicsSignalRO(read_pv='{}:PITCH:MEC:Coating1'.format(self.name))
            self.pitch_rbvs['MEC_Coating2'] = EpicsSignalRO(read_pv='{}:PITCH:MEC:Coating2'.format(self.name))
        else:
            self.pitch_rbvs['Coating1'] = EpicsSignalRO(read_pv='{}:PITCH:Coating1'.format(self.name))
            self.pitch_rbvs['Coating2'] = EpicsSignalRO(read_pv='{}:PITCH:Coating2'.format(self.name))

        self.x_state_rbv = EpicsSignalRO(read_pv=self.prefix+'MMS:XUP:STATE:GET_RBV')
        self.coating_rbv = EpicsSignal(read_pv=self.prefix+'COATING:STATE:GET_RBV')
        self.coating_done = EpicsSignalRO(read_pv=self.prefix+'COATING:STATE:DONE_RBV')
        self.pitch_done = EpicsSignalRO(read_pv=self.prefix+'MMS:PITCH:DONE_RBV')
        self.pitch_rbv = EpicsSignalRO(read_pv=self.prefix+'MMS:PITCH.RBV')
        self.x_state = EpicsSignal(self.prefix+'MMS:XUP:STATE:SET')
        #self.coating_motor = EpicsSignal(self.prefix+'COATING:STATE:SET')
        self.coating_motor = PV(self.prefix+'COATING:STATE:SET')
        self.pitch_motor = EpicsSignal(self.prefix+'MMS:PITCH')

        self.coating_rbv.subscribe(self.check_coating)
   
        self.x_state_rbv.subscribe(self.check_inout)
        self.pitch_rbv.subscribe(self.check_dest)
        self.coating_moving = EpicsSignalRO(read_pv=self.prefix+'MMS:YUP.MOVN')
        self.pitch_moving = EpicsSignalRO(read_pv=self.prefix+'MMS:PITCH.MOVN')

        moving_names = ['MMS:PITCH.MOVN','MMS:XUP.MOVN','MMS:YUP.MOVN']
        status_names = ['Ready','Moving']
        colors = [Qt.green,Qt.yellow]
        status.connect(self.prefix,moving_names,status_names,colors)

        #error_names = ['MMS:XUP:PLC:nErrorId_RBV','MMS:YUP:PLC:nErrorId_RBV','MMS:PITCH:PLC:nErrorId_RBV',
        #        'MMS:XDWN:PLC:nErrorId_RBV','MMS:YDWN:PLC:nErrorId_RBV']

    def update_mirror(self):
        with open(local_path+'/mirror_info.dat') as json_file:
            info = json.load(json_file)
     
        mirror_info = info[self.name]

        if self.name=='MR1L4':
            self.mec_ranges = mirror_info['MEC_Ranges']
            self.mec_pitches = mirror_info['MEC_Pitch']
            self.mfx_ranges = mirror_info['MFX_Ranges']
            self.mfx_pitches = mirror_info['MFX_Pitch']
        else:
            self.ranges = mirror_info['Ranges']
            self.pitches = mirror_info['Pitch']
        self.y_pos = mirror_info['Y']
        self.coatings = mirror_info['Coatings']
        self.in_pos = mirror_info['IN']
        self.out_pos = mirror_info['OUT']
        self.prefix = mirror_info['prefix']

        if self.in_pos=='nan':
            self.in_pos = np.nan
        if self.out_pos=='nan':
            self.out_pos = np.nan

    def check_coating(self, **kwargs):
        if kwargs['value']==1:
            if self.name=='MR1L4':
                if self.destination=='MFX':
                    self.current_range = self.MFX_ranges[0]
                    self.nominal_pitch = self.pitch_rbvs['MFX_Coating1'].get()
                elif self.destination=='MEC':
                    self.current_range = self.MEC_ranges[0]
                    self.nominal_pitch = self.pitch_rbvs['MEC_Coating1'].get()
                else:
                    self.current_range = None
            else:
                self.current_range = self.ranges[0]
                self.nominal_pitch = self.pitch_rbvs['Coating1'].get()
        elif kwargs['value']==2:
            if self.name=='MR1L4':
                if self.destination=='MFX':
                    self.current_range = self.MFX_ranges[1]
                    self.nominal_pitch = self.pitch_rbvs['MFX_Coating2'].get()
                elif self.destination=='MEC':
                    self.current_range = self.MEC_ranges[1]
                    self.nominal_pitch = self.pitch_rbvs['MEC_Coating2'].get()
                else:
                    self.current_range = None
            else:

                self.current_range = self.ranges[1]
                self.nominal_pitch = self.pitch_rbvs['Coating2'].get()
        else:
            self.current_range = None

    def check_dest(self, **kwargs):
        if self.name=='MR1L4':
            if kwargs['value']<=-500:
                self.destination = 'MFX'
            elif kwargs['value']>=800:
                self.destination = 'MEC'
            else:
                self.destination = None

    def check_inout(self,**kwargs):
       
        if kwargs['value']==2:
            self.is_in = True
            self.is_out = False
        elif kwargs['value']==1:
            self.is_in = False
            self.is_out = True
        else:
            self.is_in = False
            self.is_out = False
        #state = 'Unknown'
        #if np.abs(kwargs['value'] - self.in_pos)<1000:
        #    state = 'IN'
        #    self.is_in = True
        #elif np.abs(kwargs['value'] - self.out_pos)<1000:
        #    state = 'OUT'
        #    self.is_in = False
        #else:
        #    self.is_in = False
  
    def move_in_thread(self, energy_range, destination=None):
        thread = threading.Thread(target=self.move_in, args=[energy_range], kwargs={"destination": destination})
        thread.start()

    def move_pitch(self,**kwargs):
        self.pitch_motor.set(self.nominal_pitch)

    def move_in(self, energy_range, destination=None):
        if self.is_inout:
            self.x_state.set(2)

        self.coating_motor.put(energy_range+1,wait=True)

        #time.sleep(0.1)
        if self.name=='MR1L4':
            if destination=='MFX':
                if energy_range==0:
                    self.nominal_pitch = self.pitch_rbvs['MFX_Coating1'].get()
                    self.pitch_motor.set(self.nominal_pitch)
                    
                elif energy_range==1:
                    self.nominal_pitch = self.pitch_rbvs['MFX_Coating2'].get()
                    self.pitch_motor.set(self.nominal_pitch)
            elif destination=='MEC':
                if energy_range==0:
                    self.nominal_pitch = self.pitch_rbvs['MEC_Coating1'].get()
                    self.pitch_motor.set(self.nominal_pitch)
                elif energy_range==1:
                    self.nominal_pitch = self.pitch_rbvs['MEC_Coating2'].get()
                    self.pitch_motor.set(self.nominal_pitch)
        else:
            if energy_range==0:
                self.nominal_pitch = self.pitch_rbvs['Coating1'].get()
                self.pitch_motor.set(self.nominal_pitch)
            elif energy_range==1:
                self.nominal_pitch = self.pitch_rbvs['Coating2'].get()
                self.pitch_motor.set(self.nominal_pitch)
       
        # wait for mirror to stop moving and then send pitch command again
        moving_status = True
        while moving_status:
            moving_status = np.logical_and(self.coating_moving.get(),self.pitch_moving.get())
            time.sleep(0.5)

        time.sleep(0.5) 
        if np.abs(self.pitch_rbv.get()-self.nominal_pitch)>0.2:
            self.move_pitch()

    def check_pitch(self):
        pitch_flag = 1
        if self.nominal_pitch is not None:
            if np.abs(self.pitch_rbv.get()-self.nominal_pitch)>0.2:
                pitch_flag=0
        return pitch_flag


    def move_out(self):
        if self.is_inout: 
            self.x_state.set(1)

