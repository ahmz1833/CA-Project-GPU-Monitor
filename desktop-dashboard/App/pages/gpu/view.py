from PySide6.QtCore import QTimer, QThread, Signal, QObject
from PySide6.QtWidgets import QPushButton, QWidget, QScrollArea, QVBoxLayout

from App.logic.Logic import GPUMonitor
from App.pages.base_page import BasePage
from App.pages.gpu.controller import Controller
from App.widgets.MainLayout import MainLayout
from App.widgets.Plot2D import Plot2D
from App.widgets.Separator import Separator
from App.widgets.TwoSwitch import TwoSwitch


class DataFetcher(QThread):
    data_ready = Signal(dict)

    def __init__(self, monitor, gpu_index: int, parent: QObject = None):
        super().__init__(parent)
        self.gpu_index = gpu_index
        self.monitor = monitor
        self._running = True

    def run(self):
        if not self._running:
            return
        data = {}
        metrics = self.monitor.get_available_metrics(self.gpu_index)
        for metric in metrics:
            history = self.monitor.get_gpu_metric(self.gpu_index, metric)
            data[metric] = history or []
        self.data_ready.emit(data)

    def stop(self):
        self._running = False


class View(BasePage):
    def __init__(self, router):
        super().__init__(router)
        self.controller = Controller(self, router)
        self.gpu_index = None

        self.plots = {}
        self.switches = {}

        self.timer = QTimer(self)
        self._worker = None
        self.monitor = GPUMonitor()

    def _setup_ui(self):
        if self.layout():
            old_layout = self.layout()
            self._clear_layout(old_layout)
            QWidget().setLayout(old_layout)

        self.main_layout = MainLayout(f"GPU NO.{self.controller.index}")
        self.setLayout(self.main_layout)

        self.back_btn = QPushButton("Back")
        self.set = QPushButton("Restart")

        self.main_layout.add_button(self.back_btn)
        self.main_layout.add_button(self.set, role="success")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.plots_layout = QVBoxLayout(container)
        scroll.setWidget(container)
        self.main_layout.set_main_content(scroll)

        self.gpu_index = self.controller.index
        self._create_all_plots()
        self.connect_buttons()
        self._init_timer_and_worker()

    def _create_all_plots(self):
        metrics = GPUMonitor().get_available_metrics(self.gpu_index)
        for metric in metrics:
            plot = Plot2D(
                title=metric.replace('_', ' ').title(),
                x_label="Time",
                y_label=metric.split('_')[-1]
            )
            self.plots[metric] = plot

            label = metric.replace('_', ' ').title()
            switch = TwoSwitch(f"{label}: hide", "show")
            self.switches[metric] = switch
            self.main_layout.add_parameter_widget(switch)

            self.plots_layout.addWidget(plot)
            self.plots_layout.addWidget(Separator())

    def connect_buttons(self):
        self.back_btn.clicked.connect(self.controller.back)
        self.set.clicked.connect(self._on_restart_clicked)

    def _on_restart_clicked(self):
        for metric, switch in self.switches.items():
            visible = bool(switch.value)
            plot = self.plots[metric]
            plot.setVisible(visible)

            idx = self.plots_layout.indexOf(plot) + 1
            item = self.plots_layout.itemAt(idx)
            if item and item.widget():
                item.widget().setVisible(visible)

    def _init_timer_and_worker(self):
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self._start_fetcher)
        self.timer.start()
        self._start_fetcher()

    def _start_fetcher(self):
        if self._worker and self._worker.isRunning():
            return
        self._worker = DataFetcher(self.monitor, self.gpu_index)
        self._worker.data_ready.connect(self._on_new_data)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self):
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def _on_new_data(self, data: dict):
        for metric, history in data.items():
            plot = self.plots.get(metric)
            if not plot or not history:
                continue
            timestamps, values = zip(*history)
            plot.clear_plot()
            plot.plot_points(timestamps, values, label=metric.replace('_', ' '))

    def cleanup(self):
        self.timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
            elif sublayout := item.layout():
                self._clear_layout(sublayout)
        layout.deleteLater()
