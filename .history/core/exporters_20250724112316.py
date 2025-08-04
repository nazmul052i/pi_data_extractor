import csv
import pandas as pd


class DataExporter:
    """Handles CSV and TXT data export formats only"""
    
    def __init__(self, dataframe, descriptions=None, units=None, timezone="Local"):
        self.dataframe = dataframe
        self.descriptions = descriptions or {}
        self.units = units or {}
        self.timezone = timezone
    
    def get_clean_dataframe(self):
        """Get dataframe without status columns for CSV export"""
        clean_df = self.dataframe[[col for col in self.dataframe.columns 
                                  if not col.endswith("_Status")]].copy()
        
        
        if "Timestamp" in clean_df.columns and pd.api.types.is_datetime64_any_dtype(clean_df["Timestamp"]):
            clean_df["Timestamp"] = pd.to_datetime(clean_df["Timestamp"]).dt.tz_localize(None)
        
        return clean_df
    
    def export_csv(self, file_path):
        """Export to CSV format (clean data without status columns)"""
        clean_df = self.get_clean_dataframe()
        clean_df.to_csv(file_path, index=False)
    
    def export_txt(self, file_path):
        """Export to DMC format with proper status column naming"""
        df = self.dataframe.copy()
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
        
        # Get all tags (excluding Timestamp and existing Status columns)
        all_tag_columns = [col for col in df.columns 
                          if col != 'Timestamp' and not col.endswith('_Status')]
        
        # For inferential data, we may not have all tags in descriptions
        available_tags = []
        for tag in all_tag_columns:
            if tag in df.columns:
                available_tags.append(tag)
        
        # If status column doesn't exist, we'll use 'G' (Good) as default
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
                desc_row.extend([tag_desc, ""])  # Empty description for status column
            writer.writerow(desc_row)
            
            # Units row
            units_row = [""]  # Empty for Time column
            for tag in available_tags:
                tag_units = self.units.get(tag, '')
                units_row.extend([tag_units, ""])  # Empty units for status column
            writer.writerow(units_row)
            
            # Data rows
            for _, row in df.iterrows():
                # Start with timestamp
                timestamp_str = pd.to_datetime(row["Timestamp"]).isoformat()
                row_data = [timestamp_str]
                
                # Add value and status for each tag
                for tag in available_tags:
                    # Get value (handle missing values)
                    value = row.get(tag, '')
                    if pd.isna(value):
                        value = ''
                    
                    # Get status (use 'G' if status column doesn't exist or is empty)
                    status_col = f"{tag}_Status"
                    status = row.get(status_col, 'G')
                    if pd.isna(status) or status == '':
                        status = 'G'
                    
                    row_data.extend([value, status])
                
                writer.writerow(row_data)