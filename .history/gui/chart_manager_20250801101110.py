import hashlib
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QMenu
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor, QPainter, QAction
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
        
        # Control buttons (removed reset zoom buttons - use right-click instead)
        self.refresh_btn = ModernButton("🔄 Refresh Charts", color="#2196F3")
        self.refresh_btn.clicked.connect(self.refresh_charts)
        self.refresh_btn.setToolTip("Refresh charts based on currently selected tags")
        
        self.clear_btn = ModernButton("🗑️ Clear All", color="#FF6B6B")
        self.clear_btn.clicked.connect(self.clear_all_charts)
        self.clear_btn.setToolTip("Remove all charts from display")
        
        controls_layout.addWidget(info_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(self.clear_btn)
        
        self.layout.addLayout(controls_layout)
    
    def set_data(self, dataframe, descriptions=None, units=None):
        """Set the data for chart generation"""
        self.data_frame = dataframe.copy() if not dataframe.empty else pd.DataFrame()
        self.descriptions = descriptions or {}
        self.units = units or {}
    
    def update_charts_for_tags(self, selected_tags):
        """Update charts based on selected tags - REAL-TIME RESPONSE"""
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
        
        # Create charts for selected tags IMMEDIATELY
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
            self.parent_window.log_output.append(f"📈 Updated charts: {valid_charts} chart(s) for selected tags")
    
    def create_tag_chart(self, tag, height=250):
        """Create a chart for a single tag with enhanced right-click zoom reset"""
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
            
            # Create ENHANCED chart view with right-click zoom reset
            chart_view = EnhancedZoomableChartView(chart, tag)
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
        
        # Chart header with tag info only (removed reset zoom button)
        header_layout = QHBoxLayout()
        
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
        
        # Instruction label for right-click
        instruction_label = QLabel("💡 Right-click to reset zoom")
        instruction_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                font-style: italic;
                padding: 2px 5px;
            }
        """)
        
        header_layout.addWidget(tag_info)
        header_layout.addStretch()
        header_layout.addWidget(instruction_label)
        
        container_layout.addLayout(header_layout)
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
        # FIXED: Look for single "Status" column instead of tag-specific status columns
        if "Status" in self.data_frame.columns:
            mask = self.data_frame["Status"] == 'G'
        else:
            # If no status column, use all non-null values
            mask = pd.notna(self.data_frame[tag])
        
        # Get times and values
        times = pd.to_datetime(self.data_frame["Timestamp"])[mask]
        values = self.data_frame[tag][mask]
        
        # Remove any remaining NaN values
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
        """Refresh charts based on current tag selection and mode - REAL-TIME UPDATE"""
        if not hasattr(self.parent_window, 'tag_browser'):
            self.show_no_data_message("Tag browser not available")
            return
        
        if self.data_frame.empty:
            self.show_no_data_message("No data available. Please fetch data first.")
            return
        
        # Get CURRENTLY SELECTED tags from the tag browser
        currently_selected_tags = self.parent_window.tag_browser.get_selected_tags()
        
        # Update charts IMMEDIATELY based on current selection
        self.update_charts_for_tags(currently_selected_tags)
        
        if currently_selected_tags:
            # Log what we're charting
            if hasattr(self.parent_window, 'log_output'):
                self.parent_window.log_output.append(f"📈 Refreshed charts for {len(currently_selected_tags)} selected tags")
        else:
            if hasattr(self.parent_window, 'log_output'):
                self.parent_window.log_output.append("💡 No tags selected - check tags in Tags tab to view charts")
    
    # Removed reset_all_zoom method since we removed the reset zoom buttons
    # Users can right-click on individual charts to reset zoom
    
    def find_chart_views(self, widget):
        """Recursively find ZoomableChartView widgets"""
        chart_views = []
        
        if isinstance(widget, (ZoomableChartView, EnhancedZoomableChartView)):
            chart_views.append(widget)
        
        # Check children
        for child in widget.findChildren((ZoomableChartView, EnhancedZoomableChartView)):
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
            if col != 'Timestamp' and col != 'Status':
                available_tags.append(col)
        
        if available_tags:
            self.update_charts_for_tags(available_tags)
            if hasattr(self.parent_window, 'log_output'):
                self.parent_window.log_output.append(f"📈 Showing charts for all {len(available_tags)} available tags")
        else:
            self.show_no_data_message("No plottable tags found in dataset")


class EnhancedZoomableChartView(QChartView):
    """Enhanced chart view with zoom capabilities and RIGHT-CLICK reset zoom"""
    def __init__(self, chart, tag_name="", parent=None):
        super().__init__(chart, parent)
        self.tag_name = tag_name
        self.original_ranges = {}
        
        # Enable right-click context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Store original ranges after a short delay to ensure chart is fully rendered
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(200, self.store_original_ranges)

    def store_original_ranges(self):
        """Store the original axis ranges for zoom reset"""
        try:
            self.original_ranges = {}
            for axis in self.chart().axes():
                self.original_ranges[axis] = (axis.min(), axis.max())
        except Exception as e:
            print(f"Warning: Could not store original ranges for {self.tag_name}: {e}")

    def reset_zoom(self):
        """Reset zoom to original ranges"""
        try:
            if not self.original_ranges:
                # Fallback: zoom to fit all data
                self.chart().zoomReset()
                return
            
            for axis, (min_val, max_val) in self.original_ranges.items():
                if axis in self.chart().axes():  # Ensure axis still exists
                    axis.setRange(min_val, max_val)
        except Exception as e:
            print(f"Warning: Could not reset zoom for {self.tag_name}: {e}")
            # Fallback to chart's built-in zoom reset
            self.chart().zoomReset()

    def show_context_menu(self, position):
        """Show context menu on right-click with zoom reset option"""
        context_menu = QMenu(self)
        
        # Add zoom reset action
        reset_action = QAction("🔄 Reset Zoom", self)
        reset_action.setToolTip("Reset chart zoom to fit all data")
        reset_action.triggered.connect(self.reset_zoom)
        context_menu.addAction(reset_action)
        
        if self.tag_name:
            context_menu.addSeparator()
            # Add tag info action
            info_action = QAction(f"ℹ️ Tag: {self.tag_name}", self)
            info_action.setEnabled(False)  # Just for display
            context_menu.addAction(info_action)
        
        # Show context menu at cursor position
        context_menu.exec(self.mapToGlobal(position))

    def mouseReleaseEvent(self, event):
        """Handle mouse release events - prevent default right-click behavior"""
        if event.button() == Qt.MouseButton.RightButton:
            # Don't call parent's mouseReleaseEvent for right-click
            # This prevents any unwanted zoom behavior
            event.accept()
        else:
            # Handle left-click and other buttons normally
            super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.RightButton:
            # Accept right-click to prevent propagation
            event.accept()
        else:
            # Handle other mouse buttons normally (for zooming/panning)
            super().mousePressEvent(event)

    def resizeEvent(self, event):
        """Handle resize events and update stored ranges"""
        super().resizeEvent(event)
        # Update stored ranges after resize to maintain proper zoom reset
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self.store_original_ranges)

    def wheelEvent(self, event):
        """Handle wheel events for zooming"""
        # Allow normal wheel zoom behavior
        super().wheelEvent(event)