from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from .widgets import ModernButton
import PIconnect as PI


class TagSearchWorker(QThread):
    """Worker thread for searching PI tags"""
    search_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, server, search_pattern, max_results):
        super().__init__()
        self.server = server
        self.search_pattern = search_pattern
        self.max_results = max_results
    
    def run(self):
        try:
            points = self.server.search(self.search_pattern)
            
            if len(points) > self.max_results:
                points = points[:self.max_results]
            
            tags_data = []
            for point in points:
                tag_info = {
                    'name': point.name,
                    'description': getattr(point, 'description', '').replace('\t', ' ')[:200],  # Truncate long descriptions
                    'units': getattr(point, 'units_of_measurement', '').replace('\t', ' '),
                    'instrument': getattr(point, 'instrument', '').replace('\t', ' ')  # Added instrument field
                }
                tags_data.append(tag_info)
            
            self.search_complete.emit(tags_data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class TagSearchDialog(QDialog):
    """Enhanced dialog for searching and selecting PI tags with resizable columns and instrument field"""
    
    # Signal to emit when tags are added (not when dialog closes)
    tags_added = pyqtSignal(list)
    
    def __init__(self, server_name, parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.server = None
        self.accumulated_tags = []  # Store all selected tags across searches
        
        self.setWindowTitle("PI Tag Search - Enhanced")
        self.setModal(False)  # Allow interaction with main window
        self.resize(1100, 700)  # Increased width to accommodate new column
        
        self.setup_ui()
        self.connect_to_server()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Enhanced header with instructions
        header_layout = QVBoxLayout()
        title_label = QLabel("🔍 Enhanced PI Tag Search")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3; padding: 5px;")
        
        instruction_label = QLabel("💡 Tip: Perform multiple searches and accumulate tags. Click 'Add Selected' after each search.")
        instruction_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(instruction_label)
        layout.addLayout(header_layout)
        
        # Search controls
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search pattern (e.g., *TEMP*, TANK_*, FIC_*)...")
        self.search_input.returnPressed.connect(self.search_tags)
        
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
        
        self.include_description_cb = QCheckBox("Include descriptions")
        self.include_description_cb.setChecked(True)
        
        # Add search history dropdown (optional enhancement)
        self.append_results_cb = QCheckBox("Append to current results")
        self.append_results_cb.setChecked(False)
        self.append_results_cb.setToolTip("Keep previous search results and add new ones")
        
        options_layout.addWidget(QLabel("Max Results:"))
        options_layout.addWidget(self.max_results_spin)
        options_layout.addWidget(self.include_description_cb)
        options_layout.addWidget(self.append_results_cb)
        options_layout.addStretch()
        
        # Results table with enhanced features and resizable columns
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)  # Increased from 4 to 5 for instrument column
        self.results_table.setHorizontalHeaderLabels(["Select", "Tag Name", "Description", "Units", "Instrument"])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSortingEnabled(True)  # Enable column sorting
        
        # Enhanced column widths with resizable columns
        header = self.results_table.horizontalHeader()
        # Make ALL columns resizable by user
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Select - can resize
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Tag Name - can resize
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Description - can resize
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Units - can resize
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Instrument - can resize
        
        # Set intelligent default widths
        self.results_table.setColumnWidth(0, 60)   # Select checkbox
        self.results_table.setColumnWidth(1, 200)  # Tag Name
        self.results_table.setColumnWidth(2, 300)  # Description (wider for readability)
        self.results_table.setColumnWidth(3, 80)   # Units
        self.results_table.setColumnWidth(4, 150)  # Instrument (new column)
        
        # Enable horizontal scrolling for wide tables
        self.results_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # Status and progress
        self.status_label = QLabel("Enter a search pattern and click Search")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Enhanced button layout with more options
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
        
        # Accumulated tags counter
        self.accumulated_count_label = QLabel("Selected tags: 0")
        self.accumulated_count_label.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                color: #1976D2;
            }
        """)
        
        # Column resize info label
        resize_info_label = QLabel("💡 Tip: Drag column borders to resize columns as needed")
        resize_info_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic; padding: 3px;")
        
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
            self.server = PI.PIServer(self.server_name)
            self.status_label.setText(f"✅ Connected to {self.server_name}. Ready to search.")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to server: {str(e)}")
            self.status_label.setText("❌ Connection failed. Check server name.")
            self.status_label.setStyleSheet("color: #F44336; padding: 5px; font-weight: bold;")
    
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
        self.status_label.setText("🔍 Searching...")
        self.status_label.setStyleSheet("color: #2196F3; padding: 5px; font-weight: bold;")
        self.search_btn.setEnabled(False)
        
        # Start search in worker thread
        self.search_worker = TagSearchWorker(self.server, search_pattern, self.max_results_spin.value())
        self.search_worker.search_complete.connect(self.on_search_complete)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()
    
    def on_search_complete(self, tags_data):
        """Handle search completion with instrument field"""
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)
        
        if not tags_data:
            self.status_label.setText("❌ No tags found matching the search pattern.")
            self.status_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
            return
        
        # Get current row count for appending
        current_row_count = self.results_table.rowCount()
        
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
            
            # Instrument (NEW COLUMN)
            instrument_item = QTableWidgetItem(tag_info.get('instrument', ''))
            instrument_item.setFlags(instrument_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            instrument_item.setToolTip(tag_info.get('instrument', ''))  # Full instrument name in tooltip
            self.results_table.setItem(row_index, 4, instrument_item)
        
        total_results = self.results_table.rowCount()
        self.status_label.setText(f"✅ Found {len(tags_data)} new tags ({total_results} total in results)")
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
    
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
        self.status_label.setStyleSheet("color: #F44336; padding: 5px; font-weight: bold;")
        QMessageBox.critical(self, "Search Error", error_msg)
    
    def clear_search_results(self):
        """Clear current search results"""
        self.results_table.setRowCount(0)
        self.status_label.setText("Search results cleared. Enter a new search pattern.")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
    
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
        """Add currently selected tags to the accumulated list"""
        newly_selected = []
        
        for i in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                tag_name = self.results_table.item(i, 1).text()
                description = self.results_table.item(i, 2).text()
                units = self.results_table.item(i, 3).text()
                
                # Check if tag is already in accumulated list
                if not any(tag['name'] == tag_name for tag in self.accumulated_tags):
                    tag_info = {
                        'name': tag_name,
                        'description': description,
                        'units': units
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
            
            QMessageBox.information(
                self, 
                "Tags Added", 
                f"Added {len(newly_selected)} tags to your selection.\n"
                f"Total selected: {len(self.accumulated_tags)} tags\n\n"
                "Continue searching or click 'Done & Close' to finish."
            )
        else:
            QMessageBox.warning(self, "No Selection", "Please select at least one tag to add.")
    
    def show_accumulated_tags(self):
        """Show dialog with all accumulated tags"""
        if not self.accumulated_tags:
            QMessageBox.information(self, "No Tags", "No tags have been selected yet.")
            return
        
        # Create a simple dialog to show accumulated tags
        dialog = QDialog(self)
        dialog.setWindowTitle("Selected Tags")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel(f"📋 Selected Tags ({len(self.accumulated_tags)} total)")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)
        
        # List of tags
        tag_list = QTableWidget()
        tag_list.setColumnCount(3)
        tag_list.setHorizontalHeaderLabels(["Tag Name", "Description", "Units"])
        tag_list.setRowCount(len(self.accumulated_tags))
        
        for i, tag in enumerate(self.accumulated_tags):
            tag_list.setItem(i, 0, QTableWidgetItem(tag['name']))
            tag_list.setItem(i, 1, QTableWidgetItem(tag.get('description', '')))
            tag_list.setItem(i, 2, QTableWidgetItem(tag.get('units', '')))
        
        # Adjust column widths
        header = tag_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(tag_list)
        
        # Close button
        close_btn = ModernButton("Close", color="#607D8B")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def update_accumulated_count(self):
        """Update the accumulated tags counter"""
        count = len(self.accumulated_tags)
        self.accumulated_count_label.setText(f"Selected tags: {count}")
        
        if count > 0:
            self.accumulated_count_label.setStyleSheet("""
                QLabel {
                    background-color: #E8F5E8;
                    border: 1px solid #4CAF50;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-weight: bold;
                    color: #2E7D32;
                }
            """)
        else:
            self.accumulated_count_label.setStyleSheet("""
                QLabel {
                    background-color: #E3F2FD;
                    border: 1px solid #2196F3;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-weight: bold;
                    color: #1976D2;
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
    """Modern progress dialog with detailed status"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Data")
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("font-weight: bold; color: #333;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4A90E2;
                border-radius: 6px;
            }
        """)
        
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("color: #666; font-size: 11px;")
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.detail_label)
        
        self.setLayout(layout)
    
    def update_progress(self, value, status="", detail=""):
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
        if detail:
            self.detail_label.setText(detail)