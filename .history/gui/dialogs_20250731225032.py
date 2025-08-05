## File 2: `gui/dialogs.py`

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from .widgets import ModernButton
from PyQt6.QtGui import QFont, QIcon, QColor
import PIconnect as PI


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
        """Extract instrument information using multiple methods"""
        # Method 1: Try the instrument attribute directly
        instrument = self.safe_get_attribute(point, 'instrument', '')
        if instrument:
            return instrument
        
        # Method 2: Try instrumenttag attribute
        instrument = self.safe_get_attribute(point, 'instrumenttag', '')
        if instrument:
            return instrument
        
        # Method 3: Try source attribute
        instrument = self.safe_get_attribute(point, 'source', '')
        if instrument:
            return instrument
        
        # Method 4: Try location1 attribute (sometimes contains instrument info)
        instrument = self.safe_get_attribute(point, 'location1', '')
        if instrument:
            return instrument
        
        # Method 5: Try location2 attribute
        instrument = self.safe_get_attribute(point, 'location2', '')
        if instrument:
            return instrument
        
        # Method 6: Try location3 attribute
        instrument = self.safe_get_attribute(point, 'location3', '')
        if instrument:
            return instrument
        
        # Method 7: Try location4 attribute
        instrument = self.safe_get_attribute(point, 'location4', '')
        if instrument:
            return instrument
        
        # Method 8: Try pointsource attribute
        instrument = self.safe_get_attribute(point, 'pointsource', '')
        if instrument:
            return instrument
        
        # Method 9: Try asset attribute
        instrument = self.safe_get_attribute(point, 'asset', '')
        if instrument:
            return instrument
        
        # Method 10: Try area attribute
        instrument = self.safe_get_attribute(point, 'area', '')
        if instrument:
            return instrument
        
        # Method 11: Extract from tag name (common pattern: INSTRUMENT_TAG)
        tag_name = point.name
        if '_' in tag_name:
            potential_instrument = tag_name.split('_')[0]
            if len(potential_instrument) > 2:  # Avoid very short prefixes
                return potential_instrument
        
        # Method 12: Extract from tag name (pattern: UNIT.AREA.INSTRUMENT.TAG)
        if '.' in tag_name:
            parts = tag_name.split('.')
            if len(parts) >= 3:
                return parts[2]  # Third part is often the instrument
        
        return ''  # Return empty string if no instrument info found
    
    def safe_get_attribute(self, obj, attr_name, default=''):
        """Safely get attribute from PI point object"""
        try:
            value = getattr(obj, attr_name, default)
            if value is None:
                return default
            # Clean up the value
            cleaned_value = str(value).replace('\t', ' ').replace('\n', ' ').strip()
            return cleaned_value[:200]  # Truncate long values
        except Exception:
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