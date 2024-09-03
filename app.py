from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import tempfile
import base64
import requests
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote
import random


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    credits = db.Column(db.Integer, default=10)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Keep existing constants (PIXABAY_API_KEY, QUOTE_API_KEY, etc.)
PIXABAY_API_KEY = "13960567-e4d2886d86a2ccf44d5447cca"
QUOTE_API_KEY = "2zWE3epVIAt2P82SwpH6RA==fvWrtBNUDoN2j3E9"

CATEGORIES = [
    'age', 'alone', 'amazing', 'anger', 'architecture', 'art', 'attitude', 'beauty', 'best', 'birthday',
    'business', 'car', 'change', 'communication', 'computers', 'cool', 'courage', 'dad', 'dating', 'death',
    'design', 'dreams', 'education', 'environmental', 'equality', 'experience', 'failure', 'faith', 'family',
    'famous', 'fear', 'fitness', 'food', 'forgiveness', 'freedom', 'friendship', 'funny', 'future', 'god',
    'good', 'government', 'graduation', 'great', 'happiness', 'health', 'history', 'home', 'hope', 'humor',
    'imagination', 'inspirational', 'intelligence', 'jealousy', 'knowledge', 'leadership', 'learning',
    'legal', 'life', 'love', 'marriage', 'medical', 'men', 'mom', 'money', 'morning', 'movies', 'success'
]

SOCIAL_MEDIA_DIMENSIONS = {
    'instagram_square': (1080, 1080),
    'instagram_portrait': (1080, 1350),
    'facebook': (1200, 630),
    'twitter': (1200, 675),
    'pinterest': (1000, 1500),
    'linkedin': (1200, 627),
    'custom': None  # Will be set based on user input
}
# Add new fonts
FONTS = {
    'regular': 'DancingScript-Bold.ttf',
    'Merienda': 'Merienda-Bold.ttf',
    'NerkoOne': 'NerkoOne-Regular.ttf',
    'Pacifico': 'Pacifico-Regular.ttf',
    'PermanentMarker': 'PermanentMarker-Regular.ttf',
    'Satisfy': 'Satisfy-Regular.ttf',
    'ShadowsIntoLight': 'ShadowsIntoLight-Regular.ttf',
}

# Add color palettes
COLOR_PALETTES = {
    'classic': ['#000000', '#FFFFFF'],
    'pastel': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA'],
    'bold': ['#FF0000', '#00FF00', '#0000FF', '#FFFF00'],
    'earthy': ['#5D4037', '#795548', '#A1887F', '#D7CCC8'],
    'neon': ['#FF00FF', '#00FFFF', '#FF00FF', '#FFFF00'],
}

def download_font(url, font_path):
    """Download a font file if it doesn't exist locally."""
    if not os.path.exists(font_path):
        response = requests.get(url)
        response.raise_for_status()
        with open(font_path, 'wb') as f:
            f.write(response.content)

def get_font(font_name, size):
    try:
        return ImageFont.truetype(FONTS[font_name], size)
    except IOError:
        print(f"Font {font_name} not found. Using default font.")
        return ImageFont.load_default()

def get_images(query, count):
    """Fetch images from Pixabay API."""
    encoded_query = quote(query)
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={encoded_query}&image_type=photo&per_page=100"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        hits = data.get('hits', [])
        return random.sample(hits, min(count, len(hits)))
    except requests.RequestException as e:
        print(f"Error fetching images: {e}")
        return []

def generate_hashtags(quote, author, topic):
    """Generate hashtags based on the quote, author, and topic."""
    words = quote.lower().split()
    unique_words = list(set(words))
    hashtags = [f"#{word}" for word in unique_words if len(word) > 3][:3]  # Limit to 3 hashtags from quote
    hashtags.append(f"#{author.replace(' ', '')}")
    hashtags.append(f"#{topic}")
    return " ".join(hashtags)



def get_image(image_data):
    """Fetch a single image from Pixabay using the image data."""
    if not image_data:
        return None
    try:
        image_url = image_data.get('webformatURL')
        if not image_url:
            return None
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        return Image.open(BytesIO(image_response.content))
    except requests.RequestException as e:
        print(f"Error fetching image: {e}")
        return None

def get_single_quote(topic):
    """Fetch a single quote from the API Ninjas based on the given topic."""
    base_url = f'https://api.api-ninjas.com/v1/quotes?category={topic}'
    
    try:
        response = requests.get(base_url, headers={'X-Api-Key': QUOTE_API_KEY})
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]['quote'], data[0]['author']
    except requests.RequestException as e:
        print(f"Error fetching quote: {e}")
    return "The best preparation for tomorrow is doing your best today.", "H. Jackson Brown Jr."


