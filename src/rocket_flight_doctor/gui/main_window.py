import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QListWidget, QSplitter, 
                               QFileDialog, QPushButton)
from PySide6.QtCore import Qt
import pyqtgraph as pg

from ..parsers import get_parser_for_file
from ..analysis.events import detect_liftoff, detect_burnout, detect_apogee
from ..physics.kinematics import derive_velocity
from ..analysis.autopsy import check_apogee_discrepancy, analyze_coast_drag, check_boost_discrepancy

class FlightDoctorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rocket Flight Doctor - Autopsy")
        self.resize(1200, 800)
        
        self.flight_df = None
        self.sim_df = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left Panel (Autopsy & Controls)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        btn_load = QPushButton("Load Flight Data")
        btn_load.clicked.connect(self.load_flight_data)
        left_layout.addWidget(btn_load)
        
        btn_sim = QPushButton("Load Simulation")
        btn_sim.clicked.connect(self.load_sim_data)
        left_layout.addWidget(btn_sim)
        
        btn_demo = QPushButton("Load Synthetic Demo")
        btn_demo.clicked.connect(self.load_demo)
        left_layout.addWidget(btn_demo)
        
        left_layout.addWidget(QLabel("<b>Flight Autopsy Findings</b>"))
        self.findings_list = QListWidget()
        self.findings_list.setWordWrap(True)
        left_layout.addWidget(self.findings_list)
        
        # Right Panel (Plots)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.plot_widget = pg.GraphicsLayoutWidget()
        right_layout.addWidget(self.plot_widget)
        
        # Setup plots
        self.p_alt = self.plot_widget.addPlot(title="Altitude vs Time", row=0, col=0)
        self.p_alt.setLabel('left', 'Altitude', units='m')
        
        self.p_vel = self.plot_widget.addPlot(title="Velocity vs Time", row=1, col=0)
        self.p_vel.setLabel('left', 'Velocity', units='m/s')
        self.p_vel.setXLink(self.p_alt)
        
        self.p_acc = self.plot_widget.addPlot(title="Acceleration vs Time", row=2, col=0)
        self.p_acc.setLabel('left', 'Acceleration', units='m/s²')
        self.p_acc.setXLink(self.p_alt)
        
        # Shared X axis line
        self.vLine1 = pg.InfiniteLine(angle=90, movable=False)
        self.vLine2 = pg.InfiniteLine(angle=90, movable=False)
        self.vLine3 = pg.InfiniteLine(angle=90, movable=False)
        self.p_alt.addItem(self.vLine1)
        self.p_vel.addItem(self.vLine2)
        self.p_acc.addItem(self.vLine3)
        
        self.proxy = pg.SignalProxy(self.p_alt.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 900])
        
    def mouseMoved(self, evt):
        pos = evt[0]
        if self.p_alt.sceneBoundingRect().contains(pos):
            mousePoint = self.p_alt.vb.mapSceneToView(pos)
            x = mousePoint.x()
            self.vLine1.setPos(x)
            self.vLine2.setPos(x)
            self.vLine3.setPos(x)

    def load_flight_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Telemetry CSV", "", "CSV Files (*.csv)")
        if file_path:
            parser = get_parser_for_file(Path(file_path))
            self.flight_df = parser.parse(Path(file_path))
            self.update_analysis()
            
    def load_sim_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Simulation CSV", "", "CSV Files (*.csv)")
        if file_path:
            # For simplicity, assuming OpenRocket parser
            from ..parsers.openrocket import OpenRocketParser
            parser = OpenRocketParser()
            self.sim_df = parser.parse(Path(file_path))
            self.update_analysis()
            
    def load_demo(self):
        from ..analysis.synthetic import generate_synthetic_flight
        self.flight_df, self.sim_df = generate_synthetic_flight()
        self.update_analysis()
        
    def update_analysis(self):
        if self.flight_df is None:
            return
            
        self.p_alt.clear()
        self.p_vel.clear()
        self.p_acc.clear()
        
        self.findings_list.clear()
        self.p_alt.addItem(self.vLine1)
        self.p_vel.addItem(self.vLine2)
        self.p_acc.addItem(self.vLine3)
        
        df = self.flight_df.copy()
        
        # Ensure derived metrics
        if 'velocity_z_m_s' not in df.columns and 'altitude_baro_m' in df.columns:
            df['velocity_z_m_s'] = derive_velocity(df['time_s'].values, df['altitude_baro_m'].values)
            
        liftoff = detect_liftoff(df)
        if liftoff:
            df['time_s'] -= liftoff.timestamp_s
            
        burnout = detect_burnout(df, 0.0) if liftoff else None
        apogee = detect_apogee(df)
        
        # Plot flight
        t = df['time_s'].values
        if 'altitude_baro_m' in df.columns:
            self.p_alt.plot(t, df['altitude_baro_m'].values, pen='y', name="Measured Altitude")
        if 'velocity_z_m_s' in df.columns:
            self.p_vel.plot(t, df['velocity_z_m_s'].values, pen='y', name="Measured Velocity")
        if 'accel_z_m_s2' in df.columns:
            self.p_acc.plot(t, df['accel_z_m_s2'].values, pen='y', name="Measured Acceleration")
            
        # Plot sim
        if self.sim_df is not None:
            st = self.sim_df['time_s'].values
            if 'altitude_m' in self.sim_df.columns:
                self.p_alt.plot(st, self.sim_df['altitude_m'].values, pen=pg.mkPen('c', style=Qt.DashLine), name="Sim Altitude")
            if 'velocity_z_m_s' in self.sim_df.columns:
                self.p_vel.plot(st, self.sim_df['velocity_z_m_s'].values, pen=pg.mkPen('c', style=Qt.DashLine), name="Sim Velocity")
            if 'acceleration_z_m_s2' in self.sim_df.columns:
                self.p_acc.plot(st, self.sim_df['acceleration_z_m_s2'].values, pen=pg.mkPen('c', style=Qt.DashLine), name="Sim Acceleration")
                
            # Autopsy
            findings = []
            if apogee:
                findings.extend(check_apogee_discrepancy(df, self.sim_df, apogee))
            if burnout and apogee:
                findings.extend(analyze_coast_drag(df, self.sim_df, burnout, apogee))
            if liftoff and burnout:
                findings.extend(check_boost_discrepancy(df, self.sim_df, liftoff, burnout))
                
            for f in findings:
                self.findings_list.addItem(f"{f.severity.value}: {f.title}\n{f.description}")
                
def launch_gui():
    app = QApplication(sys.argv)
    window = FlightDoctorWindow()
    window.show()
    sys.exit(app.exec())
