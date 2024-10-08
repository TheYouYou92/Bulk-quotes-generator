# Bulk-quotes-generator
# Quote Image Generator

This Flask application generates inspirational quote images for social media platforms.

## Features

- User authentication
- Quote generation with customizable topics
- Image background selection
- Multiple social media platform dimensions
- Credit system for quote generation

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-username/quote-image-generator.git
   cd quote-image-generator
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file in the project root):
   ```
   SECRET_KEY=your_secret_key
   PIXABAY_API_KEY=your_pixabay_api_key
   QUOTE_API_KEY=your_quote_api_key
   ```

5. Initialize the database:
   ```
   python init_db.py
   ```

6. Run the application:
   ```
   python app.py
   ```

7. Open a web browser and go to `http://localhost:5000`

## Usage

[Provide brief instructions on how to use the application]

## Contributing

[Instructions for how others can contribute to your project]

## License

[Include your chosen license information]