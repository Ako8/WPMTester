import random
from datetime import datetime

from flask import Flask, render_template, session, redirect, url_for, request
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdadasdasdasdsad'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
socketio = SocketIO(app)
db = SQLAlchemy(app)


class Song(db.Model):
    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String)
    lyrics = db.Column(db.Text)


class LeaderBoard(db.Model):
    __tablename__ = 'leaderboard'

    id = db.Column(db.Integer, primary_key=True)
    wpm = db.Column(db.Integer)
    time = db.Column(db.Integer)
    words = db.Column(db.Integer)
    username = db.Column(db.String)


def dict_lyrics(lyrics):
    lyrics = (lyrics.replace(',', '')).lower()
    lyrics = lyrics.split(" ")
    return [{'id': i, "word": word, "result": None} for i, word in enumerate(lyrics)]


current_word_index = 0
start_time = None
numbe_of_letters = 60
default_username = 'user_undefied'


@app.route('/<theme>')
def theme(theme):
    if not session.get('theme', 'day'):
        session['theme'] = 'day'
    session['theme'] = theme

    return redirect(url_for('home'))


@app.route('/')
def home():
    global numbe_of_letters, default_username

    user_ip = request.remote_addr
    default_username = generate_default_username(user_ip)

    song = Song.query.get(1)
    leaderboard = LeaderBoard.query.order_by(LeaderBoard.wpm.desc()).all()

    if song:
        if song.id == 1:
            common_words_list = song.lyrics.split()
            random_string = ' '.join(random.sample(common_words_list, k=numbe_of_letters))
            session['lyrics_dict'] = dict_lyrics(random_string)
        else:
            session['lyrics_dict'] = dict_lyrics(song.lyrics)
        return render_template('index.html', artist=song.song_name, leaderboard=leaderboard)
    else:
        return "Song not found."


@socketio.on('connect')
def connect():
    global current_word_index
    session['start_time'] = datetime.now()
    emit("new_word", {'word': session['lyrics_dict']})


@socketio.on('check_word')
def handle_check_word(data):
    global current_word_index, numbe_of_letters, default_username
    lyrics_dict = session.get('lyrics_dict')
    step_count = len(lyrics_dict)
    elapsed_time = (datetime.now() - session.get('start_time')).total_seconds()
    if current_word_index == step_count - 1 and data['word'] == lyrics_dict[current_word_index]['word']:
        wpm = calculate_wpm(lyrics_dict, data['took'])
        time = data['took']
        if 'name' in data:
            default_username = data['name']
        add_to_leaderboard(wpm, time, numbe_of_letters, default_username)
        emit('game_over', {'wpm': wpm})
    elif data['word'] == lyrics_dict[current_word_index]['word']:
        lyrics_dict[current_word_index]['result'] = 'right'
    else:
        lyrics_dict[current_word_index]['result'] = 'wrong'

    current_word_index += 1
    if current_word_index < step_count:
        emit('new_word', {'word': lyrics_dict, "time": elapsed_time})


@socketio.on('reset_game')
def reset_game():
    global current_word_index
    current_word_index = 0
    session['start_time'] = None
    session['lyrics_dict'] = []
    emit("game_reset")


@socketio.on('setup')
def setup(data):
    global numbe_of_letters
    numbe_of_letters = data['letters']
    return redirect(url_for('home'))


def calculate_wpm(words, sec_took):
    right_words = [word for word in words if word['result'] == 'right']
    words_string = ' '.join([word['word'] for word in right_words])
    wpm = len(words_string) / 5 * (60 / sec_took)

    return int(wpm)


def add_to_leaderboard(wpm, time, words, username):
    lead = LeaderBoard.query.filter_by(username=username).first()
    print(lead.wpm)
    if lead:
        if wpm > lead.wpm:
            lead.wpm = wpm
    else:
        new_lead = LeaderBoard(
            wpm=wpm,
            time=time,
            words=words,
            username=username
        )
        db.session.add(new_lead)
    db.session.commit()
    db.session.close()


def generate_default_username(ip_address):
    username = f"User{''.join(ip_address.split('.'))}"
    return username


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
