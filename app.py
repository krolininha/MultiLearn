"""
MultiLearn Application
This module contains the main routes and configurations for MultiLearn,
a platform connecting tutors and students in Berlin.
"""

from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import sqlite3
import requests
import json
import os
import time
from cloudinary import config

# Config Cloudinary
config(
    cloud_name = "dx2gssfoi",
    api_key = "211997198544334",
    api_secret = "CWm4NLI57IIjra-N54WHrh57FWI"
)

# Define upload paste
UPLOAD_FOLDER = 'static/uploads'

# Make sure the folder exists
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except FileExistsError:
    # Pasta já existe, podemos ignorar este erro
    pass

# Created aplication Flask
app = Flask(__name__)

def get_db_connection():
    """
    Creates a connection to the SQLite database.

    Returns:
        sqlite3.Connection: Database connection object with Row factory
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'Database', 'tutors.db')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    """
    Handles tutor search with location-based filtering using Nominatim API with address.
    """
    # Get the page number from the query string, default is 1
    page = int(request.args.get('page', 1))

    # Define how many tutors to show per page
    per_page = 5
    
    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    conn = get_db_connection()
    address = request.args.get('address')  # Changed zipcode to address
    radius = float(request.args.get('radius', 5))
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    language = request.args.get('language')

    # Inicializar a consulta e os parâmetros
    query = 'SELECT * FROM tutors WHERE 1=1'
    params = []

    # Add filters if selected
    if subject and subject != 'Select Subject':
        query += ' AND subjects LIKE ?'
        params.append(f'%{subject}%')

    if language and language != 'Select Language':
        query += ' AND languages LIKE ?'
        params.append(f'%{language}%')

    if grade and grade != 'Select Grade':
        query += ' AND grade_levels LIKE ?'
        params.append(f'%{grade}%')

    # Criar consulta para contagem total
    count_query = 'SELECT COUNT(*) as count FROM tutors WHERE 1=1'
    count_params = []
    
    # Adicionar os mesmos filtros à consulta de contagem
    if subject and subject != 'Select Subject':
        count_query += ' AND subjects LIKE ?'
        count_params.append(f'%{subject}%')
    if language and language != 'Select Language':
        count_query += ' AND languages LIKE ?'
        count_params.append(f'%{language}%')
    if grade and grade != 'Select Grade':
        count_query += ' AND grade_levels LIKE ?'
        count_params.append(f'%{grade}%')
    
    # Executar a consulta de contagem
    total_count = conn.execute(count_query, count_params).fetchone()['count']
    total_pages = (total_count + per_page - 1) // per_page  # Arredondar para cima

    # Adicionar LIMIT e OFFSET à consulta principal para paginação
    pagination_query = query + ' LIMIT ? OFFSET ?'
    pagination_params = params + [per_page, offset]
    
    # Executar a consulta paginada
    tutors = conn.execute(pagination_query, pagination_params).fetchall()
    
    # Filter by distance if there is an address
    filtered_tutors = []
    center_lat = 52.5200  # Berlin center as default
    center_lng = 13.4050

    if address:
        try:
            print(f"DEBUG: Looking for tutors near the address: {address}")
            # Modified to search by address instead of postal code
            endpoint = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&country=Germany"

            headers = {
                'User-Agent': 'MultiLearn Tutorial Project'
            }
            response = requests.get(endpoint, headers=headers)

            print(f"DEBUG: Status from API: {response.status_code}")

            if response.status_code == 200:
                location_data = response.json()
                if location_data:
                    center_lat = float(location_data[0]['lat'])
                    center_lng = float(location_data[0]['lon'])

                    filtered_tutors = []
                    for tutor in tutors:
                        distance = calculate_distance(center_lat, center_lng, tutor['latitude'], tutor['longitude'])
                        print(f"DEBUG: {tutor['name']} está a {distance:.2f}km de distância")
                        if distance <= radius:
                            filtered_tutors.append(tutor)
                    
                    tutors_list = []
                    for tutor in filtered_tutors:
                        tutors_list.append({
                            'name': tutor['name'],
                            'latitude': tutor['latitude'],
                            'longitude': tutor['longitude'],
                            'subjects': tutor['subjects'],
                            'address': tutor['address']  # Now shows the address
                        })
                    
                    return render_template('search.html', 
                            tutors=tutors,
                            tutors_json=json.dumps(tutors_list),
                            center_lat=center_lat,
                            center_lng=center_lng,
                            current_page=page,
                            total_pages=total_pages)
                
        except Exception as e:
            print(f"DEBUG: Erro ao buscar localização: {e}")
    
    # If there is no address, use all filtered tutors
    tutors_list = []
    for tutor in tutors:
        tutors_list.append({
            'name': tutor['name'],
            'latitude': tutor['latitude'],
            'longitude': tutor['longitude'],
            'subjects': tutor['subjects'],
            'address': tutor['address']  # Now shows the address
        })
    
    return render_template('search.html', 
                        tutors=tutors,
                        tutors_json=json.dumps(tutors_list),
                        center_lat=center_lat,
                        center_lng=center_lng,
                        current_page=page,
                        total_pages=total_pages)

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculates distance between two points in kilometers using Haversine formula.
    """
    from math import sin, cos, sqrt, atan2, radians
    
    R = 6371.0  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

