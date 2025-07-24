"""
Test suite for core functionality
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from PyQt6.QtCore import QThread

from core.data_worker import DataFetchWorker
from core.exporters import DataExporter


class TestDataFetchWorker:
    """Test cases for DataFetchWorker class"""
    
    def test_initialization_process_mode(self):
        """Test worker initialization in process mode"""
        worker = DataFetchWorker(
            server_name="TEST_SERVER",
            tags=["TAG1", "TAG2"],
            start_time="01/01/2024 00:00:00",
            end_time="01/02/2024 00:00:00",
            interval="1h",
            mode="process"
        )
        
        assert worker.server_name == "TEST_SERVER"
        assert worker.tags == ["TAG1", "TAG2"]
        assert worker.mode == "process"
        assert worker.interval == "1h"
        assert isinstance(worker, QThread)
    
    def test_initialization_inferential_mode(self):
        """Test worker initialization in inferential mode"""
        worker = DataFetchWorker(
            server_name="TEST_SERVER",
            tags=["PROC1", "PROC2"],
            start_time="01/01/2024 00:00:00",
            end_time="01/02/2024 00:00:00",
            mode="inferential",
            lab_tags=["LAB1", "LAB2"],
            past_window=30,
            future_window=10
        )
        
        assert worker.mode == "inferential"
        assert worker.lab_tags == ["LAB1", "LAB2"]
        assert worker.past_window == 30
        assert worker.future_window == 10
    
    @patch('PIconnect.PIServer')
    def test_fetch_interpolated_process_data(self, mock_pi_server):
        """Test process data fetching"""
        # Setup mock PI server and point
        mock_server = Mock()
        mock_pi_server.return_value = mock_server
        
        mock_point = Mock()
        mock_point.description = "Test Description"
        mock_point.units_of_measurement = "Units"
        mock_server.search.return_value = [mock_point]
        
        # Mock interpolated values
        mock_data = {
            datetime(2024, 1, 1, 0, 0): 10.0,
            datetime(2024, 1, 1, 1, 0): 15.0,
            datetime(2024, 1, 1, 2, 0): 20.0
        }
        mock_point.interpolated_values.return_value = mock_data
        
        worker = DataFetchWorker(
            server_name="TEST_SERVER",
            tags=["TAG1"],
            start_time="01/01/2024 00:00:00",
            end_time="01/01/2024 03:00:00",
            interval="1h",
            mode="process"
        )
        
        # Mock the signals
        worker.progress_updated = Mock()
        worker.data_ready = Mock()
        worker.error_occurred = Mock()
        
        # Run the worker
        worker.fetch_interpolated_process_data(mock_server)
        
        # Verify results
        worker.data_ready.emit.assert_called_once()
        result = worker.data_ready.emit.call_args[0][0]
        
        assert 'dataframe' in result
        assert 'descriptions' in result
        assert 'units' in result
        assert isinstance(result['dataframe'], pd.DataFrame)
        assert len(result['dataframe']) == 3
        assert 'TAG1' in result['dataframe'].columns
        assert 'Timestamp' in result['dataframe'].columns
    
    def test_fetch_weighted_process(self):
        """Test weighted process data fetching around lab sample"""
        worker = DataFetchWorker(
            server_name="TEST_SERVER",
            tags=["PROC1"],
            start_time="01/01/2024 00:00:00",
            end_time="01/02/2024 00:00:00",
            mode="inferential",
            past_window=10,
            future_window=5
        )
        
        # Mock server and point
        mock_server = Mock()
        mock_point = Mock()
        mock_server.search.return_value = [mock_point]
        
        # Mock recorded values around sample time
        sample_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_data = {
            datetime(2024, 1, 1, 11, 55): 10.0,
            datetime(2024, 1, 1, 12, 0): 12.0,
            datetime(2024, 1, 1, 12, 5): 11.0
        }
        mock_point.recorded_values.return_value = mock_data
        
        worker.error_occurred = Mock()
        
        result = worker.fetch_weighted_process(mock_server, sample_time)
        
        assert 'PROC1' in result
        assert isinstance(result['PROC1'], float)
        # Should be weighted average, with exact time having highest weight
        assert result['PROC1'] > 10.0  # Should be closer to 12.0 due to weighting
    
    @patch('PIconnect.PIServer')
    def test_fetch_lab_samples(self, mock_pi_server):
        """Test lab sample data fetching"""
        mock_server = Mock()
        mock_pi_server.return_value = mock_server
        
        # Mock lab points
        mock_lab1 = Mock()
        mock_lab2 = Mock()
        mock_server.search.side_effect = [[mock_lab1], [mock_lab2]]
        
        # Mock lab data
        lab1_data = {
            datetime(2024, 1, 1, 8, 0): 5.5,
            datetime(2024, 1, 1, 16, 0): 6.2
        }
        lab2_data = {
            datetime(2024, 1, 1, 8, 0): 25.1,
            datetime(2024, 1, 1, 16, 0): 26.8
        }
        mock_lab1.recorded_values.return_value = lab1_data
        mock_lab2.recorded_values.return_value = lab2_data
        
        worker = DataFetchWorker(
            server_name="TEST_SERVER",
            tags=["PROC1"],
            start_time="01/01/2024 00:00:00",
            end_time="01/02/2024 00:00:00",
            mode="inferential",
            lab_tags=["LAB1", "LAB2"]
        )
        
        worker.error_occurred = Mock()
        
        result = worker.fetch_lab_samples(mock_server)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Two sample times
        assert 'Timestamp' in result.columns
        assert 'LAB1' in result.columns
        assert 'LAB2' in result.columns


class TestDataExporter:
    """Test cases for DataExporter class"""
    
    def setup_method(self):
        """Setup test data for each test"""
        self.test_data = pd.DataFrame({
            'Timestamp': pd.date_range('2024-01-01', periods=3, freq='H'),
            'TAG1': [10.0, 15.0, 20.0],
            'TAG1_Status': ['G', 'G', 'B'],
            'TAG2': [100.0, 150.0, 200.0],
            'TAG2_Status': ['G', 'G', 'G']
        })
        
        self.descriptions = {
            'TAG1': 'Temperature Sensor',
            'TAG2': 'Pressure Sensor'
        }
        
        self.units = {
            'TAG1': 'degC',
            'TAG2': 'kPa'
        }
    
    def test_initialization(self):
        """Test exporter initialization"""
        exporter = DataExporter(
            self.test_data,
            self.descriptions,
            self.units,
            "US/Central"
        )
        
        assert not exporter.dataframe.empty
        assert exporter.descriptions == self.descriptions
        assert exporter.units == self.units
        assert exporter.timezone == "US/Central"
    
    def test_get_clean_dataframe(self):
        """Test cleaning dataframe for CSV export"""
        exporter = DataExporter(self.test_data)
        clean_df = exporter.get_clean_dataframe()
        
        # Should not have status columns
        status_columns = [col for col in clean_df.columns if col.endswith('_Status')]
        assert len(status_columns) == 0
        
        # Should have data columns
        assert 'TAG1' in clean_df.columns
        assert 'TAG2' in clean_df.columns
        assert 'Timestamp' in clean_df.columns
        
        # Timestamp should be timezone-naive for CSV
        assert clean_df['Timestamp'].dt.tz is None
    
    def test_export_csv(self, tmp_path):
        """Test CSV export functionality"""
        exporter = DataExporter(self.test_data, self.descriptions, self.units)
        csv_path = tmp_path / "test_export.csv"
        
        exporter.export_csv(str(csv_path))
        
        # Verify file was created
        assert csv_path.exists()
        
        # Verify content
        exported_df = pd.read_csv(csv_path)
        assert len(exported_df) == 3
        assert 'TAG1' in exported_df.columns
        assert 'TAG2' in exported_df.columns
        assert 'Timestamp' in exported_df.columns
        
        # Should not have status columns in CSV
        status_columns = [col for col in exported_df.columns if col.endswith('_Status')]
        assert len(status_columns) == 0
    
    def test_export_txt_dmc_format(self, tmp_path):
        """Test TXT (DMC format) export functionality"""
        exporter = DataExporter(self.test_data, self.descriptions, self.units, "Local")
        txt_path = tmp_path / "test_export.txt"
        
        exporter.export_txt(str(txt_path))
        
        # Verify file was created
        assert txt_path.exists()
        
        # Read and verify content
        with open(txt_path, 'r') as f:
            lines = f.readlines()
        
        # Should have proper DMC format structure
        assert lines[0].strip() == "(timezone:Local)"
        
        # Header line should have Time, tags, and Status columns
        header = lines[1].strip().split('\t')
        assert header[0] == "Time"
        assert "TAG1" in header
        assert "TAG2" in header
        assert "Status" in header
        
        # Should have description and units rows
        assert len(lines) >= 6  # Header + descriptions + units + data rows
    
    def test_export_with_missing_status_columns(self, tmp_path):
        """Test export when some status columns are missing"""
        # Create data without all status columns
        partial_data = pd.DataFrame({
            'Timestamp': pd.date_range('2024-01-01', periods=2, freq='H'),
            'TAG1': [10.0, 15.0],
            'TAG1_Status': ['G', 'B'],
            'TAG2': [100.0, 150.0]
            # No TAG2_Status column
        })
        
        exporter = DataExporter(partial_data, self.descriptions, self.units)
        txt_path = tmp_path / "test_partial.txt"
        
        # Should not raise an error
        exporter.export_txt(str(txt_path))
        
        # Verify file was created and has content
        assert txt_path.exists()
        with open(txt_path, 'r') as f:
            content = f.read()
            assert "TAG1" in content
            assert "TAG2" in content
    
    def test_export_empty_dataframe(self, tmp_path):
        """Test export with empty dataframe"""
        empty_df = pd.DataFrame()
        exporter = DataExporter(empty_df)
        
        csv_path = tmp_path / "empty.csv"
        txt_path = tmp_path / "empty.txt"
        
        # Should handle empty dataframes gracefully
        exporter.export_csv(str(csv_path))
        exporter.export_txt(str(txt_path))
        
        assert csv_path.exists()
        assert txt_path.exists()


class TestIntegration:
    """Integration tests for core components"""
    
    @patch('PIconnect.PIServer')
    def test_full_process_workflow(self, mock_pi_server):
        """Test complete process mode workflow"""
        # Setup mock server
        mock_server = Mock()
        mock_pi_server.return_value = mock_server
        
        mock_point = Mock()
        mock_point.description = "Test Tag"
        mock_point.units_of_measurement = "Units"
        mock_server.search.return_value = [mock_point]
        
        # Mock data
        mock_data = {
            datetime(2024, 1, 1, 0, 0): 10.0,
            datetime(2024, 1, 1, 1, 0): 15.0
        }
        mock_point.interpolated_values.return_value = mock_data
        
        # Create worker
        worker = DataFetchWorker(
            server_name="TEST_SERVER",
            tags=["TEST_TAG"],
            start_time="01/01/2024 00:00:00",
            end_time="01/01/2024 02:00:00",
            interval="1h",
            mode="process"
        )
        
        # Mock signals
        results = []
        def capture_result(result):
            results.append(result)
        
        worker.progress_updated = Mock()
        worker.data_ready = Mock(side_effect=capture_result)
        worker.error_occurred = Mock()
        
        # Run worker
        worker.fetch_interpolated_process_data(mock_server)
        
        # Verify data was captured
        assert len(results) == 1
        result = results[0]
        
        # Test export
        exporter = DataExporter(
            result['dataframe'],
            result['descriptions'],
            result['units']
        )
        
        # Should be able to get clean dataframe
        clean_df = exporter.get_clean_dataframe()
        assert not clean_df.empty
        assert 'TEST_TAG' in clean_df.columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])