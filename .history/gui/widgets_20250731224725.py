import hashlib
from PyQt6.QtWidgets import (
    QPushButton, QGroupBox, QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QGridLayout, QFrame,
    QDateTimeEdit, QCalendarWidget, QTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QDate, QTime
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCharts import QChartView
import pandas as pd

class ModernButton(QPushButton):
    """Custom button with modern styling and hover effects"""
    def __init__(self, text="", icon=None, color="#4A90E2"):
        super().__init__(text)
        self.color = color
        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon:
            self.setIcon(icon)
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


class ModernCard(QGroupBox):
    """Enhanced card-style container with better styling"""
    def __init__(self, title=""):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 2px solid #E9ECEF;
                border-radius: 12px;
                margin: 10px 0;
                padding-top: 16px;
                background-color: white;
                color: #495057;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #495057;
                background-color: white;
                border-radius: 4px;
            }
        """)


class ConnectionStatusWidget(QWidget):
    """Enhanced visual connection status indicator"""
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("""
            QLabel {
                color: #DC3545;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        self.status_text = QLabel("Disconnected")
        self.status_text.setStyleSheet("""
            QLabel {
                color: #DC3545;
                font-weight: 600;
                font-size: 13px;
                padding: 2px 0;
            }
        """)
        
        # Enhanced styling container
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFEBEE, stop:1 #FFCDD2);
                border: 2px solid #FFCDD2;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        
        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_text)
        layout.addStretch()
        self.setLayout(layout)
    
    def set_connected(self, connected=True):
        if connected:
            self.status_dot.setStyleSheet("""
                QLabel {
                    color: #28A745;
                    font-size: 18px;
                    font-weight: bold;
                }
            """)
            self.status_text.setText("Connected")
            self.status_text.setStyleSheet("""
                QLabel {
                    color: #28A745;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 2px 0;
                }
            """)
            self.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #D4EDDA, stop:1 #C3E6CB);
                    border: 2px solid #28A745;
                    border-radius: 8px;
                    margin: 2px;
                }
            """)
        else:
            self.status_dot.setStyleSheet("""
                QLabel {
                    color: #DC3545;
                    font-size: 18px;
                    font-weight: bold;
                }
            """)
            self.status_text.setText("Disconnected")
            self.status_text.setStyleSheet("""
                QLabel {
                    color: #DC3545;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 2px 0;
                }
            """)
            self.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FFEBEE, stop:1 #FFCDD2);
                    border: 2px solid #FFCDD2;
                    border-radius: 8px;
                    margin: 2px;
                }
            """)