@app.route('/tutor/<int:tutor_id>')
def tutor_profile(tutor_id):
    """
    Displays the detailed profile of a specific tutor.

    Args:
        tutor_id (int): The ID of the tutor to display

    Returns:
        template: Renders tutor.html with tutor information
    """
    conn = get_db_connection()
    tutor = conn.execute('SELECT * FROM tutors WHERE id = ?',
                        (tutor_id,)).fetchone()
    conn.close()
    return render_template('tutor.html', tutor=tutor)

@app.route('/tutor/dashboard/<int:tutor_id>')
def tutor_dashboard(tutor_id):
    """
    Displays the tutor's dashboard with their information and options to edit.

    Args:
        tutor_id (int): The ID of the tutor

    Returns:
        template: Renders tutor_dashboard.html with tutor information
    """
    conn = get_db_connection()
    tutor = conn.execute('SELECT * FROM tutors WHERE id = ?',
                      (tutor_id,)).fetchone()
    conn.close()
    return render_template('tutor_dashboard.html', tutor=tutor)

@app.route('/about_us')
def about_us():
    """
    Displays the About Us page with information about MultiLearn.

    Returns:
        template: Renders about_us.html
    """
    return render_template('about_us.html')

@app.route('/tutor/login', methods=['GET', 'POST'])
def tutor_login():
    if request.method == 'POST':
        email = request.form['email']
        # Check if email exists in DB
        conn = get_db_connection()
        tutor = conn.execute('SELECT * FROM tutors WHERE email = ?', (email,)).fetchone()
        conn.close()
        if tutor:
            return redirect(url_for('tutor_dashboard', tutor_id=tutor['id']))
    return render_template('tutor_login.html')

@app.route('/logout')
def logout():
    """
    Handles user logout by redirecting to the home page.

    Returns:
        Redirect to home page
    """
    return redirect(url_for('home'))

@app.route('/tutor/edit/<int:tutor_id>', methods=['POST'])
def edit_tutor(tutor_id):
    """
    Handles the tutor profile update.
    If the tutor doesn't change subjects or languages, it keeps the previous data.
    """
    conn = get_db_connection()
    try:
        # Captures form data
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        location = request.form['location']
        address = request.form['address']  # Adicionado campo de endereço
        price = request.form['price']
        photo = request.form['photo']

        # Captures the tutor's old data to keep the values unchanged
        tutor = conn.execute('SELECT * FROM tutors WHERE id = ?', (tutor_id,)).fetchone()

        # If nothing is selected, it keeps the old data
        subjects = ', '.join(request.form.getlist('subjects')) if request.form.getlist('subjects') else tutor['subjects']
        languages = ', '.join(request.form.getlist('languages')) if request.form.getlist('languages') else tutor['languages']
        availability = ', '.join(request.form.getlist('availability')) if request.form.getlist('availability') else tutor['availability']

        # Updates the database
        conn.execute('''
            UPDATE tutors 
            SET name=?, email=?, phone=?, location=?, address=?, subjects=?, languages=?, 
                price=?, availability=?, photo=?
            WHERE id=?
        ''', (name, email, phone, location, address, subjects, languages, price, availability, photo, tutor_id))

        conn.commit()
        conn.close()

        return redirect(url_for('tutor_dashboard', tutor_id=tutor_id))
    except Exception as e:
        conn.close()
        print(f"Error updating tutor: {e}")
        return redirect(url_for('tutor_dashboard', tutor_id=tutor_id))

