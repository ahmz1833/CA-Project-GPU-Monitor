import random

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                               QSizePolicy, QHBoxLayout, QSpacerItem)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from App.utils.Loader import Loader


class Plot2D(QWidget):
    def __init__(self, title, x_label, y_label, have_grid=True, parent=None, editable=False):
        super().__init__(parent)

        self._is_panning = False
        self.editable = editable
        self._edit_mode = False
        self.editable_points = []
        self._dragged_point = None
        self._drag_offset = (0, 0)
        is_dark = Loader().is_dark()

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)

        self.is_dark_theme = is_dark
        if is_dark:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.canvas)
        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.reset_button = QPushButton("Reset Plot View")
        self.reset_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.reset_button.clicked.connect(self.reset_view)
        button_layout.addWidget(self.reset_button)
        button_layout.addSpacing(10)
        self.save_button = QPushButton("Save Plot")
        self.save_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.save_button.clicked.connect(self._save_plot_dialog)
        button_layout.addWidget(self.save_button)
        if self.editable:
            button_layout.addSpacing(10)
            self.edit_button = QPushButton("Change Points")
            self.edit_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.edit_button.setCheckable(True)
            self.edit_button.clicked.connect(self._toggle_edit_mode)
            button_layout.addWidget(self.edit_button)
            self.clear_points_button = QPushButton("Clear Points")
            self.clear_points_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.clear_points_button.clicked.connect(self._clear_user_points)
            self.clear_points_button.setVisible(False)
            button_layout.addWidget(self.clear_points_button)
        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.current_color_index = 0
        self.plotted_items = []
        self._drag_start = None
        self._drag_origin = None
        self._zoom_factor = 1.1
        self._pan_button = Qt.MouseButton.LeftButton
        self._zoom_button = Qt.MouseButton.RightButton
        self.canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.canvas.setFocus()
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.canvas.setMinimumSize(400, 400)

        self.set_title(title)
        self.set_labels(x_label, y_label)
        self.set_grid(have_grid)

    def _apply_dark_theme(self):
        self.color_cycle = [
            '#00FFFF', '#FF00FF', '#FFFF00', '#00FF00', '#FF4500',
            '#1E90FF', '#FF1493', '#7CFC00', '#FF8C00', '#BA55D3'
        ]
        self.figure.set_facecolor('#31363B')
        self.axes.set_facecolor('#1f1f1f')
        self.axes.title.set_color('white')
        self.axes.xaxis.label.set_color('white')
        self.axes.yaxis.label.set_color('white')
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        for spine in self.axes.spines.values():
            spine.set_color('#4F5B62')
        self.axes.grid(True, color='gray', linestyle='-', alpha=0.2)

    def _apply_light_theme(self):
        self.color_cycle = [
            '#007acc', '#ff6f61', '#2ec27e', '#f6c700', '#c061cb',
            '#ff4b00', '#20a4f3', '#e71d36', '#6a4c93', '#00bfae',
        ]

        self.figure.set_facecolor('#E6E6E6')
        self.axes.set_facecolor('white')
        self.axes.title.set_color('red')
        self.axes.xaxis.label.set_color('red')
        self.axes.yaxis.label.set_color('red')
        self.axes.tick_params(axis='x', colors='red')
        self.axes.tick_params(axis='y', colors='red')
        for spine in self.axes.spines.values():
            spine.set_color('black')
        self.axes.grid(True, color='gray', linestyle='-', alpha=0.3)

    def _toggle_edit_mode(self):
        self._edit_mode = not self._edit_mode
        self.edit_button.setChecked(self._edit_mode)
        self.clear_points_button.setVisible(self._edit_mode)

        if self._edit_mode:
            self.edit_button.setText("Editing Points...")
            for point_data in self.editable_points:
                point_data['line'].set_picker(5)
        else:
            self.edit_button.setText("Change Points")
            for point_data in self.editable_points:
                point_data['line'].set_picker(False)
        self.canvas.draw()

    def _clear_user_points(self):
        for point_data in self.editable_points:
            if point_data['line'] in self.plotted_items:
                self.plotted_items.remove(point_data['line'])
            point_data['line'].remove()
        self.editable_points = []
        self.canvas.draw()

    def get_user_points(self):
        return [(p['x'][0], p['y'][0]) for p in self.editable_points]

    def _on_press(self, event):
        if self._edit_mode and event.inaxes:
            if event.button == 1:
                for point_data in self.editable_points:
                    line = point_data['line']
                    contains, _ = line.contains(event)
                    if contains:
                        self._dragged_point = point_data
                        self._drag_offset = (event.xdata - point_data['x'][0],
                                             event.ydata - point_data['y'][0])
                        return
                self.add_point(event.xdata, event.ydata)
                return

            elif event.button == 3:
                closest_point = None
                min_dist = float('inf')

                for point_data in self.editable_points:
                    x, y = point_data['x'][0], point_data['y'][0]
                    dist = np.sqrt((event.xdata - x) ** 2 + (event.ydata - y) ** 2)

                    if dist < min_dist:
                        min_dist = dist
                        closest_point = point_data

                if closest_point and min_dist < 0.5:
                    self._remove_point(closest_point)
                return

        if event.button == 1 and not self._edit_mode:
            self._is_panning = True
            self._drag_start = (event.x, event.y)
            self._drag_origin = (self.axes.get_xlim(), self.axes.get_ylim())

    def add_point(self, x, y):
        point, = self.axes.plot([x], [y], 'ro', markersize=8, picker=5)
        self.plotted_items.append(point)
        point_data = {
            'line': point,
            'x': np.array([x]),
            'y': np.array([y])
        }
        self.editable_points.append(point_data)
        self.canvas.draw()

    def _remove_point(self, point_data):
        if point_data in self.editable_points:
            if point_data['line'] in self.plotted_items:
                self.plotted_items.remove(point_data['line'])
            point_data['line'].remove()

            self.editable_points.remove(point_data)
            self.canvas.draw()

    def _on_motion(self, event):
        if self._edit_mode and hasattr(self, '_dragged_point') and self._dragged_point and event.inaxes:
            point_data = self._dragged_point
            new_x = event.xdata - self._drag_offset[0]
            new_y = event.ydata - self._drag_offset[1]

            point_data['x'][0] = new_x
            point_data['y'][0] = new_y
            point_data['line'].set_data([new_x], [new_y])
            self.canvas.draw_idle()
            return

        if not self._is_panning or self._drag_start is None or self._drag_origin is None:
            return

        if not event.inaxes:
            return

        dx = (event.x - self._drag_start[0]) / self.canvas.width()
        dy = - (self._drag_start[1] - event.y) / self.canvas.height()

        xlim, ylim = self._drag_origin
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]

        new_xlim = (xlim[0] - dx * x_range, xlim[1] - dx * x_range)
        new_ylim = (ylim[0] - dy * y_range, ylim[1] - dy * y_range)

        self.axes.set_xlim(new_xlim)
        self.axes.set_ylim(new_ylim)
        self.canvas.draw_idle()

    def _on_release(self, event):
        if hasattr(self, '_dragged_point'):
            del self._dragged_point

        if event.button == 1:
            self._is_panning = False
            self._drag_start = None
            self._drag_origin = None

    def _on_scroll(self, event):
        if not event.inaxes or self._edit_mode:
            return

        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        xdata, ydata = event.xdata, event.ydata

        if event.button == 'up':
            scale_factor = 1 / self._zoom_factor
        else:
            scale_factor = self._zoom_factor

        new_xlim = [
            xdata - (xdata - xlim[0]) * scale_factor,
            xdata + (xlim[1] - xdata) * scale_factor
        ]

        new_ylim = [
            ydata - (ydata - ylim[0]) * scale_factor,
            ydata + (ylim[1] - ydata) * scale_factor
        ]

        self.axes.set_xlim(new_xlim)
        self.axes.set_ylim(new_ylim)
        self.canvas.draw()

    def _on_key_press(self, event):
        pass

    def plot_function(self, func, x_range=(-10, 10), num_points=500, label=None, color=None, linewidth=1.5):
        x = np.linspace(x_range[0], x_range[1], num_points)
        y = func(x)

        if color is None:
            color = random.choice(self.color_cycle)
            self.current_color_index += 1

        line, = self.axes.plot(x, y, color=color, linewidth=linewidth, label=label)
        self.plotted_items.append(line)

        self.axes.relim()
        self.axes.autoscale_view()
        self._update_legend()
        self.canvas.draw()

    def plot_points(self, x, y, label=None, color=None, marker='o', linestyle='-', linewidth=1.5, editable=False,
                    markersize=1):
        if color is None:
            color = random.choice(self.color_cycle)
            self.current_color_index += 1

        if linestyle != 'None' and len(x) > 1:
            connector, = self.axes.plot(x, y, color=color, linestyle=linestyle,
                                        linewidth=linewidth, alpha=0.5)
            self.plotted_items.append(connector)

        points, = self.axes.plot(x, y, color=color, marker=marker, linestyle='None',
                                 markersize=markersize, label=label)
        self.plotted_items.append(points)

        if editable and self.editable:
            for i, (xi, yi) in enumerate(zip(x, y)):
                point_data = {
                    'line': self.axes.plot([xi], [yi], 'ro', markersize=8)[0],
                    'x': np.array([xi]),
                    'y': np.array([yi]),
                    'original_x': xi,
                    'original_y': yi
                }
                self.editable_points.append(point_data)
                self.plotted_items.append(point_data['line'])

        self.axes.relim()
        self.axes.autoscale_view()
        self._update_legend()
        self.canvas.draw()

    def reset_view(self):
        self.axes.autoscale()
        self.canvas.draw()

    def _save_plot_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;PDF Files (*.pdf);;All Files (*)",
            options=options
        )
        if file_name:
            self.figure.savefig(file_name, dpi=300, bbox_inches='tight')

    def set_title(self, title):
        self.axes.set_title(title)
        self.canvas.draw()

    def set_labels(self, x_label, y_label):
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.canvas.draw()

    def set_grid(self, visible=True):
        self.axes.grid(visible)
        self.canvas.draw()

    def _update_legend(self):
        handles, labels = self.axes.get_legend_handles_labels()

        if handles:
            self.axes.legend(handles, labels)
        elif hasattr(self.axes, 'legend_'):
            self.axes.legend_.remove()

    def get_editable_points(self):
        return [(p['x'][0], p['y'][0]) for p in self.editable_points]

    def clear_plot(self, clear_user_points=True):
        if clear_user_points:
            self._clear_user_points()

        for item in self.plotted_items:
            item.remove()
        self.plotted_items = []
        self.current_color_index = 0
        if hasattr(self.axes, 'legend_'):
            try:
                self.axes.legend_.remove()
            except AttributeError:
                pass
        self.canvas.draw()
