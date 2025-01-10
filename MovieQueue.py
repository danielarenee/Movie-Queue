# -------------| M O V I E --- Q U E U E |-------------

import mysql.connector
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QDialog, QListWidget, QMessageBox
from PyQt5.QtGui import QPixmap
from io import BytesIO
import requests

# Database connection
# Replace 'your_password' with your actual database password before running.
def connect_to_database():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password',  # Replace with your database password
        database='movies_db'
    )

# Add a movie to the database
def add_movie_to_db(title, genre):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        # Fetch streaming platforms using the TMDb API
        platforms = ", ".join(get_streaming_platforms(title))

        sql = """
        INSERT INTO movies (title, genre, platform, duration, description, watched)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (title, genre, platforms, 0, "", 0)  # Default duration = 0, description empty
        cursor.execute(sql, values)
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Get all movies from the database
def get_all_movies():
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT title, genre, platform FROM movies")
        rows = cursor.fetchall()
        connection.close()
        return rows
    except Exception as e:
        print(f"Error: {e}")
        return []

# Delete a movie from the database
def delete_movie_from_db(title):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        sql = "DELETE FROM movies WHERE title = %s"
        cursor.execute(sql, (title,))
        connection.commit()
        connection.close()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error: {e}")
        return False

# Filter movies by genre
def filter_movies_by_genre(genre):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        sql = "SELECT title, genre FROM movies WHERE genre = %s"
        cursor.execute(sql, (genre,))
        rows = cursor.fetchall()
        connection.close()
        return rows
    except Exception as e:
        print(f"Error: {e}")
        return []

# Fetch movie info using TMDb API
def get_movie_info(title):
    api_key = "your_api_key"  # Replace with your TMDb API key
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data['results']:
            result = data['results'][0]  # Use the first result
            poster_path = result.get('poster_path')
            description = result.get('overview', "Description not available.")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            return {
                'poster_url': poster_url,
                'description': description
            }
    return {
        'poster_url': None,
        'description': "Description not available."
    }

# Fetch streaming platforms for a movie
def get_streaming_platforms(title):
    api_key = "your_api_key"  # Replace with your TMDb API key
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title}"
    search_response = requests.get(search_url)

    if search_response.status_code == 200:
        search_data = search_response.json()
        if search_data['results']:
            movie_id = search_data['results'][0]['id']  # Get the movie ID

            providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={api_key}"
            providers_response = requests.get(providers_url)

            if providers_response.status_code == 200:
                providers_data = providers_response.json()
                country_code = "your_country_code"  # Replace with your country code

                if country_code in providers_data['results']:
                    platforms = []
                    for key in ['flatrate', 'free', 'ads']:
                        if key in providers_data['results'][country_code]:
                            platforms.extend(
                                [platform['provider_name'] for platform in providers_data['results'][country_code][key]]
                            )

                    known_platforms = ["Netflix", "Disney Plus", "Max", "Amazon Prime Video", "Hulu", "Apple TV"]
                    filtered_platforms = [p for p in platforms if p in known_platforms]

                    return list(set(filtered_platforms))

    return ["Not Available"]

# Main Application ---------------------------------
class MovieApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Movie Watchlist")
        self.setGeometry(100, 100, 400, 300)

        # Layout
        self.layout = QVBoxLayout()

        # Add Movie Button
        self.add_movie_button = QPushButton("Add a Movie")
        self.add_movie_button.clicked.connect(self.open_add_movie_dialog)
        self.layout.addWidget(self.add_movie_button)

        # View Movies Button
        self.view_movies_button = QPushButton("View Movies")
        self.view_movies_button.clicked.connect(self.view_movies)
        self.layout.addWidget(self.view_movies_button)

        # Delete movies button 
        self.delete_movie_button = QPushButton("Delete a Movie")
        self.delete_movie_button.clicked.connect(self.open_delete_movie_dialog)
        self.layout.addWidget(self.delete_movie_button)

        # Filter movies button
        self.filter_movies_button = QPushButton("Filter Movies by Genre")
        self.filter_movies_button.clicked.connect(self.open_filter_movies_dialog)
        self.layout.addWidget(self.filter_movies_button)

        # Set layout
        self.setLayout(self.layout)

    def open_add_movie_dialog(self):
        dialog = AddMovieDialog(self)
        dialog.exec_()

    def open_delete_movie_dialog(self):
        dialog = DeleteMovieDialog(self)
        dialog.exec_()

    def open_filter_movies_dialog(self):
        dialog = FilterMoviesDialog(self)
        dialog.exec_()

    def view_movies(self):
        # Fetch movies from the database
        movies = get_all_movies()
        if not movies:
            QMessageBox.warning(self, "No Movies", "No movies found in the database!")
            return

        # Create a list widget for displaying movies
        movie_list = QListWidget()

        font = movie_list.font()
        font.setFamily("Courier")  # Monospaced font ensures consistent spacing
        movie_list.setFont(font)

        # Add movies with consistent alignment
        for movie in movies:
            title, genre, platform = movie
            movie_item = f"{title.ljust(30)} | Genre: {genre.ljust(10)} | Platforms: {platform if platform else 'None'}"
            movie_list.addItem(movie_item)

        # Create a new dialog for viewing movies
        dialog = QDialog(self)
        dialog.setWindowTitle("All Movies")
        dialog.setGeometry(150, 150, 600, 400)

        # Layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(movie_list)

        # Add the "View Info" button
        view_info_button = QPushButton("View Info")
        def show_info():
            selected_movie = movie_list.currentItem()
            if selected_movie:
                title = selected_movie.text().split(" | ")[0]
                ViewMovieInfoDialog(title, self).exec_()
            else:
                QMessageBox.warning(self, "No Selection", "Please select a movie!")

        view_info_button.clicked.connect(show_info)
        layout.addWidget(view_info_button)

        dialog.setLayout(layout)
        dialog.exec_()

# Add Movie Dialog
class AddMovieDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add a Movie")
        self.setGeometry(150, 150, 400, 400)

        # Layout
        self.layout = QVBoxLayout()

        # Title Input
        self.title_label = QLabel("Title:")
        self.layout.addWidget(self.title_label)
        self.title_input = QLineEdit()
        self.layout.addWidget(self.title_input)

        # Genre Selection
        self.genre_label = QLabel("Select Genre:")
        self.layout.addWidget(self.genre_label)

        self.selected_genre = None
        genres = [
            "Romcom", "Comedy", "Romance", "Drama", "SciFi", 
            "Profound", "Horror", "Thriller", "Fantasy", 
            "Action", "Animated", "Musical"
        ]

        # Genre buttons
        self.genre_buttons = []
        for genre in genres:
            button = QPushButton(genre)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, g=genre: self.select_genre(g))
            self.genre_buttons.append(button)
            self.layout.addWidget(button)

        # Submit Button
        self.submit_button = QPushButton("Save Movie")
        self.submit_button.setStyleSheet(
        "background-color: pink; color: black; font-size: 16px; padding: 10px;"
)

        self.submit_button.clicked.connect(self.save_movie)
        self.layout.addWidget(self.submit_button)

        # Set layout
        self.setLayout(self.layout)

    def select_genre(self, genre):
        """Highlight the selected genre and clear others."""
        self.selected_genre = genre
        for button in self.genre_buttons:
            button.setChecked(button.text() == genre)

    def save_movie(self):
        title = self.title_input.text()
        genre = self.selected_genre

        if not title or not genre:
            QMessageBox.warning(self, "Input Error", "Both Title and Genre are required!")
            return

        if add_movie_to_db(title, genre):
            QMessageBox.information(self, "Success", f"Movie '{title}' saved successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save the movie!")

#delete movie dialog 
class DeleteMovieDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete a Movie")
        self.setGeometry(150, 150, 300, 150)

        # Layout
        self.layout = QVBoxLayout()

        # Title Input
        self.title_label = QLabel("Title of Movie to Delete:")
        self.layout.addWidget(self.title_label)
        self.title_input = QLineEdit()
        self.layout.addWidget(self.title_input)

        # Submit Button
        self.submit_button = QPushButton("Delete Movie")
        self.submit_button.clicked.connect(self.delete_movie)
        self.layout.addWidget(self.submit_button)

        # Set layout
        self.setLayout(self.layout)

    def delete_movie(self):
        title = self.title_input.text()

        if not title:
            QMessageBox.warning(self, "Input Error", "Movie title is required!")
            return

        if delete_movie_from_db(title):
            QMessageBox.information(self, "Success", f"Movie '{title}' deleted successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Movie '{title}' not found!")

#filter movie dialog
class FilterMoviesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Movies by Genre")
        self.setGeometry(150, 150, 400, 400)

        # Layout
        self.layout = QVBoxLayout()

        # Instruction Label
        self.instruction_label = QLabel("Select a Genre to Filter:")
        self.layout.addWidget(self.instruction_label)

        genres = [
            "Romcom", "Comedy", "Romance", "Drama", "SciFi", 
            "Profound", "Horror", "Thriller", "Fantasy", 
            "Action", "Animated", "Musical"
        ] # Add your own genres

        # Add buttons for each genre
        for genre in genres:
            genre_button = QPushButton(genre)
            genre_button.clicked.connect(lambda checked, g=genre: self.filter_movies(g))
            self.layout.addWidget(genre_button)

        # Set layout
        self.setLayout(self.layout)

    def filter_movies(self, genre):
        # Fetch movies of the selected genre
        movies = filter_movies_by_genre(genre)
        if not movies:
            QMessageBox.warning(self, "No Movies", f"No movies found for genre '{genre}'!")
            return

        # Display filtered movie titles in a list
        movie_list = QListWidget()

        # Set the font to Courier for consistency
        font = movie_list.font()
        font.setFamily("Courier")
        movie_list.setFont(font)

        for movie in movies:
            movie_title = movie[0]  # Extract only the title
            movie_list.addItem(movie_title)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Movies in Genre: {genre}")
        dialog.setGeometry(150, 150, 400, 400)

        layout = QVBoxLayout()
        layout.addWidget(movie_list)
        dialog.setLayout(layout)
        dialog.exec_()

#view movie dialog
class ViewMovieInfoDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Info for {title}")
        self.setGeometry(200, 200, 400, 600)

        # Fetch movie details (poster and description)
        movie_info = get_movie_info(title)

        # Layout
        layout = QVBoxLayout()

        if movie_info['poster_url']:
            # Download and display the poster
            response = requests.get(movie_info['poster_url'])
            pixmap = QPixmap()
            pixmap.loadFromData(BytesIO(response.content).getvalue())

            poster_label = QLabel()
            poster_label.setPixmap(pixmap)
            poster_label.setScaledContents(True)  # Scale the image
            poster_label.setMaximumSize(200, 300)  # Set maximum dimensions
            layout.addWidget(poster_label)
        else:
            # Fallback if no poster is found
            error_label = QLabel("Poster not found!")
            layout.addWidget(error_label)

        # Add movie description
        description_label = QLabel(movie_info['description'])
        description_label.setWordWrap(True)  # Enable text wrapping
        layout.addWidget(description_label)

        self.setLayout(layout)

# Run the application
app = QApplication([])
window = MovieApp()
window.show()
app.exec_()