def create_quote_image(quote, author, image_data, dimensions, watermark, font_style, color_palette, hashtags):
    img = get_image(image_data)
    if img is None:
        img = Image.new('RGB', dimensions, color='gray')
    else:
        img = img.resize(dimensions)
    
    draw = ImageDraw.Draw(img)
    
    # Choose colors from the selected palette
    colors = COLOR_PALETTES[color_palette]
    text_color = random.choice(colors)
    shadow_color = random.choice([c for c in colors if c != text_color])
    
    # Adjust font sizes based on image dimensions
    base_size = min(dimensions) // 15
    quote_font = get_font(font_style, base_size)
    author_font = get_font('regular', int(base_size * 0.7))
    watermark_font = get_font('regular', int(base_size * 0.5))

    # Calculate maximum width for text
    max_width = int(dimensions[0] * 0.8)

    # Wrap quote text
    wrapped_quote = textwrap.fill(quote, width=int(max_width / (base_size * 0.6)))
    quote_lines = wrapped_quote.split('\n')

    # Calculate total height of text block
    line_spacing = int(base_size * 0.3)
    quote_height = sum(quote_font.getbbox(line)[3] for line in quote_lines) + (len(quote_lines) - 1) * line_spacing
    author_height = author_font.getbbox(author)[3]
    total_height = quote_height + author_height + base_size

    # Calculate starting Y position to center the text block
    y = (dimensions[1] - total_height) // 2

    # Draw quote with shadow effect
    for line in quote_lines:
        line_width, line_height = quote_font.getbbox(line)[2], quote_font.getbbox(line)[3]
        x = (dimensions[0] - line_width) // 2
        # Draw shadow
        draw.text((x+2, y+2), line, font=quote_font, fill=shadow_color)
        # Draw main text
        draw.text((x, y), line, font=quote_font, fill=text_color)
        y += line_height + line_spacing

    # Draw author
    y += base_size // 2
    author_width = author_font.getbbox(author)[2]
    x = (dimensions[0] - author_width) // 2
    draw.text((x, y), f"- {author}", font=author_font, fill=text_color)

    # Add watermark
    watermark_color = (255, 255, 255, 128)  # Semi-transparent white
    margin = int(base_size * 0.3)
    draw.text((margin, margin), watermark, font=watermark_font, fill=watermark_color)
    draw.text((dimensions[0] - margin, margin), watermark, font=watermark_font, fill=watermark_color, anchor="ra")
    draw.text((margin, dimensions[1] - margin), watermark, font=watermark_font, fill=watermark_color, anchor="ld")
    draw.text((dimensions[0] - margin, dimensions[1] - margin), watermark, font=watermark_font, fill=watermark_color, anchor="rd")

    # Add hashtags
    hashtag_font = get_font('regular', int(base_size * 0.4))
    hashtag_width = hashtag_font.getbbox(hashtags)[2]
    hashtag_x = (dimensions[0] - hashtag_width) // 2
    hashtag_y = dimensions[1] - margin - hashtag_font.getbbox(hashtags)[3]
    draw.text((hashtag_x, hashtag_y), hashtags, font=hashtag_font, fill=text_color)

    return img

@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        
        new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            app.logger.error(f"Registration error: {str(e)}")
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', categories=CATEGORIES, social_media_dimensions=SOCIAL_MEDIA_DIMENSIONS, fonts=list(FONTS.keys()), color_palettes=list(COLOR_PALETTES.keys()), credits=current_user.credits)

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    if current_user.credits <= 0:
        flash('Not enough credits. Please add more credits to continue.', 'error')
        return jsonify({'error': 'Not enough credits'}), 403

    try:
        topic = request.form['topic']
        image_query = request.form['image_query']
        watermark = request.form['watermark']
        quote_count = int(request.form['quote_count'])
        social_media_platform = request.form['social_media_platform']
        font_style = request.form['font_style']
        color_palette = request.form['color_palette']
        
        if social_media_platform == 'custom':
            width = int(request.form['custom_width'])
            height = int(request.form['custom_height'])
            dimensions = (width, height)
        else:
            dimensions = SOCIAL_MEDIA_DIMENSIONS[social_media_platform]
        
        quotes = []
        for _ in range(quote_count):
            quote, author = get_single_quote(topic)
            quotes.append((quote, author))
        
        images = get_images(image_query, quote_count)
        
        results = []
        for i, (quote, author) in enumerate(quotes):
            image_data = images[i] if i < len(images) else None
            hashtags = generate_hashtags(quote, author, topic)
            img = create_quote_image(quote, author, image_data, dimensions, watermark, font_style, color_palette, hashtags)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name)
            
            with open(temp_file.name, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            
            results.append({
                'quote': quote,
                'author': author,
                'image_path': temp_file.name,
                'image_data': f"data:image/png;base64,{encoded_string}",
                'hashtags': hashtags
            })
        
        current_user.credits -= quote_count
        db.session.commit()
        
        flash(f'Successfully generated {quote_count} quote image(s).', 'success')
        return jsonify({'results': results, 'credits': current_user.credits})
    
    except Exception as e:
        app.logger.error(f"Error generating quotes: {str(e)}")
        flash('An error occurred while generating quotes. Please try again.', 'error')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/add_credits', methods=['POST'])
@login_required
def add_credits():
    try:
        current_user.credits += 10
        db.session.commit()
        flash('10 credits have been added to your account.', 'success')
        return jsonify({'credits': current_user.credits})
    except Exception as e:
        app.logger.error(f"Error adding credits: {str(e)}")
        flash('An error occurred while adding credits. Please try again.', 'error')
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def page_not_found(e):
    flash('The page you are looking for does not exist.', 'error')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    flash('An internal server error occurred. Please try again later.', 'error')
    return render_template('500.html'), 500


def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized.")

#if __name__ == '__main__':
#   init_db()  # Initialize the database before running the app
#    app.run(debug=True)