class EnhancedDateTimeEdit(QDateTimeEdit):
    """Enhanced DateTime picker with better calendar popup and styling"""
    def __init__(self, datetime=None):
        super().__init__(datetime or QDateTime.currentDateTime())
        self.setup_enhanced_features()
    
    def setup_enhanced_features(self):
        """Setup enhanced datetime features"""
        # Enable calendar popup
        self.setCalendarPopup(True)
        
        # Set display format
        self.setDisplayFormat("MM/dd/yyyy HH:mm:ss")
        
        # Enhanced styling
        self.setStyleSheet("""
            QDateTimeEdit {
                padding: 12px 16px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                background-color: white;
                font-size: 13px;
                font-weight: 500;
                min-height: 20px;
                min-width: 200px;
            }
            
            QDateTimeEdit:focus {
                border-color: #4A90E2;
                background-color: #FAFBFC;
            }
            
            QDateTimeEdit:hover {
                border-color: #ADB5BD;
            }
            
            QDateTimeEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 2px solid #DEE2E6;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #F8F9FA;
            }
            
            QDateTimeEdit::drop-down:hover {
                background-color: #E9ECEF;
            }
            
            QDateTimeEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #6C757D;
            }
        """)
        
        # Get and enhance the calendar widget
        calendar = self.calendarWidget()
        if calendar:
            self.setup_enhanced_calendar(calendar)
    
    def setup_enhanced_calendar(self, calendar):
        """Setup enhanced calendar styling"""
        calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                font-size: 12px;
            }
            
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #F8F9FA;
                border-bottom: 1px solid #DEE2E6;
                border-radius: 6px 6px 0 0;
            }
            
            QCalendarWidget QToolButton {
                height: 30px;
                width: 40px;
                color: #495057;
                font-size: 14px;
                background-color: transparent;
                border: none;
                margin: 2px;
                border-radius: 4px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #E9ECEF;
            }
            
            QCalendarWidget QToolButton:pressed {
                background-color: #DEE2E6;
            }
            
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
            }
            
            QCalendarWidget QSpinBox {
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
                selection-background-color: #4A90E2;
                selection-color: white;
                border: none;
            }
            
            QCalendarWidget QAbstractItemView:disabled {
                color: #ADB5BD;
            }
        """)
        
        # Set grid visibility
        calendar.setGridVisible(True)
        
        # Set vertical header format
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)


class AdvancedTagBrowser(QWidget):
    """Enhanced tag browser with simplified lab tag designation"""
    def __init__(self):
        super().__init__()
        self.inferential_mode = False
        layout = QVBoxLayout()
        
        # Tag management controls
        management_layout = QHBoxLayout()
        self.search_tags_btn = ModernButton("🔍 Search PI Tags", color="#2196F3")
        self.load_file_btn = ModernButton("📁 Load from File", color="#FF9800")
        self.clear_all_btn = ModernButton("🗑️ Clear All", color="#FF6B6B")
        
        management_layout.addWidget(self.search_tags_btn)
        management_layout.addWidget(self.load_file_btn)
        management_layout.addWidget(self.clear_all_btn)
        management_layout.addStretch()
        
        # Mode indicator and instructions
        self.mode_indicator = QLabel("📊 Process Mode - Select tags for data extraction")
        self.mode_indicator.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                color: #1976D2;
            }
        """)
        layout.addWidget(self.mode_indicator)
        
        # Search and filter controls
        filter_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("🔍 Filter current tags...")
        self.filter_input.textChanged.connect(self.filter_tags)
        self.filter_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
            }
        """)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Tags", "Selected Only", "Unselected Only"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        
        filter_layout.addWidget(self.filter_input, 3)
        filter_layout.addWidget(self.filter_combo, 1)
        
        # Tag tree
        self.tag_tree = QTreeWidget()
        self.setup_tree_headers()
        
        # Enhanced table styling
        self.tag_tree.setStyleSheet("""
            QTreeWidget {
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #F9F9F9;
                selection-background-color: #E3F2FD;
            }
            QTreeWidget::item {
                padding: 6px;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #E3F2FD;
                color: #333;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
                color: #333;
            }
        """)
        
        # Quick action buttons
        button_layout = QHBoxLayout()
        self.select_all_btn = ModernButton("Select All", color="#4CAF50")
        self.deselect_all_btn = ModernButton("Clear Selection", color="#FF6B6B")
        self.remove_selected_btn = ModernButton("Remove Selected", color="#F44336")
        self.export_list_btn = ModernButton("💾 Export List", color="#607D8B")
        
        # Inferential mode specific button (initially hidden)
        self.mark_as_lab_btn = ModernButton("🧪 Mark Selected as Lab Tags", color="#9C27B0")
        self.mark_as_lab_btn.setVisible(False)
        self.mark_as_lab_btn.setToolTip("Select tags first, then click to mark them as lab tags")
        
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.deselect_all_btn)
        button_layout.addWidget(self.remove_selected_btn)
        button_layout.addWidget(self.mark_as_lab_btn)
        button_layout.addWidget(self.export_list_btn)
        button_layout.addStretch()
        
        # Tag count label with enhanced info
        self.tag_count_label = QLabel("Tags: 0 total, 0 selected")
        self.tag_count_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        
        # Add all to layout
        layout.addLayout(management_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(self.tag_tree)
        layout.addWidget(self.tag_count_label)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Connect signals
        self.tag_tree.itemChanged.connect(self.update_tag_count)
        self.mark_as_lab_btn.clicked.connect(self.mark_selected_as_lab)
    
    def setup_tree_headers(self):
        """Setup tree headers based on current mode"""
        if self.inferential_mode:
            self.tag_tree.setHeaderLabels(["Select", "Tag", "Description", "Units", "Tag Type"])
            self.tag_tree.setColumnCount(5)
            header = self.tag_tree.header()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Select
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Tag
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Description
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Units
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Tag Type
        else:
            self.tag_tree.setHeaderLabels(["Tag", "Description", "Units", "Type"])
            self.tag_tree.setColumnCount(4)
            header = self.tag_tree.header()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
    
    def set_inferential_mode(self, enabled):
        """Switch between process and inferential modes"""
        self.inferential_mode = enabled
        
        if enabled:
            self.mode_indicator.setText(
                "🧪 Inferential Mode - Select tags and mark some as Lab Tags. "
                "All other tags will be treated as Process Tags."
            )
            self.mode_indicator.setStyleSheet("""
                QLabel {
                    background-color: #F3E5F5;
                    border: 1px solid #9C27B0;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                    color: #7B1FA2;
                }
            """)
            # Show inferential mode button
            self.mark_as_lab_btn.setVisible(True)
            
            # Update filter combo for inferential mode
            self.filter_combo.clear()
            self.filter_combo.addItems(["All Tags", "Lab Tags Only", "Process Tags Only", "Selected Only"])
        else:
            self.mode_indicator.setText("📊 Process Mode - Select tags for data extraction")
            self.mode_indicator.setStyleSheet("""
                QLabel {
                    background-color: #E3F2FD;
                    border: 1px solid #2196F3;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                    color: #1976D2;
                }
            """)
            # Hide inferential mode button
            self.mark_as_lab_btn.setVisible(False)
            
            # Reset filter combo for process mode
            self.filter_combo.clear()
            self.filter_combo.addItems(["All Tags", "Selected Only", "Unselected Only"])
        
        # Rebuild tree structure
        self.rebuild_tree()
    
    def rebuild_tree(self):
        """Rebuild tree with current mode structure - FIXED VERSION"""
        # Save current tag data BEFORE mode change
        current_tags = []
        root = self.tag_tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            item = root.child(i)
            
            # Read from CURRENT structure (before the mode change)
            if self.inferential_mode:
                # We're NOW in inferential mode, so we're switching FROM process mode
                # Current structure should be: [Tag, Description, Units, Type]
                if item.columnCount() >= 4:
                    tag_data = {
                        'name': item.text(0),  # Tag was in column 0 in process mode
                        'description': item.text(1),
                        'units': item.text(2),
                        'tag_type': item.text(3),
                        'is_lab': getattr(item, '_is_lab_tag', False),
                        'checked': item.checkState(0) == Qt.CheckState.Checked
                    }
                else:
                    # Fallback for malformed items
                    tag_data = {
                        'name': item.text(0) if item.text(0) else "Unknown",
                        'description': '',
                        'units': '',
                        'tag_type': 'Process Tag',
                        'is_lab': False,
                        'checked': item.checkState(0) == Qt.CheckState.Checked
                    }
            else:
                # We're NOW in process mode, so we're switching FROM inferential mode
                # Current structure should be: [Select, Tag, Description, Units, Tag Type]
                if item.columnCount() >= 5:
                    tag_data = {
                        'name': item.text(1),  # Tag was in column 1 in inferential mode
                        'description': item.text(2),
                        'units': item.text(3),
                        'tag_type': item.text(4),
                        'is_lab': getattr(item, '_is_lab_tag', False),
                        'checked': item.checkState(0) == Qt.CheckState.Checked
                    }
                else:
                    # Fallback for malformed items
                    tag_data = {
                        'name': item.text(1) if len(item.text(1)) > 0 else item.text(0),
                        'description': '',
                        'units': '',
                        'tag_type': 'Process Tag',
                        'is_lab': getattr(item, '_is_lab_tag', False),
                        'checked': item.checkState(0) == Qt.CheckState.Checked
                    }
            
            if tag_data['name']:  # Only add if we have a valid tag name
                current_tags.append(tag_data)
        
        # Clear and rebuild with new structure
        self.tag_tree.clear()
        self.setup_tree_headers()
        
        # Re-add tags with new structure
        for tag_data in current_tags:
            self.add_single_tag(tag_data)
        
        self.update_tag_count()
    
    def add_tags(self, tags_data):
        """Add tags to the browser"""
        for tag_info in tags_data:
            # Check if tag already exists
            if self.find_tag_item(tag_info['name']):
                continue  # Skip duplicates
            
            tag_data = {
                'name': tag_info['name'],
                'description': tag_info.get('description', ''),
                'units': tag_info.get('units', ''),
                'tag_type': 'Process Tag',  # Default to process tag
                'is_lab': False,
                'checked': False
            }
            self.add_single_tag(tag_data)
        
        self.update_tag_count()
    
    def add_single_tag(self, tag_data):
        """Add a single tag with proper structure based on current mode"""
        if self.inferential_mode:
            # Inferential mode: [Select, Tag, Description, Units, Tag Type]
            tag_type_display = "Lab Tag" if tag_data['is_lab'] else "Process Tag"
            item = QTreeWidgetItem([
                "",  # Select column (checkbox)
                tag_data['name'],
                tag_data['description'],
                tag_data['units'],
                tag_type_display
            ])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked if tag_data['checked'] else Qt.CheckState.Unchecked)
            
            # Store lab tag status
            item._is_lab_tag = tag_data['is_lab']
            
            # Color coding for lab tags
            if tag_data['is_lab']:
                for col in range(item.columnCount()):
                    item.setBackground(col, QColor("#FFF3E0"))  # Light orange background
                    item.setForeground(col, QColor("#E65100"))  # Dark orange text
        else:
            # Process mode: [Tag, Description, Units, Type]
            item = QTreeWidgetItem([
                tag_data['name'],
                tag_data['description'],
                tag_data['units'],
                tag_data['tag_type']
            ])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked if tag_data['checked'] else Qt.CheckState.Unchecked)
            
            # Store lab tag status (hidden in process mode)
            item._is_lab_tag = tag_data['is_lab']
        
        self.tag_tree.addTopLevelItem(item)
    
    def mark_selected_as_lab(self):
        """Mark selected tags as lab tags"""
        if not self.inferential_mode:
            return
            
        selected_items = []
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                selected_items.append(item)
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select tags to mark as lab tags.")
            return
        
        # Update selected items to lab tags
        for item in selected_items:
            item.setText(4, "Lab Tag")  # Tag Type column
            item._is_lab_tag = True
            
            # Apply lab tag styling
            for col in range(item.columnCount()):
                item.setBackground(col, QColor("#FFF3E0"))  # Light orange background
                item.setForeground(col, QColor("#E65100"))  # Dark orange text
        
        # Unselect the marked items
        for item in selected_items:
            item.setCheckState(0, Qt.CheckState.Unchecked)
        
        self.update_tag_count()
        
        lab_count = len([item for item in selected_items])
        process_count = self.get_process_tag_count()
        
        QMessageBox.information(
            self, 
            "Lab Tags Marked", 
            f"✅ Marked {lab_count} tags as Lab Tags.\n\n"
            f"📊 Current Status:\n"
            f"🧪 Lab Tags: {self.get_lab_tag_count()}\n"
            f"⚙️ Process Tags: {process_count}\n\n"
            f"💡 All non-lab tags will be treated as Process Tags during data fetching."
        )
    
    def find_tag_item(self, tag_name):
        """Find a tag item by name"""
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            # Get tag name based on current mode
            if self.inferential_mode:
                item_name = item.text(1)  # Tag column in inferential mode
            else:
                item_name = item.text(0)  # Tag column in process mode
            
            if item_name == tag_name:
                return item
        return None
    
    def filter_tags(self):
        """Filter tags based on search text"""
        filter_text = self.filter_input.text().lower()
        root = self.tag_tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            item = root.child(i)
            if self.inferential_mode:
                tag_name = item.text(1).lower()
                description = item.text(2).lower()
            else:
                tag_name = item.text(0).lower()
                description = item.text(1).lower()
            
            # Show item if filter text is in tag name or description
            visible = (filter_text in tag_name or filter_text in description) if filter_text else True
            item.setHidden(not visible)
    
    def apply_filter(self):
        """Apply combo box filter"""
        filter_type = self.filter_combo.currentText()
        root = self.tag_tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            item = root.child(i)
            visible = True
            
            if filter_type == "Lab Tags Only":
                visible = getattr(item, '_is_lab_tag', False)
            elif filter_type == "Process Tags Only":
                visible = not getattr(item, '_is_lab_tag', False)
            elif filter_type == "Selected Only":
                visible = item.checkState(0) == Qt.CheckState.Checked
            elif filter_type == "Unselected Only":
                visible = item.checkState(0) == Qt.CheckState.Unchecked
            
            # Combine with text filter
            if visible and self.filter_input.text():
                filter_text = self.filter_input.text().lower()
                if self.inferential_mode:
                    tag_name = item.text(1).lower()
                    description = item.text(2).lower()
                else:
                    tag_name = item.text(0).lower()
                    description = item.text(1).lower()
                visible = filter_text in tag_name or filter_text in description
            
            item.setHidden(not visible)
    
    def get_lab_tag_count(self):
        """Get count of lab tags"""
        count = 0
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if getattr(item, '_is_lab_tag', False):
                count += 1
        return count
    
    def get_process_tag_count(self):
        """Get count of process tags"""
        count = 0
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if not getattr(item, '_is_lab_tag', False):
                count += 1
        return count
    
    def update_tag_count(self):
        """Update the tag count label with enhanced info"""
        root = self.tag_tree.invisibleRootItem()
        total_count = root.childCount()
        selected_count = 0
        lab_count = 0
        process_count = 0
        
        for i in range(total_count):
            item = root.child(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                selected_count += 1
            
            if getattr(item, '_is_lab_tag', False):
                lab_count += 1
            else:
                process_count += 1
        
        if self.inferential_mode:
            self.tag_count_label.setText(
                f"Tags: {total_count} total, {selected_count} selected | "
                f"🧪 Lab: {lab_count}, ⚙️ Process: {process_count}"
            )
        else:
            self.tag_count_label.setText(f"Tags: {total_count} total, {selected_count} selected")
    
    def get_all_tags(self):
        """Get all tag names"""
        tags = []
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if self.inferential_mode:
                tags.append(item.text(1))  # Tag column in inferential mode
            else:
                tags.append(item.text(0))  # Tag column in process mode
        return tags

    def get_selected_tags(self):
        """Get selected tag names"""
        tags = []
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                if self.inferential_mode:
                    tags.append(item.text(1))  # Tag column in inferential mode
                else:
                    tags.append(item.text(0))  # Tag column in process mode
        return tags

    def get_lab_tags(self):
        """Get ALL tags marked as lab tags (regardless of selection)"""
        lab_tags = []
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if getattr(item, '_is_lab_tag', False):
                if self.inferential_mode:
                    lab_tags.append(item.text(1))  # Tag column in inferential mode
                else:
                    lab_tags.append(item.text(0))  # Tag column in process mode
        return lab_tags

    def get_process_tags(self):
        """Get ALL tags marked as process tags (regardless of selection)"""
        process_tags = []
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if not getattr(item, '_is_lab_tag', False):
                if self.inferential_mode:
                    process_tags.append(item.text(1))  # Tag column in inferential mode
                else:
                    process_tags.append(item.text(0))  # Tag column in process mode
        return process_tags

    def clear_all_tags(self):
        """Clear all tags from the browser"""
        self.tag_tree.clear()
        self.update_tag_count()

    def remove_selected_tags(self):
        """Remove selected tags from the browser"""
        root = self.tag_tree.invisibleRootItem()
        items_to_remove = [root.child(i) for i in range(root.childCount()) 
                        if root.child(i).checkState(0) == Qt.CheckState.Checked]
        
        for item in items_to_remove:
            root.removeChild(item)
        self.update_tag_count()

    def select_all_visible_tags(self):
        """Select all visible tags"""
        root = self.tag_tree.invisibleRootItem()
        selected_count = 0
        
        for i in range(root.childCount()):
            item = root.child(i)
            # Only select items that are not hidden
            if not item.isHidden():
                item.setCheckState(0, Qt.CheckState.Checked)
                selected_count += 1
        
        self.update_tag_count()
        
        # Optional: Log the action if parent window has logging
        if hasattr(self.parent(), 'log_output') and selected_count > 0:
            self.parent().log_output.append(f"✅ Selected {selected_count} visible tags")

    def deselect_all_tags(self):
        """Deselect all tags"""
        root = self.tag_tree.invisibleRootItem()
        for i in range(root.childCount()):
            root.child(i).setCheckState(0, Qt.CheckState.Unchecked)
        self.update_tag_count()

    def export_tag_list(self):
        """Export current tag list to file"""
        if self.tag_tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, "No Tags", "No tags to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Tag List", "tag_list.txt", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    root = self.tag_tree.invisibleRootItem()
                    for i in range(root.childCount()):
                        if self.inferential_mode:
                            tag_name = root.child(i).text(1)
                        else:
                            tag_name = root.child(i).text(0)
                        f.write(f"{tag_name}\n")
                QMessageBox.information(self, "Export Complete", f"Tag list exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export tag list: {str(e)}")
                
