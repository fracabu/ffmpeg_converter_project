from flask import Blueprint, request, jsonify, render_template, send_from_directory, current_app
import os
import subprocess
from gtts import gTTS
from gtts.tts import gTTSError
import time
import pyttsx3  # Aggiunto come fallback

bp = Blueprint('main', __name__)

# Definisci percorsi assoluti per le directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted')

# Crea le directory se non esistono
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = file.filename.replace(" ", "_").replace("(", "").replace(")", "")
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)
    
    return jsonify({'message': 'File uploaded successfully', 'file_path': input_path})

@bp.route('/convert', methods=['POST'])
def convert_file():
    try:
        data = request.json
        input_file = data.get('input_file')
        output_format = data.get('output_format', 'mp4')
        
        if not input_file or not os.path.exists(input_file):
            print(f"Invalid input file: {input_file}")
            return jsonify({'error': 'Invalid input file'}), 400
        
        # Genera nome file output
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(CONVERTED_FOLDER, f"{base_name}.{output_format}")
        
        command = [
            "ffmpeg",
            "-i", input_file,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_file
        ]
        
        print(f"Running command: {' '.join(command)}")
        
        result = subprocess.run(command, 
                              capture_output=True, 
                              text=True, 
                              check=False)
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            return jsonify({'error': 'Conversion failed'}), 500
        
        if os.path.exists(output_file):
            return jsonify({
                'message': 'File converted successfully',
                'output_file': os.path.basename(output_file)
            })
        else:
            return jsonify({'error': 'Output file not created'}), 500
            
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/generate_audio', methods=['POST'])
def generate_audio():
    try:
        data = request.json
        text = data.get('text')
        language = data.get('language', 'en')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Dividi il testo in chunks di circa 1000 caratteri
        # Cerca di dividere alle frasi complete
        def split_text(text, chunk_size=1000):
            chunks = []
            current_chunk = []
            current_size = 0
            
            # Dividi il testo in frasi
            sentences = text.replace('\n', ' ').split('. ')
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # Aggiungi il punto che è stato rimosso dallo split
                sentence = sentence + '.'
                
                if current_size + len(sentence) <= chunk_size:
                    current_chunk.append(sentence)
                    current_size += len(sentence)
                else:
                    if current_chunk:
                        chunks.append(' '.join(current_chunk))
                    current_chunk = [sentence]
                    current_size = len(sentence)
                    
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                
            return chunks

        # Genera un nome base per i file con timestamp
        timestamp = int(time.time())
        chunks = split_text(text)
        output_files = []

        for i, chunk in enumerate(chunks):
            output_filename = f"audio_{timestamp}_part{i+1}.mp3"
            output_path = os.path.join(CONVERTED_FOLDER, output_filename)

            try:
                # Prova prima con gTTS
                tts = gTTS(text=chunk, lang=language)
                tts.save(output_path)
                output_files.append(output_filename)
            except (gTTSError, Exception) as e:
                print(f"gTTS failed for chunk {i+1}, trying offline TTS: {str(e)}")
                try:
                    # Fallback a pyttsx3
                    engine = pyttsx3.init()
                    engine.save_to_file(chunk, output_path)
                    engine.runAndWait()
                    output_files.append(output_filename)
                except Exception as e2:
                    print(f"Offline TTS failed too for chunk {i+1}: {str(e2)}")
                    return jsonify({
                        'error': f'Failed to generate audio for part {i+1}'
                    }), 500

        # Se abbiamo più parti, combinale
        if len(output_files) > 1:
            final_output = f"audio_{timestamp}_complete.mp3"
            final_path = os.path.join(CONVERTED_FOLDER, final_output)
            
            # Crea una lista di file da concatenare
            with open(os.path.join(CONVERTED_FOLDER, "filelist.txt"), "w") as f:
                for file in output_files:
                    f.write(f"file '{file}'\n")
            
            # Usa FFmpeg per concatenare i file
            command = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", os.path.join(CONVERTED_FOLDER, "filelist.txt"),
                "-c", "copy",
                final_path
            ]
            
            subprocess.run(command, check=True)
            
            # Rimuovi i file temporanei
            for file in output_files:
                os.remove(os.path.join(CONVERTED_FOLDER, file))
            os.remove(os.path.join(CONVERTED_FOLDER, "filelist.txt"))
            
            return jsonify({
                'message': 'Audio generated successfully',
                'audio_file': final_output
            })
        else:
            # Se abbiamo solo una parte, restituisci quella
            return jsonify({
                'message': 'Audio generated successfully',
                'audio_file': output_files[0]
            })

    except Exception as e:
        print(f"Audio generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(
            directory=CONVERTED_FOLDER,
            path=filename,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500