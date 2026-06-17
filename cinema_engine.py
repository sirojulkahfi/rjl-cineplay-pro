from flask import Flask, request, jsonify
from flask_cors import CORS
import vlc
import os

app = Flask(__name__)
CORS(app)

MOVIES_DIR = "/home/ubuntu/cinema-theater/public/movies"

vlc_args = ["--fullscreen", "--video-on-top", "--mouse-hide-timeout=0", "--hwdec=vaapi"]
instance = vlc.Instance(" ".join(vlc_args))
player = instance.media_player_new()

playlist_queue = []
current_index = -1

@app.route('/api/playlist/add', methods=['POST'])
def add_to_playlist():
    filename = request.json.get('filename')
    if filename and filename not in playlist_queue:
        playlist_queue.append(filename)
    return jsonify({"playlist": playlist_queue})

@app.route('/api/playlist/clear', methods=['POST'])
def clear_playlist():
    global playlist_queue, current_index
    player.stop()
    playlist_queue, current_index = [], -1
    return jsonify({"status": "success"})

@app.route('/api/playlist/get', methods=['GET'])
def get_playlist():
    return jsonify({"playlist": playlist_queue, "current_index": current_index})

@app.route('/api/player/play-index', methods=['POST'])
def play_index():
    global current_index
    idx = int(request.json.get('index', 0))
    if 0 <= idx < len(playlist_queue):
        current_index = idx
        filepath = os.path.join(MOVIES_DIR, playlist_queue[current_index])
        player.set_media(instance.media_new(filepath))
        player.play()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/api/player/control', methods=['POST'])
def control():
    action = request.json.get('action')
    global current_index
    if action == 'play': player.play()
    elif action == 'pause': player.pause()
    elif action == 'stop': player.stop()
    elif action == 'next' and current_index + 1 < len(playlist_queue):
        current_index += 1
        player.set_media(instance.media_new(os.path.join(MOVIES_DIR, playlist_queue[current_index])))
        player.play()
    elif action == 'prev' and current_index - 1 >= 0:
        current_index -= 1
        player.set_media(instance.media_new(os.path.join(MOVIES_DIR, playlist_queue[current_index])))
        player.play()
    return jsonify({"current_index": current_index})

# GET STATUS: Ditambah pelacak Track Audio & Subtitle
@app.route('/api/player/status', methods=['GET'])
def player_status():
    current_time = player.get_time()
    total_time = player.get_length()
    
    # Ambil list audio tracks bawaan film dari VLC
    audio_tracks = []
    for track_id, track_name in player.audio_get_track_description():
        audio_tracks.append({"id": track_id, "name": track_name.decode('utf-8', errors='ignore')})
        
    # Ambil list subtitle tracks bawaan film dari VLC
    subtitle_tracks = []
    for track_id, track_name in player.video_get_spu_description():
        subtitle_tracks.append({"id": track_id, "name": track_name.decode('utf-8', errors='ignore')})

    return jsonify({
        "is_playing": player.is_playing(),
        "current_time": max(0, current_time // 1000),
        "total_time": max(0, total_time // 1000),
        "current_index": current_index,
        "audio_tracks": audio_tracks,
        "subtitle_tracks": subtitle_tracks,
        "current_audio": player.audio_get_track(),
        "current_subtitle": player.video_get_spu()
    })

@app.route('/api/player/seek', methods=['POST'])
def player_seek():
    seconds = int(request.json.get('seconds', 0))
    player.set_time(seconds * 1000)
    return jsonify({"status": "success"})

# SET AUDIO TRACK VIA WEB
@app.route('/api/player/set-audio', methods=['POST'])
def set_audio():
    track_id = int(request.json.get('id', -1))
    player.audio_set_track(track_id)
    return jsonify({"status": "success"})

# SET SUBTITLE TRACK VIA WEB
@app.route('/api/player/set-subtitle', methods=['POST'])
def set_subtitle():
    track_id = int(request.json.get('id', -1))
    player.video_set_spu(track_id)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)