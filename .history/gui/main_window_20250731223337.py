import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QScrollArea, QLineEdit, QDateTimeEdit, QComboBox,
    QMessageBox, QProgressBar, QSplitter, QTabWidget, QGroupBox, 
    QGridLayout, QSpinBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QDateTime, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QColor

from gui.widgets import (
    ModernCard, ModernButton, ConnectionStatusWidget, 
    AdvancedTagBrowser, DataPreviewWidget, EnhancedDateTimeEdit
)
from gui.dialogs import TagSearchDialog, ProgressDialog
from gui.chart_manager import ChartManager
from core.data_worker import DataFetchWorker
from core.exporters import DataExporter


class EnhancedPIDataExtractorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PI Data Extractor Pro v2.0")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1200, 800)
        
        # Apply modern theme
        self.apply_modern_theme()
        
        # Initialize data
        self.data_frame = pd.DataFrame()
        self.tags = []
        self.descriptions = {}
        self.units = {}
        self.connection_status = False
        self.lab_tags = []
        self.pi_available = False
        
        # Initialize debounce timer
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        
        self.setup_ui()
        self.connect_signals()
        
        # Test PI availability after UI is set up
        QTimer.singleShot(1000, self.test_pi_availability)
    
    def test_pi_availability(self):
        """Test if PIconnect is available without causing crashes"""
        try:
            import PIconnect as PI
            self.pi_available = True
            self.log_output.append("✅ PIconnect library loaded successfully")
            self.connect_btn.setEnabled(True)
        except Exception as e:
            self.pi_available = False
            self.log_output.append(f"❌ PIconnect not available: {str(e)}")
            self.log_output.append("💡 You can still load tag files and test the interface")
            self.connect_btn.setEnabled(False)
            self.connect_btn.setText("❌ PI Not Available")
    
    def apply_modern_theme(self):
        """Apply enhanced modern theme with better spacing and colors"""
        self.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                color: #212529;
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
                font-size: 13px;
            }
            
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
                font-size: 13px;
                min-height: 20px;
                selection-background-color: #E3F2FD;
            }
            
            QLineEdit:focus {
                border-color: #4A90E2;
                background-color: #FAFBFC;
            }
            
            QLineEdit:hover {
                border-color: #ADB5BD;
            }
            
            QComboBox {
                padding: 12px 16px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
                font-size: 13px;
                min-height: 20px;
                min-width: 120px;
            }
            
            QComboBox:focus {
                border-color: #4A90E2;
            }
            
            QComboBox:hover {
                border-color: #ADB5BD;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #6C757D;
                margin-right: 10px;
            }
            
            QSpinBox {
                padding: 12px 16px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
                font-size: 13px;
                min-height: 20px;
            }
            
            QSpinBox:focus {
                border-color: #4A90E2;
            }
            
            QDateTimeEdit {
                padding: 12px 16px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
                font-size: 13px;
                min-height: 20px;
                min-width: 180px;
            }
            
            QDateTimeEdit:focus {
                border-color: #4A90E2;
            }
            
            QDateTimeEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #DEE2E6;
            }
            
            QTextEdit {
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
                padding: 12px;
                font-size: 12px;
            }
            
            QLabel {
                color: #495057;
                font-weight: 500;
                margin-bottom: 4px;
            }
            
            QListWidget, QTreeWidget, QTableWidget {
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            
            QScrollBar:vertical {
                background: #F1F3F4;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: #C1C8CD;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #A8B2B9;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel (controls)
        left_panel = self.create_control_panel()
        left_panel.setFixedWidth(400)
        
        # Right panel (tabs for different views)
        right_panel = self.create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 1200])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def create_control_panel(self):
        """Create the enhanced left control panel with better spacing and styling"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F8F9FA;
            }
        """)
        
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Connection Card
        connection_card = self.create_connection_card()
        
        # Time Configuration Card
        time_card = self.create_time_card()
        
        # Data Extraction Card
        extraction_card = self.create_extraction_card()
        
        # Export Options Card
        export_card = self.create_export_card()
        
        # Add all cards to layout
        layout.addWidget(connection_card)
        layout.addWidget(time_card)
        layout.addWidget(extraction_card)
        layout.addWidget(export_card)
        layout.addStretch()
        
        panel.setLayout(layout)
        scroll.setWidget(panel)
        return scroll
    
    def create_connection_card(self):
        """Create enhanced connection card"""
        connection_card = ModernCard("🌐 PI Server Connection")
        connection_layout = QVBoxLayout()
        connection_layout.setSpacing(12)
        connection_layout.setContentsMargins(16, 20, 16, 16)
        
        # Connection status widget
        self.connection_status_widget = ConnectionStatusWidget()
        connection_layout.addWidget(self.connection_status_widget)
        
        # Server input with better label
        server_label = QLabel("Server Name:")
        server_label.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 14px;
                color: #495057;
                margin-bottom: 6px;
            }
        """)
        connection_layout.addWidget(server_label)
        
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("Enter PI Server name (e.g., PIHOME)")
        self.server_input.textChanged.connect(self.on_server_name_changed)
        self.server_input.setStyleSheet("""
            QLineEdit {
                padding: 14px 16px;
                font-size: 14px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
                background-color: #FAFBFC;
            }
        """)
        connection_layout.addWidget(self.server_input)
        
        # Connection buttons
        connection_buttons = QHBoxLayout()
        connection_buttons.setSpacing(8)
        
        self.connect_btn = ModernButton("🔌 Connect", color="#28A745")
        self.connect_btn.setMinimumHeight(44)
        
        self.disconnect_btn = ModernButton("⏹ Disconnect", color="#DC3545")
        self.disconnect_btn.setMinimumHeight(44)
        self.disconnect_btn.setEnabled(False)
        
        connection_buttons.addWidget(self.connect_btn)
        connection_buttons.addWidget(self.disconnect_btn)
        connection_layout.addLayout(connection_buttons)
        
        connection_card.setLayout(connection_layout)
        return connection_card
    
    def create_time_card(self):
        """Create enhanced time configuration card"""
        time_card = ModernCard("⏰ Time Configuration")
        time_layout = QVBoxLayout()
        time_layout.setSpacing(12)
        time_layout.setContentsMargins(16, 20, 16, 16)
        
        # Date time inputs in a grid
        datetime_grid = QGridLayout()
        datetime_grid.setSpacing(12)
        
        now = QDateTime.currentDateTime()
        yesterday = now.addDays(-1)
        
        # Start time
        start_label = QLabel("Start Time:")
        start_label.setStyleSheet(self.get_label_style())
        datetime_grid.addWidget(start_label, 0, 0)
        
        self.start_time = EnhancedDateTimeEdit(yesterday)
        datetime_grid.addWidget(self.start_time, 0, 1)
        
        # End time
        end_label = QLabel("End Time:")
        end_label.setStyleSheet(self.get_label_style())
        datetime_grid.addWidget(end_label, 1, 0)
        
        self.end_time = EnhancedDateTimeEdit(now)
        datetime_grid.addWidget(self.end_time, 1, 1)
        
        # Interval
        interval_label = QLabel("Interval:")
        interval_label.setStyleSheet(self.get_label_style())
        datetime_grid.addWidget(interval_label, 2, 0)
        
        self.interval_input = QComboBox()
        self.interval_input.addItems(["1m", "5m", "15m", "30m", "1h", "4h", "8h", "1d"])
        self.interval_input.setCurrentText("5m")
        datetime_grid.addWidget(self.interval_input, 2, 1)
        
        # Timezone
        timezone_label = QLabel("Timezone:")
        timezone_label.setStyleSheet(self.get_label_style())
        datetime_grid.addWidget(timezone_label, 3, 0)
        
        self.timezone_combo = QComboBox()
        self.timezone_combo.addItems(["Local", "UTC", "US/Central", "US/Eastern", "US/Pacific"])
        datetime_grid.addWidget(self.timezone_combo, 3, 1)
        
        time_layout.addLayout(datetime_grid)
        
        # Quick time buttons
        quick_label = QLabel("Quick Select:")
        quick_label.setStyleSheet(self.get_label_style())
        time_layout.addWidget(quick_label)
        
        quick_time_layout = QHBoxLayout()
        quick_time_layout.setSpacing(8)
        
        self.last_hour_btn = ModernButton("1H", color="#9C27B0")
        self.last_day_btn = ModernButton("1D", color="#9C27B0")
        self.last_week_btn = ModernButton("7D", color="#9C27B0")
        
        for btn in [self.last_hour_btn, self.last_day_btn, self.last_week_btn]:
            btn.setFixedSize(50, 36)
        
        quick_time_layout.addWidget(self.last_hour_btn)
        quick_time_layout.addWidget(self.last_day_btn)
        quick_time_layout.addWidget(self.last_week_btn)
        quick_time_layout.addStretch()
        
        time_layout.addLayout(quick_time_layout)
        time_card.setLayout(time_layout)
        return time_card
    
    def create_extraction_card(self):
        """Create enhanced data extraction card"""
        extraction_card = ModernCard("📊 Data Extraction")
        extraction_layout = QVBoxLayout()
        extraction_layout.setSpacing(12)
        extraction_layout.setContentsMargins(16, 20, 16, 16)

        # Mode selector
        mode_label = QLabel("Extraction Mode:")
        mode_label.setStyleSheet(self.get_label_style())
        extraction_layout.addWidget(mode_label)
        
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Process Only", "Inferential (Lab + Process)"])
        extraction_layout.addWidget(self.mode_selector)

        # Instructions for inferential mode
        self.inferential_instructions = QLabel(
            "💡 In Inferential Mode:\n"
            "• Select tags in Tags tab\n"
            "• Use 'Mark as Lab Tags' to designate lab tags\n"
            "• Lab tags determine sample times\n"
            "• Process tags are averaged around lab samples"
        )
        self.inferential_instructions.setStyleSheet("""
            QLabel {
                background-color: #FFF8E1;
                border: 2px solid #FFB74D;
                border-radius: 8px;
                padding: 12px;
                color: #E65100;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        self.inferential_instructions.setVisible(False)
        extraction_layout.addWidget(self.inferential_instructions)

        # Time window group
        self.window_group = QGroupBox("⏳ Time Window Around Lab Sample")
        self.window_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 13px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                margin: 8px 0;
                padding-top: 12px;
                background-color: #FAFBFC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #495057;
                background-color: #FAFBFC;
            }
        """)
        
        window_layout = QGridLayout()
        window_layout.setSpacing(12)
        window_layout.setContentsMargins(16, 16, 16, 16)

        past_label = QLabel("Past Window (min):")
        past_label.setStyleSheet(self.get_label_style())
        window_layout.addWidget(past_label, 0, 0)
        
        self.past_window_spin = QSpinBox()
        self.past_window_spin.setRange(0, 1440)
        self.past_window_spin.setValue(20)
        window_layout.addWidget(self.past_window_spin, 0, 1)

        future_label = QLabel("Future Window (min):")
        future_label.setStyleSheet(self.get_label_style())
        window_layout.addWidget(future_label, 1, 0)
        
        self.future_window_spin = QSpinBox()
        self.future_window_spin.setRange(0, 1440)
        self.future_window_spin.setValue(0)
        window_layout.addWidget(self.future_window_spin, 1, 1)

        self.window_group.setLayout(window_layout)
        self.window_group.setVisible(False)
        extraction_layout.addWidget(self.window_group)

        # Fetch Button
        self.fetch_btn = ModernButton("🚀 Fetch Data", color="#007BFF")
        self.fetch_btn.setMinimumHeight(48)
        extraction_layout.addWidget(self.fetch_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                height: 28px;
                background-color: #F8F9FA;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 6px;
            }
        """)
        extraction_layout.addWidget(self.progress_bar)
        
        extraction_card.setLayout(extraction_layout)
        return extraction_card
    
    def create_export_card(self):
        """Create enhanced export options card"""
        export_card = ModernCard("💾 Export Options")
        export_layout = QVBoxLayout()
        export_layout.setSpacing(12)
        export_layout.setContentsMargins(16, 20, 16, 16)

        # Format selection
        format_label = QLabel("Export Format:")
        format_label.setStyleSheet(self.get_label_style())
        export_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([".csv", ".tsv", ".txt", ".iq"])
        export_layout.addWidget(self.format_combo)

        # Format description
        self.format_tooltip_label = QLabel("ℹ️ CSV: Comma-delimited | TSV: Tab-delimited | TXT: DMC format | IQ: Lab compatible")
        self.format_tooltip_label.setStyleSheet("""
            QLabel {
                color: #6C757D;
                font-size: 11px;
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 8px;
                line-height: 1.3;
            }
        """)
        self.format_tooltip_label.setWordWrap(True)
        export_layout.addWidget(self.format_tooltip_label)
        
        # Save path
        path_label = QLabel("Export Location:")
        path_label.setStyleSheet(self.get_label_style())
        export_layout.addWidget(path_label)
        
        save_layout = QHBoxLayout()
        save_layout.setSpacing(8)
        
        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("Choose export location...")
        save_layout.addWidget(self.save_path_input, 1)
        
        self.browse_btn = ModernButton("📁", color="#6C757D")
        self.browse_btn.setFixedSize(44, 44)
        save_layout.addWidget(self.browse_btn)
        
        export_layout.addLayout(save_layout)
        
        self.export_btn = ModernButton("💾 Export Data", color="#28A745")
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumHeight(44)
        export_layout.addWidget(self.export_btn)
        
        export_card.setLayout(export_layout)
        return export_card
    
    def get_label_style(self):
        """Get consistent label styling"""
        return """
            QLabel {
                font-weight: 600;
                font-size: 13px;
                color: #495057;
                margin-bottom: 4px;
            }
        """
    
    def create_right_panel(self):
        """Create the right panel with tabs"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background: #F8F9FA;
                border: 2px solid #DEE2E6;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                min-width: 120px;
                padding: 12px 16px;
                margin: 2px;
                font-weight: 600;
                color: #495057;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid white;
                color: #212529;
            }
            QTabBar::tab:hover {
                background: #E9ECEF;
            }
        """)
        
        # Tags tab (always visible)
        self.tag_browser = AdvancedTagBrowser()
        self.tab_widget.addTab(self.tag_browser, "🏷️ Tags")
        
        # Charts tab - Create but don't add to tabs yet
        self.chart_manager = ChartManager(self)
        self.chart_scroll = QScrollArea()
        self.chart_scroll.setWidgetResizable(True)
        self.chart_scroll.setWidget(self.chart_manager)
        self.charts_tab_index = None
        
        # Data Preview tab - Create but don't add to tabs yet
        self.data_preview = DataPreviewWidget()
        self.preview_tab_index = None
        
        # Log tab (always visible)
        self.log_output = QTextEdit()
        self.log_output.setFont(QFont("Consolas", 10))
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        self.tab_widget.addTab(self.log_output, "📋 Log")
        
        return self.tab_widget
    
    def show_data_tabs(self):
        """Show Charts and Preview tabs after data is fetched"""
        # Add Charts tab if not already added
        if self.charts_tab_index is None:
            self.charts_tab_index = self.tab_widget.insertTab(1, self.chart_scroll, "📈 Charts")
            self.log_output.append("📈 Charts tab now available")
        
        # Add Preview tab if not already added
        if self.preview_tab_index is None:
            self.preview_tab_index = self.tab_widget.insertTab(2, self.data_preview, "👁️ Preview")
            self.log_output.append("👁️ Preview tab now available")
    
    def hide_data_tabs(self):
        """Hide Charts and Preview tabs when no data"""
        # Remove Charts tab if exists
        if self.charts_tab_index is not None:
            self.tab_widget.removeTab(self.charts_tab_index)
            self.charts_tab_index = None
            # Update preview tab index since it comes after charts
            if self.preview_tab_index is not None:
                self.preview_tab_index -= 1
        
        # Remove Preview tab if exists
        if self.preview_tab_index is not None:
            self.tab_widget.removeTab(self.preview_tab_index)
            self.preview_tab_index = None
    
    def connect_signals(self):
        """Connect all signals to their respective slots"""
        # Connection
        self.connect_btn.clicked.connect(self.connect_to_server)
        self.disconnect_btn.clicked.connect(self.disconnect_from_server)
        
        # Data operations
        self.fetch_btn.clicked.connect(self.fetch_pi_data)
        self.export_btn.clicked.connect(self.export_data)
        self.browse_btn.clicked.connect(self.browse_export_path)
        
        # Mode switching
        self.mode_selector.currentTextChanged.connect(self.toggle_inferential_controls)
        
        # Quick time buttons
        self.last_hour_btn.clicked.connect(lambda: self.set_quick_time_range(1))
        self.last_day_btn.clicked.connect(lambda: self.set_quick_time_range(24))
        self.last_week_btn.clicked.connect(lambda: self.set_quick_time_range(168))
        
        # Tag browser signals
        self.tag_browser.select_all_btn.clicked.connect(self.select_all_tags)
        self.tag_browser.deselect_all_btn.clicked.connect(self.deselect_all_tags)
        self.tag_browser.search_tags_btn.clicked.connect(self.search_pi_tags)
        self.tag_browser.load_file_btn.clicked.connect(self.load_tag_file)
        self.tag_browser.clear_all_btn.clicked.connect(self.clear_all_tags)
        self.tag_browser.remove_selected_btn.clicked.connect(self.remove_selected_tags)
        self.tag_browser.export_list_btn.clicked.connect(self.export_tag_list)
        self.tag_browser.tag_tree.itemChanged.connect(self.on_tag_selection_changed)
        
        # Connect debounce timer to chart updates
        self._debounce_timer.timeout.connect(self.update_charts)
        
        # Time validation
        self.start_time.dateTimeChanged.connect(self.validate_time_range)
        self.end_time.dateTimeChanged.connect(self.validate_time_range)
    
    def toggle_inferential_controls(self):
        """Show or hide inferential mode controls and update tag browser"""
        is_inferential = self.mode_selector.currentText().startswith("Inferential")
        
        # Show/hide UI elements
        self.inferential_instructions.setVisible(is_inferential)
        self.window_group.setVisible(is_inferential)
        
        # Update tag browser mode
        self.tag_browser.set_inferential_mode(is_inferential)
        
        # Log the mode change
        mode_name = "Inferential" if is_inferential else "Process"
        self.log_output.append(f"🔄 Switched to {mode_name} mode")
    
    def get_lab_tags(self):
        """Return ALL lab tags (regardless of selection status)"""
        return self.tag_browser.get_lab_tags()

    def get_process_tags(self):
        """Return ALL process tags (regardless of selection status)"""
        if self.mode_selector.currentText().startswith("Inferential"):
            return self.tag_browser.get_process_tags()
        else:
            return self.tag_browser.get_selected_tags()
    
    def on_server_name_changed(self, text):
        """Handle server name text changes and auto-normalize"""
        if not text:
            return
        
        cursor_pos = self.server_input.cursorPosition()
        normalized = text.strip().upper()
        
        if normalized != text:
            self.server_input.blockSignals(True)
            self.server_input.setText(normalized)
            new_cursor_pos = min(cursor_pos, len(normalized))
            self.server_input.setCursorPosition(new_cursor_pos)
            self.server_input.blockSignals(False)
    
    def normalize_server_name(self, server_name):
        """Normalize server name to uppercase"""
        if not server_name:
            return server_name
        
        normalized = server_name.strip().upper()
        
        if normalized != server_name:
            self.log_output.append(f"📝 Server name normalized: '{server_name}' → '{normalized}'")
        
        return normalized
    
    def connect_to_server(self):
        """Handle server connection"""
        if not self.pi_available:
            QMessageBox.warning(self, "PI Not Available", "PIconnect library is not available. Please check your installation.")
            return
            
        server_name = self.server_input.text().strip()
        if not server_name:
            QMessageBox.warning(self, "Missing Server", "Please enter a PI Server name.")
            return
        
        normalized_server = self.normalize_server_name(server_name)
        
        if normalized_server != server_name:
            self.server_input.setText(normalized_server)
        
        try:
            import PIconnect as PI
            server = PI.PIServer(normalized_server)
            self.connection_status_widget.set_connected(True)
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.connection_status = True
            self.log_