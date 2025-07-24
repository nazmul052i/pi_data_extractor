import hashlib
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtCharts import QChart, QLineSeries, QDateTimeAxis, QValueAxis, QChartView
from .widgets import ModernButton, ZoomableChartView


class ChartManager(QWidget):
    """Manages chart creation, display, and lifecycle for PI data visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.data_frame = pd.DataFrame()
        self.descriptions = {}
        self.units = {}
        self.chart_widgets = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the chart container UI"""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)
        
        # Chart controls header
        self.create_chart_controls()
        
        # Instructions label (shown when no charts)
        self.instructions_label = QLabel("📈 Charts will appear here when you check tags in the Tags tab")
        self.instructions_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 20px;
                text-align: center;
                background-color: #F9F9F9;
                border: 2px dashed #CCC;
                border-radius: 8px;
                margin: 20px;
                font-style: italic;
            }
        """)
        self.instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.instructions_label)
        
        self.setLayout(self.layout)
    
    def create_chart_controls(self):
        """Create chart control buttons"""
        controls_layout = QHBoxLayout()
        
        # Info label
        info_label = QLabel("📊 Data Visualization")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px;
            }
        """)
        
        # Control buttons
        self.refresh_btn = ModernButton("🔄 Refresh Charts", color="#2196F3")
        self.refresh_btn.clicked.connect(self.refresh_charts)
        self.refresh_btn.setToolTip("Refresh charts based on currently selected tags")
        
        self.clear_btn = ModernButton("🗑️ Clear All", color="#FF6B6B")
        self.clear_btn.clicked.connect(self.clear_all_charts)
        self.clear_btn.setToolTip("Remove all charts from display")
        
        self.reset_zoom_all_btn = ModernButton("🔍 Reset All Zoom", color="#9C27B0")
        self.reset_zoom_all_btn.clicked.connect(self.reset_all_zoom)
        self.reset_zoom_all_btn.setToolTip("Reset zoom level for all charts")
        
        controls_layout.addWidget(info_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(self.reset_zoom_all_btn)
        controls_layout.addWidget(self.clear_btn)
        
        self.layout.addLayout(controls_layout)
    
    def set_data(self, dataframe, descriptions=None, units=None):
        """Set the data for chart generation"""
        self.data_frame = dataframe.copy() if not dataframe.empty else pd.DataFrame()
        self.descriptions = descriptions or {}
        self.units = units or {}
    
    def update_charts_for_tags(self, selected_tags):
        """Update charts based on selected tags"""
        if self.data_frame.empty:
            self.show_no_data_message("No data available. Please fetch data first.")
            return
        
        # Clear existing charts
        self.clear_all_charts()
        
        if not selected_tags:
            self.show_instructions()
            return
        
        # Hide instructions
        self.instructions_label.setVisible(False)
        
        # Create charts for selected tags
        valid_charts = 0
        for tag in selected_tags:
            if tag in self.data_frame.columns:
                chart_widget = self.create_tag_chart(tag)
                if chart_widget:
                    self.layout.addWidget(chart_widget)
                    self.chart_widgets.append(chart_widget)
                    valid_charts += 1
        
        if valid_charts == 0:
            self.show_no_data_message("Selected tags not found in current dataset.")
        
        # Log the operation if parent has logging
        if hasattr(self.parent_window, 'log_output') and valid_charts > 0:
            self.parent_window.log_output.append(f"📈 Created {valid_charts} chart(s)")
    
    def create_tag_chart(self, tag, height=250):
        """Create a chart for a single tag"""
        if tag not in self.data_frame.columns:
            return None
        
        try:
            # Get valid data for the tag
            times, values = self.get_valid_series_data(tag)
            
            if len(times) == 0 or len(values) == 0:
                return self.create_no_data_chart(tag, "No valid data points found")
            
            # Create chart
            chart = QChart()
            chart.setBackgroundBrush(QColor(245, 245, 245))
            chart.legend().setVisible(True)
            chart.setTitle(f"{tag}")
            chart.setTitleBrush(QColor(51, 51, 51))
            
            # Create series
            series = QLineSeries()
            series.setName(tag)
            
            # Generate color based on tag name hash
            tag_hash = int(hashlib.md5(tag.encode()).hexdigest()[:6], 16)
            series_color = QColor(
                (tag_hash >> 16) & 255, 
                (tag_hash >> 8) & 255, 
                tag_hash & 255
            )
            series.setColor(series_color)
            
            # Add data points
            for time_val, data_val in zip(times, values):
                try:
                    if pd.notna(data_val):
                        timestamp_ms = int(time_val.timestamp() * 1000)
                        series.append(timestamp_ms, float(data_val))
                except (ValueError, TypeError, OverflowError):
                    continue
            
            if series.count() == 0:
                return self.create_no_data_chart(tag, "No plottable data points")
            
            chart.addSeries(series)
            
            # Setup X-axis (time)
            axis_x = QDateTimeAxis()
            axis_x.setFormat("MM-dd HH:mm")
            axis_x.setTitleText("Time")
            
            if len(times) > 0:
                time_min = QDateTime.fromMSecsSinceEpoch(int(times.min().timestamp() * 1000))
                time_max = QDateTime.fromMSecsSinceEpoch(int(times.max().timestamp() * 1000))
                axis_x.setRange(time_min, time_max)
            
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)
            
            # Setup Y-axis (values)
            axis_y = QValueAxis()
            unit = self.units.get(tag, "").strip()
            y_title = f"{tag} ({unit})" if unit else tag
            axis_y.setTitleText(y_title)
            
            # Set Y-axis range with buffer
            if len(values) > 0:
                y_min, y_max = float(values.min()), float(values.max())
                if y_max > y_min:
                    buffer = (y_max - y_min) * 0.05
                    axis_y.setRange(y_min - buffer, y_max + buffer)
                else:
                    axis_y.setRange(y_min - 1.0, y_max + 1.0)
            
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_y)
            
            # Create chart view with zoom capabilities
            chart_view = ZoomableChartView(chart)
            chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            chart_view.setMinimumHeight(height)
            chart_view.setRubberBand(QChartView.RubberBand.RectangleRubberBand)
            
            # Create container with reset zoom button
            container = self.create_chart_container(chart_view, tag)
            return container
            
        except Exception as e:
            if hasattr(self.parent_window, 'log_output'):
                self.parent_window.log_output.append(f"❌ Failed to create chart for {tag}: {str(e)}")
            return self.create_error_chart(tag, str(e))
    
    def create_chart_container(self, chart_view, tag_name):
        """Create a container widget with chart and controls"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        
        # Chart controls
        controls_layout = QHBoxLayout()
        
        # Tag info
        tag_info = QLabel(f"📊 {tag_name}")
        description = self.descriptions.get(tag_name, "")
        if description:
            tag_info.setToolTip(f"Description: {description}")
        tag_info.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #333;
                padding: 2px 5px;
            }
        """)
        
        # Reset zoom button
        reset_btn = ModernButton("🔄 Reset Zoom", color="#607D8B")
        reset_btn.setFixedWidth(120)
        reset_btn.clicked.connect(chart_view.reset_zoom)
        reset_btn.setToolTip("Reset zoom level for this chart")
        
        controls_layout.addWidget(tag_info)
        controls_layout.addStretch()
        controls_layout.addWidget(reset_btn)
        
        container_layout.addLayout(controls_layout)
        container_layout.addWidget(chart_view)
        
        # Add styling to container
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        return container
    
    def create_no_data_chart(self, tag_name, message):
        """Create a placeholder chart when no data is available"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        no_data_label = QLabel(f"📊 {tag_name}\n\n⚠️ {message}")
        no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_data_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 14px;
                padding: 40px;
                background-color: #FAFAFA;
                border: 2px dashed #DDD;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        
        layout.addWidget(no_data_label)
        container.setMinimumHeight(200)
        
        return container
    
    def create_error_chart(self, tag_name, error_message):
        """Create an error chart when chart creation fails"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        error_label = QLabel(f"📊 {tag_name}\n\n❌ Chart Error:\n{error_message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                color: #D32F2F;
                font-size: 12px;
                padding: 30px;
                background-color: #FFEBEE;
                border: 2px solid #FFCDD2;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        
        layout.addWidget(error_label)
        container.setMinimumHeight(150)
        
        return container
    
    def get_valid_series_data(self, tag):
        """Extract valid time series data for a tag"""
        # Check for status column (good quality data)
        status_col = f"{tag}_Status"
        if status_col in self.data_frame.columns:
            mask = self.data_frame[status_col] == 'G'
        else:
            # If no status column, use all non-null values
            mask = pd.notna(self.data_frame[tag])
        
        # Get times and values
        times = pd.to_datetime(self.data_frame["Timestamp"])[mask]
        values = self.data_frame[tag][mask]
        
        valid_mask = pd.notna(values)
        times = times[valid_mask]
        values = values[valid_mask]
        
        return times, values
    
    def show_instructions(self):
        """Show the instructions label"""
        self.instructions_label.setVisible(True)
    
    def show_no_data_message(self, message):
        """Show a no data message"""
        self.clear_all_charts()
        
        no_data_label = QLabel(f"ℹ️ {message}")
        no_data_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 20px;
                text-align: center;
                background-color: #FFF9C4;
                border: 2px solid #FFF176;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(no_data_label)
        self.chart_widgets.append(no_data_label)
    
    def clear_all_charts(self):
        """Remove all chart widgets from the layout"""
        # Remove all chart widgets
        for widget in self.chart_widgets:
            widget.setParent(None)
            widget.deleteLater()
        
        self.chart_widgets.clear()
        
        # Show instructions
        self.show_instructions()
    
    def refresh_charts(self):
        """Refresh charts based on current tag selection and mode"""
        if not hasattr(self.parent_window, 'tag_browser'):
            self.show_no_data_message("Tag browser not available")
            return
        
        if self.data_frame.empty:
            self.show_no_data_message("No data available. Please fetch data first.")
            return
        
        # Determine which tags to chart based on mode
        if hasattr(self.parent_window, 'mode_selector'):
            is_inferential = self.parent_window.mode_selector.currentText().startswith("Inferential")
        else:
            is_inferential = self.parent_window.tag_browser.inferential_mode
        
        chartable_tags = []
        
        if is_inferential:
            # In inferential mode, show charts for ALL tags that exist in the data
            lab_tags = self.parent_window.tag_browser.get_lab_tags()
            process_tags = self.parent_window.tag_browser.get_process_tags()
            
            # Add all tags that exist in the dataframe
            all_available_tags = lab_tags + process_tags
            for tag in all_available_tags:
                if tag in self.data_frame.columns:
                    chartable_tags.append(tag)
            
            # Log what we're charting
            if hasattr(self.parent_window, 'log_output') and chartable_tags:
                lab_in_charts = [t for t in chartable_tags if t in lab_tags]
                process_in_charts = [t for t in chartable_tags if t in process_tags]
                self.parent_window.log_output.append(
                    f"📈 Inferential Mode: Charting {len(lab_in_charts)} lab tags + {len(process_in_charts)} process tags"
                )
        else:
            # In process mode, only chart selected tags
            root = self.parent_window.tag_browser.tag_tree.invisibleRootItem()
            
            for i in range(root.childCount()):
                item = root.child(i)
                if item.checkState(0) == Qt.CheckState.Checked and not item.isHidden():
                    # Get tag name based on mode
                    if self.parent_window.tag_browser.inferential_mode:
                        tag_name = item.text(1)  # Tag column in inferential mode
                    else:
                        tag_name = item.text(0)  # Tag column in process mode
                    
                    if tag_name in self.data_frame.columns:
                        chartable_tags.append(tag_name)
        
        # Update charts with the determined tags
        self.update_charts_for_tags(chartable_tags)
    
    def reset_all_zoom(self):
        """Reset zoom for all chart views"""
        reset_count = 0
        for widget in self.chart_widgets:
            # Find ZoomableChartView widgets recursively
            chart_views = self.find_chart_views(widget)
            for chart_view in chart_views:
                chart_view.reset_zoom()
                reset_count += 1
        
        if hasattr(self.parent_window, 'log_output') and reset_count > 0:
            self.parent_window.log_output.append(f"🔍 Reset zoom for {reset_count} chart(s)")
    
    def find_chart_views(self, widget):
        """Recursively find ZoomableChartView widgets"""
        chart_views = []
        
        if isinstance(widget, ZoomableChartView):
            chart_views.append(widget)
        
        # Check children
        for child in widget.findChildren(ZoomableChartView):
            chart_views.append(child)
        
        return chart_views
    
    def get_chart_count(self):
        """Get the current number of charts displayed"""
        return len([w for w in self.chart_widgets if not isinstance(w, QLabel)])
    
    def show_all_available_tags(self):
        """Show charts for all tags available in the current dataset"""
        if self.data_frame.empty:
            self.show_no_data_message("No data available. Please fetch data first.")
            return
        
        # Get all columns that are not Timestamp or Status columns
        available_tags = []
        for col in self.data_frame.columns:
            if col != 'Timestamp' and not col.endswith('_Status'):
                available_tags.append(col)
        
        if available_tags:
            self.update_charts_for_tags(available_tags)
            if hasattr(self.parent_window, 'log_output'):
                self.parent_window.log_output.append(f"📈 Showing charts for all {len(available_tags)} available tags")
        else:
            self.show_no_data_message("No plottable tags found in dataset")