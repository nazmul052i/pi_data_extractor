# PI Data Extractor

A modern GUI application for extracting and visualizing process data from PI servers.

## Features

- Connect to PI servers and browse tags
- Extract historical process data
- Interactive charts and data visualization
- Export data to CSV and TXT formats
- Support for lab data correlation (inferential mode)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pi-data-extractor.git
   cd pi-data-extractor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Requirements

- Python 3.8+
- PyQt6
- pandas
- PIconnect
- Access to PI Server

## Usage

1. **Connect to PI Server**: Enter your PI server name and click Connect
2. **Add Tags**: Use the search function or load tags from a file
3. **Set Time Range**: Choose your start/end times and interval
4. **Fetch Data**: Click "Fetch Data" to retrieve the information
5. **View Results**: Check the Charts and Preview tabs
6. **Export**: Save your data in CSV or TXT format

## Screenshots

![Main Interface](docs/screenshots/main-window.png)
![Charts View](docs/screenshots/charts-view.png)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- Report bugs: [GitHub Issues](https://github.com/yourusername/pi-data-extractor/issues)
- Documentation: [User Guide](docs/user_guide.md)
- Email: your.email@example.com