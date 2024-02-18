import numpy as np
import functions as f
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from scipy import signal
import pyqtgraph as pg



class FilterDesign:
    def __init__(self, plot_widget, mag_plot_widget, phase_plot_widget):
        self.zeros = []
        self.poles = []
        self.zero_items = []
        self.pole_items = []
        self.selected_zero = None
        self.selected_pole = None
        self.selected_item = None
        self.plot_widget = plot_widget
        self.mag_plot_widget = mag_plot_widget
        self.phase_plot_widget = phase_plot_widget
        if plot_widget:
            self.plot_unit_circle()

    def plot_unit_circle(self):
        theta = np.linspace(0, 2 * np.pi, 100)
        x = np.cos(theta)
        y = np.sin(theta)
        self.plot_widget.plot(x,y,pen='k')
        self.plot_widget.plot([0, 0], [-1, 1], pen='k')
        self.plot_widget.plot([-1, 1], [0, 0], pen='k')
        self.plot_widget.setTitle("Z-Plane")
        self.plot_widget.setAspectLocked(True)

    def add_zero_pole(self, event):

        pos = event.scenePos()

        item_pos = self.plot_widget.plotItem.mapToView(pos)
        pnt = (round(item_pos.x(),1), round(item_pos.y(),1))

        # Add zero or pole based on user input
        if event.button() == 1:  # Left mouse button for zero
            if pnt not in self.zeros:
                self.zeros.append(pnt)
            else:
                self.selected_zero = pnt
        elif event.button() == 2:  # Right mouse button for pole
            if self.is_within_unit_circle(pnt[0],pnt[1]):
                if pnt not in self.poles:
                    self.poles.append(pnt)
                else:
                    self.selected_pole = pnt
        elif event.button() == 4:
            self.selected_zero = None
            self.selected_pole = None



        # Update z-plane plot
        self.update_z_plane()

    def update_z_plane(self):

        # Plot zeros and poles
        for zero in self.zeros:
           item =pg.ScatterPlotItem(symbol='o', brush='r', size=10)
           item.setData(x=[zero[0]], y=[zero[1]])
           self.plot_widget.addItem(item)
           self.zero_items.append(item)

           if zero==self.selected_zero:
               item.setBrush(pg.mkBrush('yellow'))


        for pole in self.poles:
            item=pg.ScatterPlotItem(symbol='x', symbolPen='b', size=10)
            item.setData([pole[0]], [pole[1]],)
            self.plot_widget.addItem(item)
            self.pole_items.append(item)
            if pole == self.selected_pole:
                item.setBrush(pg.mkBrush('yellow'))
        self.compute_freq_response()

    def remove_zero(self):
        self.zeros.remove(self.selected_zero)
        temp_zeros = self.zeros
        self.clear_zeros()
        self.zeros = temp_zeros
        self.selected_zero=None
        self.update_z_plane()

    def remove_pole(self):
        self.poles.remove(self.selected_pole)
        temp_poles = self.poles
        self.clear_poles()
        self.poles = temp_poles
        self.selected_pole=None
        self.update_z_plane()

    def clear_all(self):
        self.clear_zeros()
        self.clear_poles()
        self.compute_freq_response()

    def add_conjugate(self):

        if self.selected_zero:
            if self.selected_zero !=0:
                item = pg.ScatterPlotItem(symbol='o', brush='r', size=10)
                item.setData(x=[self.selected_zero[0]], y=[-self.selected_zero[1]])
                self.plot_widget.addItem(item)
                self.zero_items.append(item)
                self.zeros.append((self.selected_zero[0],-self.selected_zero[1]))
        if self.selected_pole:
            if self.selected_pole != 0:
                 item = pg.ScatterPlotItem(symbol='x', brush='r', size=10)
                 item.setData(x=[self.selected_pole[0]], y=[-self.selected_pole[1]])
                 self.plot_widget.addItem(item)
                 self.pole_items.append(item)
                 self.poles.append((self.selected_pole[0],-self.selected_pole[1]))
        self.selected_pole=None
        self.selected_zero=None
        self.compute_freq_response()

    def clear_zeros(self):
        for item in self.zero_items:
            self.plot_widget.removeItem(item)
            self.zeros=[]
        self.compute_freq_response()

    def clear_poles(self):
        for item in self.pole_items:
            self.plot_widget.removeItem(item)
            self.poles=[]
        self.compute_freq_response()

    def compute_freq_response(self):
        zeros = [complex(x, y) for x, y in self.zeros]
        poles = [complex(x, y) for x, y in self.poles]
        omega, h = signal.freqz_zpk(zeros, poles, 1)
        eps = 1e-10
        self.magnitude = 20 * np.log10(np.abs(h)+ eps)
        self.phase = np.unwrap(np.angle(h))
        self.frequecies=omega/max(omega)
        self.plot_freq_response()

    def plot_freq_response(self):
        if self.mag_plot_widget:
            self.mag_plot_widget.clear()
            self.mag_plot_widget.setLabel('left', 'Magnitude (dB)')
            self.mag_plot_widget.plot(self.frequecies, self.magnitude, pen='b')
        self.phase_plot_widget.clear()
        self.phase_plot_widget.setLabel('left', 'Phase (radians)')
        self.phase_plot_widget.plot(self.frequecies,self.phase,pen='r')

    def is_within_unit_circle(self,x, y):
        return x ** 2 + y ** 2 < 1

    def mousePressEvent(self,event):
            if self.selected_zero:
                pos = event.pos()
                item_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
                self.remove_zero()
                self.selected_zero=(round(item_pos.x(),1),round(item_pos.y(),1))
                self.zeros.append(self.selected_zero)
                self.update_z_plane()
            if self.selected_pole:
                pos = event.pos()
                item_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
                temp_pole=self.selected_pole
                self.remove_pole()
                self.selected_pole = (round(item_pos.x(),1),round(item_pos.y(),1))
                if self.is_within_unit_circle(self.selected_pole[0],self.selected_pole[1]):
                    self.poles.append(self.selected_pole)
                    self.update_z_plane()
                else:
                    self.selected_pole=None
                    self.poles.append(temp_pole)
                    self.update_z_plane()


    def apply_filter(self, data):
        zeros = [complex(x, y) for x, y in self.zeros]
        poles = [complex(x, y) for x, y in self.poles]
        zeros_array = np.array(zeros)
        poles_array = np.array(poles)

        numerator, denominator = signal.zpk2tf(zeros_array, poles_array, 1)
        signal_after_filter= np.real(signal.lfilter(numerator, denominator, data))
        return signal_after_filter

    def all_pass_design(self,a,built_in_library=None,library_list=None):
        pole=a
        zero=1 / np.conj(a)
        zero_coord=(zero.real,zero.imag)
        self.zeros.append(zero_coord)
        pole_coord=(pole.real,pole.imag)
        if self.is_within_unit_circle(pole_coord[0],pole_coord[1]):
            if library_list:
                    library_list.append(a)
            built_in_library.addItem(str(a))
            self.poles.append(pole_coord)
            self.update_z_plane()
            print(self.zeros)
            print(self.poles)

    def remove_all_pass(self,a,combobox,index):
        pole=a
        zero = 1 / np.conj(a)
        zero_coord = (zero.real, zero.imag)
        pole_coord = (pole.real, pole.imag)
        if zero_coord in self.zeros and pole_coord in self.poles:
            self.plot_widget.clear()
            self.plot_unit_circle()
            self.zeros.remove(zero_coord)
            self.poles.remove(pole_coord)
            combobox.removeItem(index)
            self.update_z_plane()
    def add_all_pass_coeff(self,built_in_library,a,library_list):
        self.all_pass_design(a,built_in_library,library_list)

    def apply_all_pass_filter(self,filter_zeros,filter_poles,all_pass_zeros,all_pass_poles):
        self.zeros=list(set(filter_zeros).union(set(all_pass_zeros)))
        self.poles=list(set(filter_poles).union(set(all_pass_poles)))
        print(self.poles,self.zeros)
        self.compute_freq_response()

    def clear_all_pass(self):
        self.clear_all()






