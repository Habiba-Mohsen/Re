# IMPORTS
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pyqtgraph as pg
from PyQt5 import uic
from PyQt5.QtGui import QIcon,QKeySequence
import os
import pandas as pd
import numpy as np
from scipy import signal

# CLASSES
from filter_designer import FilterDesign

    
class RealtimeFilterDesigner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()


    def init_ui(self):
        self.ui = uic.loadUi('design.ui', self)
        self.setWindowTitle("Realtime Filter Designer")
        self.setWindowIcon(QIcon("icons/filter.png"))
        self.load_ui_elements()

        # Variables and Signals
        self.built_in_all_pass=[0.5,complex(0, 0.5),complex(0.5, 0.5)]
        self.ui.apply_btn.clicked.connect(lambda: self.change_page(1))
        self.ui.apply_btn.clicked.connect(lambda: self.edit_signal)
        self.ui.pushButton_6.clicked.connect(lambda: self.change_page(0))
        self.FilterDesigner = FilterDesign(self.z_plane_plot,self.graphicsView_2,self.graphicsView_3)
        self.all_pass_filter = FilterDesign(self.all_pass_plot,None,self.graphicsView_11)
        self.new_filter = FilterDesign(None,None,self.graphicsView_12)
        
        self.z_plane_plot.setBackground('w')
        self.graphicsView_2.setBackground('w')
        self.graphicsView_3.setBackground('w')
        self.all_pass_plot.setBackground('w')
        self.graphicsView_11.setBackground('w')
        self.graphicsView_12.setBackground('w')
        
        self.z_plane_plot.setMenuEnabled(False)
        self.z_plane_plot.scene().sigMouseClicked.connect(self.FilterDesigner.add_zero_pole)
        self.z_plane_plot.getViewBox().setLimits(xMin=-1.5, xMax=1.5, yMin=-1.5, yMax=1.5)
        self.z_plane_plot.setMouseTracking(True)
        self.z_plane_plot.mouseMoveEvent = lambda event: self.FilterDesigner.mousePressEvent(event)
        self.add_btn.clicked.connect(lambda :self.all_pass_filter.all_pass_design(self.built_in_all_pass[self.builtinCombo.currentIndex()],self.all_pass_combobox,self.built_in_all_pass))
        self.remove_btn.clicked.connect(lambda :self.all_pass_filter.remove_all_pass(self.built_in_all_pass[self.all_pass_combobox.currentIndex()-1],self.all_pass_combobox,self.all_pass_combobox.currentIndex()))
        self.add_coord.clicked.connect(lambda:self.all_pass_filter.add_all_pass_coeff(self.all_pass_combobox,complex(float(self.lineEdit.text()),float(self.lineEdit_2.text())),self.built_in_all_pass))
        self.apply_all_pass_btn.clicked.connect(lambda:self.new_filter.apply_all_pass_filter(self.FilterDesigner.zeros,self.FilterDesigner.poles,self.all_pass_filter.zeros,self.all_pass_filter.poles))
        self.pushButton.clicked.connect(lambda:self.all_pass_filter.clear_all_pass())
        self.sampling_rate = 1
        self.data = []
        
        # SHORTCUTS
        self.clear_zeros_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.clear_poles_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.clear_all_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.remove_zero_shortcut =QShortcut(QKeySequence("Ctrl+R"),self)
        self.remove_pole_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.add_conjugate_shortcut=QShortcut(QKeySequence("Ctrl+A"),self)

        # Connecting shortcuts
        self.clear_zeros_shortcut.activated.connect(self.FilterDesigner.clear_zeros)
        self.clear_poles_shortcut.activated.connect(self.FilterDesigner.clear_poles)
        self.clear_all_shortcut.activated.connect(self.FilterDesigner.clear_all)
        self.add_conjugate_shortcut.activated.connect(self.FilterDesigner.add_conjugate)
        self.remove_zero_shortcut.activated.connect(self.FilterDesigner.remove_zero)
        self.remove_pole_shortcut.activated.connect(self.FilterDesigner.remove_pole)




    def load_ui_elements(self):  
        # Realtime-Signal
        self.realSignalgraph.getViewBox().setLimits(xMin=0)
        self.filteredSignalgraph.getViewBox().setLimits(xMin=0)
        self.Touchpad.getViewBox().setLimits(xMin=0)
        self.Touchpad.getViewBox().setLimits(yMin=0)
        
        self.loadButton.clicked.connect(self.uploadFile)
        self.btn_play.clicked.connect(self.toggle_animation)
        self.clearButton.clicked.connect(self.clear_plots)
        self.radioButton_2.clicked.connect(self.change_mode)
        self.radioButton.clicked.connect(self.change_mode)
        
        self.is_animation_running = False
        self.is_signal_ended = False
        self.current_index = 0
        self.counter_max = 0  
        self.mode = 'Load'

        self.signalItemInput = pg.PlotDataItem([], pen = 'b', width = 5)
        self.signalItemFiltered = pg.PlotDataItem([], pen = 'r', width = 5)
        self.realSignalgraph.setBackground('w')
        self.filteredSignalgraph.setBackground('w')
        self.ui.realSignalgraph.addItem(self.signalItemInput)
        self.ui.filteredSignalgraph.addItem(self.signalItemFiltered)
        self.btn_play.setIcon(QIcon('icons/play.png'))

        # Touchpad 
        self.x_data = [0]  # Store x coordinates for signal generation
        
        # Connect the sigMouseMoved signal to the on_mouse_move method in init_UI
        self.ui.Touchpad.scene().sigMouseMoved.connect(self.on_mouse_click)
        
        # Hide AXES
        self.Touchpad.getAxis('left').setPen(pg.mkPen(color=(0, 0, 0, 0)))
        self.Touchpad.getAxis('left').setTextPen(pg.mkPen(color=(0, 0, 0, 0)))

        # Hide the bottom axis
        self.Touchpad.getAxis('bottom').setPen(pg.mkPen(color=(0, 0, 0, 0)))
        self.Touchpad.getAxis('bottom').setTextPen(pg.mkPen(color=(0, 0, 0, 0)))
        #real time signal timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.ui.speedSlider.valueChanged.connect(self.change_sr) # Set Animation speed when slide is changed
        
        
    def uploadFile(self):
        try:
            self.clear_plots()
            # Get the script directory and set the initial folder for file dialog
            script_directory = os.path.dirname(os.path.abspath(__file__))
            initial_folder = os.path.join(script_directory, "Data")

            # Display the file dialog to get the selected file
            file_name, _ = QFileDialog.getOpenFileName(
                self, 'Open File', initial_folder, "CSV files (*.csv)"
            )
            
            # Check if the user canceled the file dialog
            if not file_name:
                return

            # Read the CSV file using pandas
            df = pd.read_csv(file_name)

            # Extract data from the specified column
            data_col = 'Data'
            data = df[data_col].values
            
            # Set the flag indicating that data has been opened
            self.data_opened = True

            self.signal_data = data
            if len(self.new_filter.poles)>0 and len(self.new_filter.zeros)>0:
                self.filtered_signal_data = self.new_filter.apply_filter(data)
                print("with all pass")
            else:
                self.filtered_signal_data=self.FilterDesigner.apply_filter(data)
                print("without all pass")
            # Filtered
            self.toggle_animation()
            self.btn_play.setEnabled(True)
            self.speedSlider.setEnabled(True)
            
            # Reset the viewport range and update the plotted data
            self.reset_viewport_range()
            self.ui.realSignalgraph.setData(self.signal_data[0:self.current_index])
            self.ui.filteredSignalgraph.setData(self.filtered_signal_data[0:self.current_index])
            
            
            
            
        except Exception as e:
            print(f"Error: {e}")
      
    def change_mode(self):
        if self.mode == 'Load':
            self.btn_play.setEnabled(False)
            self.speedSlider.setEnabled(False)
            self.loadButton.setEnabled(False)
            self.Touchpad.setEnabled(True)
            self.clear_plots()
            self.mode = 'TouchPad'
        else:
            self.btn_play.setEnabled(True)
            self.speedSlider.setEnabled(True)
            self.loadButton.setEnabled(True)
            self.Touchpad.setEnabled(False)
            self.clear_plots()
            self.mode = 'Load'
                       
    def reset_viewport_range(self):
        for plot in [self.ui.filteredSignalgraph, self.ui.realSignalgraph]:
            plot.setRange(xRange=[0, 1000])
            
    def change_sr(self):
        self.sampling_rate = int(self.ui.speedSlider.value())
        
    def set_play_button_state(self):
        if self.is_animation_running == True:
            self.btn_play.setIcon(QIcon('icons/pause.png'))
        else:
            self.btn_play.setIcon(QIcon('icons/play.png'))
    
    def stop_animation(self):
        print("animation stopped")
        self.animation_timer.stop()
        self.is_animation_running = False
        self.set_play_button_state()
    
    def play_animation(self):
        if self.is_signal_ended:
            print("Signal Ended")
            self.current_index = 0
            self.reset_viewport_range()
            self.is_signal_ended = False
        print("animation playing")
        self.animation_timer.start(1000)
        self.is_animation_running = True
        self.set_play_button_state()
        
    def toggle_animation(self):
        self.is_animation_running = not self.is_animation_running

        if self.is_animation_running:
            self.play_animation()
        else:
            self.stop_animation()
            
    def update_animation(self):
        x_min , x_max = self.ui.realSignalgraph.viewRange()[0]
        self.signalItemInput.setData(self.signal_data[0:self.current_index])

        self.signalItemFiltered.setData(self.filtered_signal_data[0:self.current_index])

        if self.current_index > x_max:   
            for viewport in [self.ui.filteredSignalgraph, self.ui.realSignalgraph]:
                viewport.setLimits(xMax = self.current_index)
                viewport.getViewBox().translateBy(x = self.sampling_rate)
        
        if self.current_index >= len(self.signal_data)-1:
            self.stop_animation()
            self.is_signal_ended = True
        
        self.current_index += self.sampling_rate # Convert the speed value to integer
        QApplication.processEvents()
        
    def on_mouse_click(self, pos):
        if self.ui.radioButton_2.isChecked():
            
            pos = self.ui.Touchpad.getViewBox().mapSceneToView(pos)
            signal_value =pos.y()
            self.counter_max += 1
            self.x_data.append(signal_value)

            if len(self.new_filter.poles) > 0 and len(self.new_filter.zeros) > 0:
                self.fltr_data = self.new_filter.apply_filter(self.x_data) # Filtered Signal
            else:
                self.fltr_data = self.FilterDesigner.apply_filter(self.x_data)

            
            # Update signalItemInput and signalItemFiltered data
            self.signalItemInput.setData(self.x_data)
            self.signalItemFiltered.setData(self.fltr_data) 
            
            # Adjust x_min and x_max for plotting
            x_max = len(self.x_data)
            x_min = max(0, x_max - 200)

            # SetRange for real-time plots
            self.ui.realSignalgraph.setRange(xRange=[x_min, x_max])
            self.ui.filteredSignalgraph.setRange(xRange=[x_min, x_max])

    def clear_plots(self):
        self.x_data = [0, 0]
        self.fltr_data = [0, 0]
        self.signal_data = [0, 0]
        self.filtered_signal_data = [0, 0]
        self.signalItemInput.setData([0])
        self.signalItemFiltered.setData([0])
        self.current_index = 0

    def edit_signal(self):
        if self.radioButton.isChecked():
            self.update_animation()


    def change_page(self, mode):
        if mode == 1:
            self.ui.stackedWidget.setCurrentIndex(mode)
        else:
            self.ui.stackedWidget.setCurrentIndex(mode)    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = RealtimeFilterDesigner()
    mainWin.show()
    sys.exit(app.exec())
