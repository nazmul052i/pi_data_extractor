import csv
import pandas as pd


class DataExporter:
    """Handles CSV (comma), TSV (tab), TXT (DMC), and IQ data export formats"""
    
    def __init__(self, dataframe, descriptions=None, units=None, timezone="Local"):
        self.dataframe = dataframe
        self.descriptions = descriptions or {}
        self.units = units or {}
        self.timezone = timezone
    
    def get_clean_dataframe(self):
        """Get dataframe without status columns"""
        clean_df = self.dataframe[[col for col in self.dataframe.columns 
                                  if not col.endswith("_Status")]].copy()
        
        # Remove timezone from timestamp for compatibility
        if "Timestamp" in clean_df.columns and pd.api.types.is_datetime64_any_dtype(clean_df["Timestamp"]):
            clean_df["Timestamp"] = pd.to_datetime(clean_df["Timestamp"]).dt.tz_localize(None)
        
        return clean_df
    
    def export_csv(self, file_path):
        """Export to CSV format (comma-delimited, Excel compatible)"""
        clean_df = self.get_clean_dataframe()
        clean_df.to_csv(file_path, sep=',', index=False)  # Comma-delimited
    
    def export_tsv(self, file_path):
        """Export to TSV format (tab-delimited, clean data)"""
        clean_df = self.get_clean_dataframe()
        clean_df.to_csv(file_path, sep='\t', index=False)  # Tab-delimited
    
    def export_txt(self, file_path):
        """Export to DMC TXT format with status columns and metadata"""
        df = self.dataframe.copy()
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
        
        # Get all tags (excluding Timestamp and existing Status columns)
        all_tag_columns = [col for col in df.columns 
                          if col != 'Timestamp' and not col.endswith('_Status')]
        
        available_tags = []
        for tag in all_tag_columns:
            if tag in df.columns:
                available_tags.append(tag)
        
        # Ensure we have status columns for all tags
        for tag in available_tags:
            status_col = f"{tag}_Status"
            if status_col not in df.columns:
                df[status_col] = 'G'  # Default to Good quality
        
        with open(file_path, "w", newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            
            # Header line with timezone
            writer.writerow([f"(timezone:{self.timezone})"])
            
            # Column headers: Time, then tag1, Status, tag2, Status, etc.
            header_row = ["Time"]
            for tag in available_tags:
                header_row.extend([tag, "Status"])
            writer.writerow(header_row)
            
            # Description row
            desc_row = [""]  # Empty for Time column
            for tag in available_tags:
                tag_desc = self.descriptions.get(tag, '')
                desc_row.extend([tag_desc, ""])
            writer.writerow(desc_row)
            
            # Units row
            units_row = [""]  # Empty for Time column
            for tag in available_tags:
                tag_units = self.units.get(tag, '')
                units_row.extend([tag_units, ""])
            writer.writerow(units_row)
            
            # Data rows
            for _, row in df.iterrows():
                timestamp_str = pd.to_datetime(row["Timestamp"]).isoformat()
                row_data = [timestamp_str]
                
                for tag in available_tags:
                    value = row.get(tag, '')
                    if pd.isna(value):
                        value = ''
                    
                    status_col = f"{tag}_Status"
                    status = row.get(status_col, 'G')
                    if pd.isna(status) or status == '':
                        status = 'G'
                    
                    row_data.extend([value, status])
                
                writer.writerow(row_data)
    
    def export_iq(self, file_path):
        """Export to IQ format (tab-delimited, lab data compatible, MM/DD/YYYY format)"""
        clean_df = self.get_clean_dataframe()
        
        # Format timestamp to match lab data format (MM/DD/YYYY HH:MM:SS)
        if "Timestamp" in clean_df.columns:
            clean_df["Timestamp"] = pd.to_datetime(clean_df["Timestamp"]).dt.strftime("%m/%d/%Y %H:%M:%S")
            # Rename to "Time" to match lab data format
            clean_df = clean_df.rename(columns={"Timestamp": "Time"})
        
        # Export with tab delimiter, no index, no quotes
        clean_df.to_csv(file_path, sep='\t', index=False, quoting=csv.QUOTE_NONE, escapechar='\\')


# Update for main_window.py
def setup_export_formats(self):
    """Setup export format options"""
    # Add all four formats
    self.format_combo.addItems([".csv", ".tsv", ".txt", ".iq"])
    
    # Update tooltip
    self.format_tooltip_label.setText(
        "ℹ️ CSV: Comma-delimited (Excel) | TSV: Tab-delimited | TXT: DMC format | IQ: Lab compatible"
    )

