from flask import Flask, request, jsonify, render_template, send_from_directory
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

# Load dataset
songs_df = pd.read_csv('data/spotify_millsongdata.csv')

# Combine features for better recommendations
songs_df['combined_features'] = songs_df.apply(lambda row: f"{row['song']} {row['artist']}", axis=1)

# NLTK initialization
nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()  # Lowercase
    text = text.translate(str.maketrans('', '', string.punctuation))  # Remove punctuation
    words = word_tokenize(text)  # Tokenize
    words = [word for word in words if word not in stop_words]  # Remove stopwords
    return ' '.join(words)

# Apply preprocessing to the combined features
songs_df['processed_features'] = songs_df['combined_features'].apply(preprocess_text)

# Spotify API credentials (Use your own credentials)
SPOTIPY_CLIENT_ID = '5b800f43996944a8ab89514f14df8336'
SPOTIPY_CLIENT_SECRET = 'd5818fea44e94c1aa6e270a21d04f9fe'

# Initialize Spotipy client
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                                         client_secret=SPOTIPY_CLIENT_SECRET))


# Preprocess data for recommendation
tfidf_vectorizer = TfidfVectorizer()
tfidf_matrix = tfidf_vectorizer.fit_transform(songs_df['processed_features'].values.astype('U'))

# Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.','index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    processed_input = preprocess_text(user_message)

    if "recommend" in processed_input or "song" in processed_input:
        # Handle song recommendation
        tfidf_user_input = tfidf_vectorizer.transform([processed_input])
        cosine_similarities = cosine_similarity(tfidf_user_input, tfidf_matrix).flatten()

        top_indices = cosine_similarities.argsort()[:-6:-1]

        recommendations = []
        for idx in top_indices:
            song_name = songs_df['song'].iloc[idx]
            artist = songs_df['artist'].iloc[idx]

    # Search on Spotify to get the track's details
            results = sp.search(q=f'track:{song_name} artist:{artist}', type='track', limit=1)

            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                spotify_image = track['album']['images'][0]['url'] if track['album']['images'] else None
                spotify_link = track['external_urls']['spotify']  # Get the direct Spotify link
            else:
                spotify_image = None
                spotify_link = "No valid Spotify link available"  # Provide a default value if no song is found

            recommendations.append({
                'song_name': song_name,
                'artist': artist,
                'spotify_link': spotify_link,  # Ensure spotify_link always has a value
                'spotify_image': spotify_image
            })


        response = "Here are some song recommendations based on your input:" if recommendations else "Sorry, I couldn't find any recommendations for you."
        return jsonify({'response': response, 'recommendations': recommendations})

    return jsonify({'response': "Please ask for song recommendations.", 'recommendations': []})


if __name__ == '__main__':
    app.run(debug=True)

