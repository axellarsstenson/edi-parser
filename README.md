# EDI Parser

A command-line tool for parsing EDI claims files to JSON format.

## Installation

```bash
pip install git+https://github.com/yourusername/edi-parser.git
```

## Usage

```bash
# Parse a file and output to stdout
edi-parser input.edi

# Parse a file and save to JSON
edi-parser input.edi -o output.json

# Get help
edi-parser --help
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/edi-parser.git
cd edi-parser
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.