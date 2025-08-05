from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QMessageBox, QPushButton, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor


class ModernButton(QPushButton):
    """FIXED: Lightweight modern button for dialogs"""
    
    def __init__(self, text="", color="#4A90E2"):
        super().__init__(text)
        self.color = color
        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_style()
    
    def apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.color}, stop:1 {self.darken_color(self.color)});
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.lighten_color(self.color)}, stop:1 {self.color});
            }}
            QPushButton:pressed {{
                background: {self.darken_color(self.color)};
            }}
            QPushButton:disabled {{
                background: #CCCCCC;
                color: #666666;
            }}
        """)
    
    def darken_color(self, hex_color):
        color = QColor(hex_color)
        return color.darker(120).name()
    
    def lighten_color(self, hex_color):
        color = QColor(hex_color)
        return color.lighter(110).name()


try:
    import PIconnect as PI
    PI_AVAILABLE = True
except ImportError:
    PI_AVAILABLE = False
    # Create a dummy PI module for when PIconnect is not available
    class DummyPI:
        class PIServer:
            def __init__(self, name):
                raise Exception("PIconnect library not available")
    PI = DummyPI()


class TagSearchWorker(QThread):
    """Worker thread for searching PI tags with enhanced instrument field handling"""
    search_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, server, search_pattern, max_results):
        super().__init__()
        self.server = server
        self.search_pattern = search_pattern
        self.max_results = max_results
    
    def run(self):
        try:
            if not PI_AVAILABLE:
                self.error_occurred.emit("PIconnect library is not available")
                return
                
            points = self.server.search(self.search_pattern)
            
            if len(points) > self.max_results:
                points = points[:self.max_results]
            
            tags_data = []
            for point in points:
                # Enhanced instrument field extraction with multiple fallbacks
                instrument_value = self.get_instrument_info(point)
                
                tag_info = {
                    'name': point.name,
                    'description': self.safe_get_attribute(point, 'description', ''),
                    'units': self.safe_get_attribute(point, 'units_of_measurement', ''),
                    'instrument': instrument_value
                }
                tags_data.append(tag_info)
            
            self.search_complete.emit(tags_data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    

    def get_instrument_info(self, point):
        """Extract instrument information using multiple methods - FIXED for 'instrumenttag' attribute"""
        
        # Method 1: Try the "Instrument tag" attribute (the correct one!)
        instrument = self.safe_get_attribute(point, 'path', '')
        if instrument:
            return instrument
        
        return ''  # Return empty string if no instrument info found


    def safe_get_attribute(self, obj, attr_name, default=''):
        """Safely get attribute from PI point object - UPDATED to handle spaces in attribute names"""
        try:
            # Handle attribute names with spaces by trying different access methods
            if ' ' in attr_name:
                # For attributes with spaces, try using getattr with the exact name
                value = getattr(obj, attr_name, None)
                
                # If that doesn't work, try accessing as a property
                if value is None:
                    try:
                        # Some PI systems might require accessing through a properties collection
                        # or using bracket notation (this depends on your PI system implementation)
                        value = getattr(obj, attr_name.replace(' ', '_'), None)
                    except:
                        pass
            else:
                value = getattr(obj, attr_name, default)
            
            if value is None:
                return default
                
            # Clean up the value
            cleaned_value = str(value).replace('\t', ' ').replace('\n', ' ').strip()
            return cleaned_value[:200]  # Truncate long values
            
        except Exception as e:
            # Debug: print what went wrong
            print(f"Error getting attribute '{attr_name}': {e}")
            return default


class TagSearchDialog(QDialog):
    """Enhanced dialog for searching and selecting PI tags with better instrument field support"""
    
    # Signal to emit when tags are added (not when dialog closes)
    tags_added = pyqtSignal(list)
    
    def __init__(self, server_name, parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.server = None
        self.accumulated_tags = []  # Store all selected tags across searches
        
        self.setWindowTitle("PI Tag Search - Enhanced with Instrument Detection")
        self.setModal(False)  # Allow interaction with main window
        self.resize(1200, 700)  # Increased width for better column visibility
        
        self.setup_ui()
        self.connect_to_server()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Enhanced header with instructions
        header_layout = QVBoxLayout()
        title_label = QLabel("🔍 Enhanced PI Tag Search with Instrument Detection")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3; padding: 5px;")
        
        instruction_label = QLabel("💡 Tip: Perform multiple searches and accumulate tags. The system will automatically detect instrument information from various PI point attributes.")
        instruction_label.setStyleSheet("color: #666; font-style: italic; padding: 5px; line-height: 1.4;")
        instruction_label.setWordWrap(True)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(instruction_label)
        layout.addLayout(header_layout)
        
        # Search controls
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search pattern (e.g., *TEMP*, TANK_*, FIC_*)...")
        self.search_input.returnPressed.connect(self.search_tags)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
            }
        """)
        
        self.search_btn = ModernButton("🔍 Search", color="#2196F3")
        self.search_btn.clicked.connect(self.search_tags)
        
        self.clear_results_btn = ModernButton("🗑️ Clear Results", color="#FF6B6B")
        self.clear_results_btn.clicked.connect(self.clear_search_results)
        
        search_layout.addWidget(QLabel("Search Pattern:"))
        search_layout.addWidget(self.search_input, 3)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.clear_results_btn)
        
        # Search options with enhanced controls
        options_layout = QHBoxLayout()
        
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 10000)
        self.max_results_spin.setValue(1000)
        self.max_results_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                border: 2px solid #DEE2E6;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        
        self.include_description_cb = QCheckBox("Include descriptions")
        self.include_description_cb.setChecked(True)
        
        self.append_results_cb = QCheckBox("Append to current results")
        self.append_results_cb.setChecked(False)
        self.append_results_cb.setToolTip("Keep previous search results and add new ones")
        
        # Add instrument detection info
        instrument_info_label = QLabel("🔧 Instrument detection: Automatic from PI attributes")
        instrument_info_label.setStyleSheet("color: #28A745; font-size: 11px; font-weight: 500;")
        
        options_layout.addWidget(QLabel("Max Results:"))
        options_layout.addWidget(self.max_results_spin)
        options_layout.addWidget(self.include_description_cb)
        options_layout.addWidget(self.append_results_cb)
        options_layout.addWidget(instrument_info_label)
        options_layout.addStretch()
        
        # Results table with enhanced features and optimized column widths
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)  # Keep 5 columns including instrument
        self.results_table.setHorizontalHeaderLabels(["Select", "Tag Name", "Description", "Units", "Instrument"])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSortingEnabled(True)  # Enable column sorting
        
        # Enhanced styling for table
        self.results_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E0E0E0;
                background-color: white;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                selection-background-color: #E3F2FD;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
            QHeaderView::section {
                background-color: #F8F9FA;
                padding: 10px 8px;
                border: 1px solid #DEE2E6;
                font-weight: 600;
                color: #495057;
                font-size: 13px;
            }
            QHeaderView::section:hover {
                background-color: #E9ECEF;
            }
        """)
        
        # Enhanced column widths with resizable columns
        header = self.results_table.horizontalHeader()
        # Make ALL columns resizable by user
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        
        # Set intelligent default widths optimized for readability
        self.results_table.setColumnWidth(0, 70)   # Select checkbox - slightly wider
        self.results_table.setColumnWidth(1, 220)  # Tag Name - wider for long tag names
        self.results_table.setColumnWidth(2, 320)  # Description - much wider for readability
        self.results_table.setColumnWidth(3, 90)   # Units - optimal for unit names
        self.results_table.setColumnWidth(4, 180)  # Instrument - wider for instrument names
        
        # Enable horizontal scrolling for wide tables
        self.results_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.results_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # Status and progress
        self.status_label = QLabel("Enter a search pattern and click Search")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6C757D;
                padding: 8px 12px;
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                height: 25px;
                background-color: #F8F9FA;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #28A745, stop:1 #20C997);
                border-radius: 6px;
            }
        """)
        
        # Enhanced button layout with better grouping
        button_layout = QHBoxLayout()
        
        # Selection buttons
        self.select_all_btn = ModernButton("✅ Select All", color="#4CAF50")
        self.select_all_btn.clicked.connect(self.select_all_results)
        
        self.select_none_btn = ModernButton("❌ Clear Selection", color="#FF9800")
        self.select_none_btn.clicked.connect(self.select_none_results)
        
        self.invert_selection_btn = ModernButton("🔄 Invert Selection", color="#9C27B0")
        self.invert_selection_btn.clicked.connect(self.invert_selection)
        
        # Action buttons
        self.add_selected_btn = ModernButton("➕ Add Selected to List", color="#2196F3")
        self.add_selected_btn.clicked.connect(self.add_selected_tags)
        
        self.view_accumulated_btn = ModernButton("📋 View Selected Tags", color="#607D8B")
        self.view_accumulated_btn.clicked.connect(self.show_accumulated_tags)
        
        self.done_btn = ModernButton("✅ Done & Close", color="#4CAF50")
        self.done_btn.clicked.connect(self.accept)
        
        self.cancel_btn = ModernButton("❌ Cancel", color="#F44336")
        self.cancel_btn.clicked.connect(self.reject)
        
        # Arrange buttons in logical groups
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.select_none_btn)
        button_layout.addWidget(self.invert_selection_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.add_selected_btn)
        button_layout.addWidget(self.view_accumulated_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.done_btn)
        button_layout.addWidget(self.cancel_btn)
        
        # Accumulated tags counter with enhanced styling
        self.accumulated_count_label = QLabel("Selected tags: 0")
        self.accumulated_count_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                color: #1976D2;
                font-size: 13px;
            }
        """)
        
        # Column resize info label
        resize_info_label = QLabel("💡 Tip: Drag column borders to resize. Instrument info is auto-detected from PI point attributes.")
        resize_info_label.setStyleSheet("color: #6C757D; font-size: 11px; font-style: italic; padding: 4px;")
        resize_info_label.setWordWrap(True)
        
        # Add all to layout
        layout.addLayout(search_layout)
        layout.addLayout(options_layout)
        layout.addWidget(QLabel("🔍 Search Results:"))
        layout.addWidget(resize_info_label)
        layout.addWidget(self.results_table)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.accumulated_count_label)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def connect_to_server(self):
        """Connect to PI server"""
        try:
            if not PI_AVAILABLE:
                raise Exception("PIconnect library is not available")
                
            self.server = PI.PIServer(self.server_name)
            self.status_label.setText(f"✅ Connected to {self.server_name}. Ready to search with enhanced instrument detection.")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #28A745;
                    padding: 8px 12px;
                    background-color: #D4EDDA;
                    border: 2px solid #28A745;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 13px;
                }
            """)
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to server: {str(e)}")
            self.status_label.setText("❌ Connection failed. Check server name.")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #DC3545;
                    padding: 8px 12px;
                    background-color: #F8D7DA;
                    border: 2px solid #DC3545;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 13px;
                }
            """)
    
    def search_tags(self):
        """Search for tags on PI server"""
        if not self.server:
            QMessageBox.warning(self, "No Connection", "Not connected to PI server.")
            return
        
        search_pattern = self.search_input.text().strip()
        if not search_pattern:
            QMessageBox.warning(self, "Empty Search", "Please enter a search pattern.")
            return
        
        # Clear previous results if not appending
        if not self.append_results_cb.isChecked():
            self.results_table.setRowCount(0)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("🔍 Searching with enhanced instrument detection...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #2196F3;
                padding: 8px 12px;
                background-color: #E3F2FD;
                border: 2px solid #2196F3;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
        """)
        self.search_btn.setEnabled(False)
        
        # Start search in worker thread
        self.search_worker = TagSearchWorker(self.server, search_pattern, self.max_results_spin.value())
        self.search_worker.search_complete.connect(self.on_search_complete)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()
    
    def on_search_complete(self, tags_data):
        """Handle search completion with enhanced instrument field display"""
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)
        
        if not tags_data:
            self.status_label.setText("❌ No tags found matching the search pattern.")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    padding: 8px 12px;
                    background-color: #FFF3E0;
                    border: 2px solid #FF9800;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 13px;
                }
            """)
            return
        
        # Get current row count for appending
        current_row_count = self.results_table.rowCount()
        
        # Count tags with instrument info for statistics
        tags_with_instruments = sum(1 for tag in tags_data if tag.get('instrument', ''))
        
        # Add new rows
        self.results_table.setRowCount(current_row_count + len(tags_data))
        
        for i, tag_info in enumerate(tags_data):
            row_index = current_row_count + i
            
            # Check if tag already exists to avoid duplicates
            if self.tag_already_exists(tag_info['name']):
                continue
                
            # Checkbox for selection
            checkbox = QCheckBox()
            self.results_table.setCellWidget(row_index, 0, checkbox)
            
            # Tag name
            name_item = QTableWidgetItem(tag_info['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row_index, 1, name_item)
            
            # Description
            desc_item = QTableWidgetItem(tag_info.get('description', ''))
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            desc_item.setToolTip(tag_info.get('description', ''))  # Full description in tooltip
            self.results_table.setItem(row_index, 2, desc_item)
            
            # Units
            units_item = QTableWidgetItem(tag_info.get('units', ''))
            units_item.setFlags(units_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row_index, 3, units_item)
            
            # Instrument (Enhanced with visual indicators)
            instrument_text = tag_info.get('instrument', '')
            instrument_item = QTableWidgetItem(instrument_text)
            instrument_item.setFlags(instrument_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Add visual styling for instrument field
            if instrument_text:
                # Green background for tags with instrument info
                instrument_item.setBackground(QColor("#D4EDDA"))
                instrument_item.setForeground(QColor("#155724"))
                instrument_item.setToolTip(f"Instrument: {instrument_text}")
            else:
                # Light gray background for tags without instrument info
                instrument_item.setBackground(QColor("#F8F9FA"))
                instrument_item.setForeground(QColor("#6C757D"))
                instrument_item.setText("(not detected)")
                instrument_item.setToolTip("Instrument information not available")
            
            self.results_table.setItem(row_index, 4, instrument_item)
        
        total_results = self.results_table.rowCount()
        self.status_label.setText(
            f"✅ Found {len(tags_data)} new tags ({total_results} total) • "
            f"🔧 {tags_with_instruments}/{len(tags_data)} have instrument info"
        )
        self.status_label.setStyleSheet("""
            QLabel {
                color: #28A745;
                padding: 8px 12px;
                background-color: #D4EDDA;
                border: 2px solid #28A745;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
        """)
    
    def tag_already_exists(self, tag_name):
        """Check if tag already exists in results table"""
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 1)
            if item and item.text() == tag_name:
                return True
        return False
    
    def on_search_error(self, error_msg):
        """Handle search error"""
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)
        self.status_label.setText(f"❌ Search failed: {error_msg}")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #DC3545;
                padding: 8px 12px;
                background-color: #F8D7DA;
                border: 2px solid #DC3545;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
        """)
        QMessageBox.critical(self, "Search Error", error_msg)
    
    def clear_search_results(self):
        """Clear current search results"""
        self.results_table.setRowCount(0)
        self.status_label.setText("Search results cleared. Enter a new search pattern.")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6C757D;
                padding: 8px 12px;
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
    
    def select_all_results(self):
        """Select all search results"""
        for i in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def select_none_results(self):
        """Deselect all search results"""
        for i in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def invert_selection(self):
        """Invert the current selection"""
        for i in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(not checkbox.isChecked())
    
    def add_selected_tags(self):
        """Add currently selected tags to the accumulated list with enhanced instrument field"""
        newly_selected = []
        
        for i in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                tag_name = self.results_table.item(i, 1).text()
                description = self.results_table.item(i, 2).text()
                units = self.results_table.item(i, 3).text()
                
                # Enhanced instrument field handling
                instrument_item = self.results_table.item(i, 4)
                instrument_text = instrument_item.text() if instrument_item else ''
                # Clean up the "(not detected)" placeholder
                if instrument_text == "(not detected)":
                    instrument_text = ''
                
                # Check if tag is already in accumulated list
                if not any(tag['name'] == tag_name for tag in self.accumulated_tags):
                    tag_info = {
                        'name': tag_name,
                        'description': description,
                        'units': units,
                        'instrument': instrument_text  # Include cleaned instrument data
                    }
                    self.accumulated_tags.append(tag_info)
                    newly_selected.append(tag_info)
        
        if newly_selected:
            # Emit signal for immediate addition to main window
            self.tags_added.emit(newly_selected)
            
            # Update counter
            self.update_accumulated_count()
            
            # Uncheck the added tags
            for i in range(self.results_table.rowCount()):
                checkbox = self.results_table.cellWidget(i, 0)
                if checkbox and checkbox.isChecked():
                    tag_name = self.results_table.item(i, 1).text()
                    if any(tag['name'] == tag_name for tag in newly_selected):
                        checkbox.setChecked(False)
            
            # Count tags with instrument info in this batch
            with_instruments = sum(1 for tag in newly_selected if tag['instrument'])
            
            QMessageBox.information(
                self, 
                "Tags Added", 
                f"Added {len(newly_selected)} tags to your selection.\n"
                f"🔧 {with_instruments} tags have instrument information.\n"
                f"Total selected: {len(self.accumulated_tags)} tags\n\n"
                "Continue searching or click 'Done & Close' to finish."
            )
        else:
            QMessageBox.warning(self, "No Selection", "Please select at least one tag to add.")
   
    def show_accumulated_tags(self):
        """Show dialog with all accumulated tags including enhanced instrument field"""
        if not self.accumulated_tags:
            QMessageBox.information(self, "No Tags", "No tags have been selected yet.")
            return
        
        # Create a dialog to show accumulated tags
        dialog = QDialog(self)
        dialog.setWindowTitle("Selected Tags")
        dialog.setModal(True)
        dialog.resize(900, 450)  # Increased width for instrument column
        
        layout = QVBoxLayout()
        
        # Header with statistics
        tags_with_instruments = sum(1 for tag in self.accumulated_tags if tag.get('instrument', ''))
        header_label = QLabel(
            f"📋 Selected Tags ({len(self.accumulated_tags)} total) • "
            f"🔧 {tags_with_instruments} with instrument info"
        )
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                background-color: #F8F9FA;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                color: #495057;
            }
        """)
        layout.addWidget(header_label)
        
        # List of tags with enhanced instrument column
        tag_list = QTableWidget()
        tag_list.setColumnCount(4)
        tag_list.setHorizontalHeaderLabels(["Tag Name", "Description", "Units", "Instrument"])
        tag_list.setRowCount(len(self.accumulated_tags))
        tag_list.setAlternatingRowColors(True)
        
        # Enhanced styling for accumulated tags table
        tag_list.setStyleSheet("""
            QTableWidget {
                gridline-color: #E0E0E0;
                background-color: white;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                selection-background-color: #E3F2FD;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #F8F9FA;
                padding: 10px 8px;
                border: 1px solid #DEE2E6;
                font-weight: 600;
                color: #495057;
            }
        """)
        
        # Make columns resizable in the accumulated tags dialog
        header = tag_list.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        
        # Set optimized default widths for accumulated tags dialog
        tag_list.setColumnWidth(0, 200)  # Tag Name
        tag_list.setColumnWidth(1, 280)  # Description
        tag_list.setColumnWidth(2, 80)   # Units
        tag_list.setColumnWidth(3, 180)  # Instrument
        
        for i, tag in enumerate(self.accumulated_tags):
            # Tag name
            tag_list.setItem(i, 0, QTableWidgetItem(tag['name']))
            
            # Description
            desc_item = QTableWidgetItem(tag.get('description', ''))
            desc_item.setToolTip(tag.get('description', ''))
            tag_list.setItem(i, 1, desc_item)
            
            # Units
            tag_list.setItem(i, 2, QTableWidgetItem(tag.get('units', '')))
            
            # Instrument with visual enhancement
            instrument_text = tag.get('instrument', '')
            instrument_item = QTableWidgetItem(instrument_text if instrument_text else '(not available)')
            
            if instrument_text:
                # Green styling for available instrument info
                instrument_item.setBackground(QColor("#D4EDDA"))
                instrument_item.setForeground(QColor("#155724"))
            else:
                # Gray styling for missing instrument info
                instrument_item.setForeground(QColor("#6C757D"))
            
            tag_list.setItem(i, 3, instrument_item)
        
        layout.addWidget(tag_list)
        
        # Summary info
        summary_label = QLabel(
            f"💡 Instrument information was automatically detected from PI point attributes. "
            f"{tags_with_instruments} out of {len(self.accumulated_tags)} tags have instrument data."
        )
        summary_label.setStyleSheet("""
            QLabel {
                color: #6C757D;
                font-size: 11px;
                padding: 8px;
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                line-height: 1.4;
            }
        """)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)
        
        # Close button
        close_btn = ModernButton("Close", color="#607D8B")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def update_accumulated_count(self):
        """Update the accumulated tags counter with enhanced styling"""
        count = len(self.accumulated_tags)
        tags_with_instruments = sum(1 for tag in self.accumulated_tags if tag.get('instrument', ''))
        
        self.accumulated_count_label.setText(
            f"Selected tags: {count} • With instruments: {tags_with_instruments}"
        )
        
        if count > 0:
            self.accumulated_count_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #D4EDDA, stop:1 #C3E6CB);
                    border: 2px solid #28A745;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 600;
                    color: #155724;
                    font-size: 13px;
                }
            """)
        else:
            self.accumulated_count_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #E3F2FD, stop:1 #BBDEFB);
                    border: 2px solid #2196F3;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 600;
                    color: #1976D2;
                    font-size: 13px;
                }
            """)
    
    def get_accumulated_tags(self):
        """Return all accumulated tags"""
        return self.accumulated_tags
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.accumulated_tags:
            reply = QMessageBox.question(
                self,
                "Confirm Close",
                f"You have {len(self.accumulated_tags)} tags selected.\n"
                "Are you sure you want to close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class ProgressDialog(QDialog):
    """Enhanced progress dialog with modern styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Data")
        self.setModal(True)
        self.setFixedSize(450, 180)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-weight: 600;
                color: #495057;
                font-size: 14px;
                padding: 5px 0;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                height: 28px;
                background-color: #F8F9FA;
                color: #495057;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4A90E2, stop:1 #357ABD);
                border-radius: 6px;
            }
        """)
        
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("""
            QLabel {
                color: #6C757D;
                font-size: 12px;
                padding: 5px 0;
                line-height: 1.3;
            }
        """)
        self.detail_label.setWordWrap(True)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.detail_label)
        
        self.setLayout(layout)
        
        # Apply dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #DEE2E6;
                border-radius: 12px;
            }
        """)
    
    def update_progress(self, value, status="", detail=""):
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
        if detail:
            self.detail_label.setText(detail)