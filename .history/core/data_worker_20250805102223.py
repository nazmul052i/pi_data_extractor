from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd
import PIconnect as PI
from functools import reduce


class DataFetchWorker(QThread):
    """Worker thread for fetching PI data (process or inferential/lab)"""
    progress_updated = pyqtSignal(int, str, str)
    data_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, server_name, tags, start_time, end_time, interval=None,
                 mode='process', lab_tags=None, past_window=20, future_window=0):
        super().__init__()
        self.server_name = server_name
        self.tags = tags
        self.start_time = start_time
        self.end_time = end_time
        self.interval = interval
        self.mode = mode  # 'process' or 'inferential'
        self.lab_tags = lab_tags or []
        self.past_window = past_window
        self.future_window = future_window
        self.descriptions = {}
        self.units = {}

    def fetch_weighted_process(self, server, sample_time):
        """Weighted average around lab sample"""
        from datetime import timedelta
        start = sample_time - timedelta(minutes=self.past_window)
        end = sample_time + timedelta(minutes=self.future_window)
        result = {}

        for tag in self.tags:
            try:
                point = server.search(tag)[0]
                raw = point.recorded_values(start, end)
                df = pd.DataFrame(raw.items(), columns=["Timestamp", "Value"])
                if df.empty:
                    result[tag] = None
                    continue
                df["Weight"] = 1.0 / ((df["Timestamp"] - sample_time).abs().dt.total_seconds() + 1)
                weighted = (df["Value"] * df["Weight"]).sum() / df["Weight"].sum()
                result[tag] = weighted
            except Exception as e:
                self.error_occurred.emit(f"⚠️ {tag} fetch around {sample_time} failed: {e}")
                result[tag] = None
        return result

    def fetch_lab_samples(self, server):
        """Get lab sample timestamps and values"""
        all_samples = []
        for tag in self.lab_tags:
            try:
                point = server.search(tag)[0]
                raw = point.recorded_values(self.start_time, self.end_time)
                df = pd.DataFrame(raw.items(), columns=["Timestamp", tag])
                all_samples.append(df)
            except Exception as e:
                self.error_occurred.emit(f"⚠️ Lab tag {tag} failed: {e}")
        if not all_samples:
            raise ValueError("❌ No lab data found.")
        merged = all_samples[0]
        for df in all_samples[1:]:
            merged = pd.merge(merged, df, on="Timestamp", how="outer")
        return merged.dropna().sort_values("Timestamp")

    def run(self):
        try:
            self.progress_updated.emit(0, "Connecting to PI Server...", f"Server: {self.server_name}")
            server = PI.PIServer(self.server_name)

            if self.mode == 'process':
                self.fetch_interpolated_process_data(server)
            elif self.mode == 'inferential':
                self.fetch_inferential_data(server)
            else:
                self.error_occurred.emit(f"Unknown mode: {self.mode}")
        except Exception as e:
            self.error_occurred.emit(f"Server connection failed: {str(e)}")

    def fetch_interpolated_process_data(self, server):
        """Fetch interpolated process data (simple mode) - FIXED VERSION"""
        data_frames = []
        total = len(self.tags)

        for i, tag in enumerate(self.tags):
            try:
                progress = int((i / total) * 90)
                self.progress_updated.emit(progress, f"Fetching {tag}", "")
                point = server.search(tag)[0]
                raw = point.interpolated_values(self.start_time, self.end_time, self.interval)
                df = pd.DataFrame(raw.items(), columns=["Timestamp", tag])
                # REMOVED: Don't add Status column here - we'll add it after merging
                self.descriptions[tag] = getattr(point, 'description', '').replace('\t', ' ')
                self.units[tag] = getattr(point, 'units_of_measurement', '').replace('\t', ' ')
                data_frames.append(df)
            except Exception as e:
                self.error_occurred.emit(f"Failed to fetch {tag}: {e}")

        if data_frames:
            self.progress_updated.emit(95, "Merging data...", "")
            merged = reduce(lambda l, r: pd.merge(l, r, on="Timestamp", how="outer"), data_frames)
            merged = merged.sort_values("Timestamp")
            
            # FIXED: Add single Status column AFTER merging all data
            merged["Status"] = 'G'  # Single status column for all tags

            result = {
                'dataframe': merged,
                'descriptions': self.descriptions,
                'units': self.units
            }
            self.progress_updated.emit(100, "Complete!", f"Retrieved {len(data_frames)} tags")
            self.data_ready.emit(result)
        else:
            self.error_occurred.emit("No process data fetched.")

    def fetch_inferential_data(self, server):
        """Fetch inferential dataset: lab + weighted process"""
        lab_df = self.fetch_lab_samples(server)
        rows = []
        total = len(lab_df)

        for i, (_, row) in enumerate(lab_df.iterrows()):
            sample_time = row["Timestamp"]
            lab_vals = row.drop("Timestamp").to_dict()
            proc_vals = self.fetch_weighted_process(server, sample_time)

            merged = {"Timestamp": sample_time}
            merged.update(lab_vals)
            merged.update(proc_vals)
            rows.append(merged)

            progress = int((i / total) * 95)
            self.progress_updated.emit(progress, f"Sample {i+1}/{total}", f"Time: {sample_time}")

        df = pd.DataFrame(rows)
        # FIXED: Add single Status column for inferential data too
        df["Status"] = 'G'
        
        self.progress_updated.emit(100, "Inferential dataset complete!", f"{len(df)} rows")

        result = {
            'dataframe': df,
            'descriptions': {},
            'units': {}
        }
        self.data_ready.emit(result)