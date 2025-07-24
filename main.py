import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("PI Data Extractor Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Process Data Solutions")
    
    # Apply application-wide style
    app.setStyle('Fusion')  # Modern look and feel
    
    try:
        # Import the main window only after Qt is initialized
        from gui.main_window import EnhancedPIDataExtractorGUI
        
        window = EnhancedPIDataExtractorGUI()
        window.show()
        
        return app.exec()
        
    except ImportError as e:
        QMessageBox.critical(None, "Import Error", 
                           f"Failed to import required modules:\n{str(e)}\n\n"
                           f"Please check your Python environment and dependencies.")
        return 1
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application:\n{str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())