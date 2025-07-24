"""
Pytest configuration and fixtures for PI Data Extractor tests
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for GUI tests"""
    if not QApplication.instance():
        app = QApplication([])
        app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True)
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def sample_dataframe():
    """Create sample dataframe for testing"""
    dates = pd.date_range('2024-01-01', periods=10, freq='H')
    return pd.DataFrame({
        'Timestamp': dates,
        'TEMP_001': [20.0 + i * 0.5 for i in range(10)],
        'TEMP_001_Status': ['G'] * 8 + ['B', 'G'],
        'PRES_001': [100.0 + i * 2.0 for i in range(10)],
        'PRES_001_Status': ['G'] * 10,
        'FLOW_001': [50.0 + i * 1.0 for i in range(10)],
        'FLOW_001_Status': ['G'] * 9 + ['B']
    })


@pytest.fixture
def sample_descriptions():
    """Sample tag descriptions"""
    return {
        'TEMP_001': 'Reactor Temperature',
        'PRES_001': 'System Pressure', 
        'FLOW_001': 'Feed Flow Rate'
    }


@pytest.fixture
def sample_units():
    """Sample tag units"""
    return {
        'TEMP_001': 'degC',
        'PRES_001': 'kPa',
        'FLOW_001': 'L/min'
    }


@pytest.fixture
def lab_dataframe():
    """Create lab data for inferential testing"""
    lab_times = [
        datetime(2024, 1, 1, 8, 0),
        datetime(2024, 1, 1, 16, 0),
        datetime(2024, 1, 2, 8, 0)
    ]
    
    return pd.DataFrame({
        'Timestamp': lab_times,
        'LAB_MOISTURE': [5.2, 5.8, 5.1],
        'LAB_PURITY': [98.5, 98.2, 98.7]
    })


@pytest.fixture
def process_dataframe():
    """Create process data around lab sample times"""
    # Create hourly data for 2 days
    times = pd.date_range('2024-01-01', periods=48, freq='H')
    
    return pd.DataFrame({
        'Timestamp': times,
        'PROC_TEMP': [80.0 + (i % 24) * 0.5 for i in range(48)],
        'PROC_TEMP_Status': ['G'] * 48,
        'PROC_FLOW': [150.0 + (i % 12) * 2.0 for i in range(48)],
        'PROC_FLOW_Status': ['G'] * 46 + ['B', 'G']
    })


@pytest.fixture
def mock_pi_server():
    """Mock PI server for testing"""
    from unittest.mock import Mock
    
    server = Mock()
    server.name = "TEST_SERVER"
    
    # Mock search method
    def mock_search(pattern):
        mock_point = Mock()
        mock_point.name = pattern
        mock_point.description = f"Description for {pattern}"
        mock_point.units_of_measurement = "Units"
        return [mock_point]
    
    server.search = mock_search
    return server


@pytest.fixture
def temp_export_dir(tmp_path):
    """Create temporary directory for export tests"""
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    return export_dir


@pytest.fixture(autouse=True)
def cleanup_qt():
    """Cleanup Qt objects after each test"""
    yield
    # Force garbage collection to clean up Qt objects
    import gc
    gc.collect()


# Test data constants
TEST_SERVER_NAME = "TEST_PI_SERVER"
TEST_START_TIME = "01/01/2024 00:00:00"
TEST_END_TIME = "01/02/2024 00:00:00"
TEST_INTERVAL = "1h"

# Mock PI data
MOCK_PI_DATA = {
    'TEMP_001': {
        datetime(2024, 1, 1, 0, 0): 20.0,
        datetime(2024, 1, 1, 1, 0): 20.5,
        datetime(2024, 1, 1, 2, 0): 21.0,
    },
    'PRES_001': {
        datetime(2024, 1, 1, 0, 0): 100.0,
        datetime(2024, 1, 1, 1, 0): 102.0,
        datetime(2024, 1, 1, 2, 0): 104.0,
    }
}


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "gui: mark test as GUI test (requires X server)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Mark GUI tests
        if "test_gui" in item.nodeid or "gui" in str(item.fspath):
            item.add_marker(pytest.mark.gui)
        
        # Mark slow tests
        if "slow" in item.name.lower() or "integration" in item.name.lower():
            item.add_marker(pytest.mark.slow)


# Skip GUI tests if running in headless environment
def pytest_runtest_setup(item):
    """Setup for individual tests"""
    if "gui" in [mark.name for mark in item.iter_markers()]:
        if os.environ.get('CI') == 'true' and not os.environ.get('DISPLAY'):
            pytest.skip("GUI tests require display server")


# Custom assertions for testing
class PIDataAssertions:
    """Custom assertions for PI data testing"""
    
    @staticmethod
    def assert_valid_pi_dataframe(df):
        """Assert dataframe has valid PI data structure"""
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert 'Timestamp' in df.columns
        
        # Check timestamp column
        assert pd.api.types.is_datetime64_any_dtype(df['Timestamp'])
        
        # Check for data columns (non-status columns)
        data_cols = [col for col in df.columns if not col.endswith('_Status') and col != 'Timestamp']
        assert len(data_cols) > 0
        
        # Check for corresponding status columns
        for col in data_cols:
            status_col = f"{col}_Status"
            if status_col in df.columns:
                # Status values should be valid PI status codes
                valid_statuses = {'G', 'B', 'U', 'Q', 'S'}  # Good, Bad, Uncertain, Questionable, Substituted
                unique_statuses = set(df[status_col].dropna().unique())
                assert unique_statuses.issubset(valid_statuses), f"Invalid status codes found: {unique_statuses - valid_statuses}"
    
    @staticmethod
    def assert_export_file_valid(file_path, format_type):
        """Assert exported file is valid"""
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0
        
        if format_type == 'csv':
            # Try to read as CSV
            df = pd.read_csv(file_path)
            assert not df.empty
        elif format_type == 'txt':
            # Check DMC format structure
            with open(file_path, 'r') as f:
                lines = f.readlines()
            assert len(lines) > 3  # At least header, description, units, and one data row
            assert lines[0].startswith('(timezone:')


# Make assertions available as fixture
@pytest.fixture
def pi_assertions():
    """Provide custom PI data assertions"""
    return PIDataAssertions()