@app.route('/tutor/register', methods=['GET', 'POST'])
def tutor_register():
    """
    Handles tutor registration process.

    GET: Displays the registration form
    POST: Processes form submission and adds new tutor to database

    Form data:
        - name: Tutor's full name
        - email: Contact email
        - password: Password for account access
        - confirm_password: Password verification
        - phone: Contact phone number
        - location: District in Berlin
        - subjects: Teaching subjects (comma separated)
        - languages: Teaching languages (comma separated)
        - price: Hourly rate
        - zipcode: Location postal code

    Returns:
        GET: Renders registration form template
        POST: Redirects to login page after successful registration
    """
    if request.method == 'POST':
        try:
            # Debug logs 
            print("DEBUG: Formulário recebido")
            print("DEBUG: Campos do formulário:")
            for key in request.form:
                print(f"DEBUG: {key} = {request.form[key]}")
            
            print("DEBUG: Arquivos enviados:")
            for key in request.files:
                print(f"DEBUG: {key} = {request.files[key].filename}")

            # Get form data
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            phone = request.form['phone']
            location = request.form['location']
            address = request.form['address']  # Capturar o endereço
            price = request.form['price']
            zipcode = request.form['zipcode']

            # Obter e converter os valores diretamente
            subjects = ", ".join(request.form.getlist('subjects'))
            languages = ", ".join(request.form.getlist('languages'))
            grade_levels = ", ".join(request.form.getlist('grade_levels'))
            availability = ", ".join(request.form.getlist('availability'))

            # Verificar se algum campo está vazio
            if not subjects:
                subjects = ""
            if not languages:
                languages = ""
            if not grade_levels:
                grade_levels = ""
            if not availability:
                availability = ""



            # Verify if passwords match
            if password != confirm_password:
                return render_template('tutor_register.html', error="Passwords do not match")

            # Get coordinates from hidden fields (set by autocomplete)
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')

            # If latitude/longitude not provided via autocomplete, get from zipcode
            if not latitude or not longitude:
                headers = {
                    'User-Agent': 'MultiLearn Tutorial Project'
                }
                endpoint = f"https://nominatim.openstreetmap.org/search?postalcode={zipcode}&country=Germany&format=json"
                response = requests.get(endpoint, headers=headers)

                if response.status_code == 200:
                    location_data = response.json()
                    if location_data:
                        latitude = float(location_data[0]['lat'])
                        longitude = float(location_data[0]['lon'])
                    else:
                        return render_template('tutor_register.html', error="Could not verify location")
                else:
                    return render_template('tutor_register.html', error="Could not verify location")
            
            
            photo_path = ""
            if 'photo' in request.files:
                photo_file = request.files['photo']

                # Check if a file has been selected
                if photo_file.filename != '':
                    # Ensuring a secure file name
                    filename = secure_filename(photo_file.filename)
                    # Create a unique name to avoid overwriting files
                    unique_filename = f"{int(time.time())}_{filename}"
                    # Complete path
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    # Save the file
                    photo_file.save(filepath)
                    # Relative path to store in the bank
                    photo_path = f"/static/uploads/{unique_filename}"
            
            
            # Após processar o upload da foto e antes de inserir no banco de dados
            print(f"DEBUG: Caminho da foto salvo: {photo_path}")

            # Insert into database
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO tutors (
                    name, email, password, phone, location, address,
                    subjects, languages, grade_levels, availability,
                    price, zipcode, photo, latitude, longitude
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name, email, password, phone, location, address,
                subjects, languages, grade_levels, availability,
                price, zipcode, photo_path, latitude, longitude
            ))
            conn.commit()
            conn.close()

            return redirect(url_for('tutor_login'))

        except Exception as e:
            print(f"Error during registration: {e}")
            return render_template('tutor_register.html', error="Registration failed. Please try again.")

    # GET request
    return render_template('tutor_register.html')

if __name__ == '__main__':
    app.run(debug=True)