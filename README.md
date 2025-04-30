# Website Parser

A beautiful web interface that allows users to parse any website and view its HTML, CSS, and JavaScript components.

## Features

- Modern and responsive UI
- Real-time website parsing
- Detailed analysis of:
  - Basic information (title)
  - Meta tags
  - Links
  - Scripts
  - Stylesheets
  - Images
- Beautiful animations and transitions
- Error handling and loading states

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd website-parser
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. Enter a website URL in the input field and click "Parse"

## Requirements

- Python 3.7+
- Flask
- requests
- beautifulsoup4
- python-dotenv

## Project Structure

```
website-parser/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── static/
│   └── style.css      # Custom CSS styles
└── templates/
    └── index.html     # Main HTML template
```

## License

MIT License 