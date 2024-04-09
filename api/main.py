from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from pydantic import BaseModel
import matplotlib.pyplot as plt
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from pydub import AudioSegment
from typing import List, Dict
import os
import tempfile
import librosa
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure PostgreSQL database
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

# Define SQLAlchemy models
class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    age = Column(Integer)

class Recording(Base):
    __tablename__ = "recordings"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    patient_name = Column(String)  # Add patient_name column
    patient_age = Column(Integer)
    emotions = Column(JSON)
    emotion_percentages = Column(JSON)
    timestamp = Column(DateTime)


class PatientIn(BaseModel):
    name: str
    age: int

temp_files = []
# Create tables in the database
Base.metadata.bind = engine
Base.metadata.create_all(engine)

MODEL = tf.keras.models.load_model("/opt/render/project/src/models/models/1/mymodel.h5")
emotion_classes = ["sad", "disgust", "happy", "neutral", "angry", "calm", "surprise", "fear"]

@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI application!"}

@app.get("/ping")
def ping():
    return "Hello, I am alive"

# Function to save uploaded file to a temporary location
def save_uploaded_file(file: UploadFile) -> str:
    _, temp_file_path = tempfile.mkstemp(dir="/opt/render/project/src/temp", suffix=".wav")
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file.file.read())
    return temp_file_path

def divide_audio(audio_path: str, segment_length: float, temp_dir: str) -> List[np.ndarray]:
    audio = AudioSegment.from_file(audio_path)
    segment_length_ms = int(segment_length * 1000)
    segments = []
    for i in range(0, len(audio), segment_length_ms):
        temp_file_path = os.path.join(temp_dir, f"temp_audio_{i}.wav")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=temp_dir) as temp_file:
            temp_files.append(temp_file.name)  # Store temporary file paths for later deletion
            segment = audio[i:i+segment_length_ms]
            segment.export(temp_file_path, format="wav")
            features = get_features(temp_file_path)
            segments.append(features)
    return segments

def delete_files_in_folder(folder_path):
    files = os.listdir(folder_path)
    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

def noise(data):
    noise_amp = 0.035*np.random.uniform()*np.amax(data)
    data = data + noise_amp*np.random.normal(size=data.shape[0])
    return data

def stretch(data, rate=0.8):
    return librosa.effects.time_stretch(data,rate=0.8)

def shift(data):
    shift_range = int(np.random.uniform(low=-5, high = 5)*1000)
    return np.roll(data, shift_range)

def pitch(data, sampling_rate, pitch_factor=0.7):
    return librosa.effects.pitch_shift(data, sr=sampling_rate,n_steps = 1)

def extract_features(data,sample_rate):
    result = np.array([])
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
    result=np.hstack((result, zcr))
    stft = np.abs(librosa.stft(data))
    chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)
    result = np.hstack((result, chroma_stft))
    mfcc = np.mean(librosa.feature.mfcc(y=data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mfcc))
    rms = np.mean(librosa.feature.rms(y=data).T, axis=0)
    result = np.hstack((result, rms))
    mel = np.mean(librosa.feature.melspectrogram(y=data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mel))
    return result

def get_features(path):
    data, sample_rate = librosa.load(path, duration=2.5, offset=0.6)
    res1 = extract_features(data,sample_rate)
    result = np.array(res1)
    noise_data = noise(data)
    res2 = extract_features(noise_data,sample_rate)
    result = np.vstack((result, res2))
    rate = 0.8
    new_data = stretch(data)
    data_stretch_pitch = pitch(new_data, sample_rate)
    res3 = extract_features(data_stretch_pitch,sample_rate)
    result = np.vstack((result, res3))
    return result

@app.post("/predict")
def predict(patient_id: int, patient_age: int, patient_name: str, file: UploadFile = File(...)) -> Dict:
    file_path = save_uploaded_file(file)
    segments = divide_audio(file_path, segment_length=5, temp_dir="//opt//render//project//src//temp")
    predictions = []
    for segment in segments:
        scaler = StandardScaler()
        segment_features = scaler.fit_transform(segment)
        prediction = MODEL.predict(segment_features)
        predictions.append(prediction)

    delete_files_in_folder("E://mentalhealth# api//temp")
    aggregated_prediction = np.mean(predictions, axis=0)
    confidences = [[round(float(conf), 2) for conf in confidence_probs] for confidence_probs in aggregated_prediction]
    total_confidences = [sum(confidence) for confidence in zip(*confidences)]
    total_sum = sum(total_confidences)
    emotion_percentages = [round(float(conf / total_sum) * 100, 2) for conf in total_confidences]
    predicted_emotions = [emotion_classes[np.argmax(emotion_probs)] for emotion_probs in aggregated_prediction]
    timestamp = datetime.now()
    with SessionLocal() as db:
        db_recording = Recording(
            patient_id=patient_id,
            patient_name=patient_name,
            patient_age=patient_age,
            emotions=emotion_classes,
            emotion_percentages=emotion_percentages,
            timestamp=timestamp,
        )
        db.add(db_recording)
        db.commit()

    return {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "patient_age": patient_age,
        "emotions": emotion_classes,
        "emotion_percentages": emotion_percentages,
        "timestamp": timestamp,
    }

@app.post("/addnewpatient")
def create_patient(patient: PatientIn):
    with SessionLocal() as db:
        db_patient = Patient(name=patient.name, age=patient.age)
        db.add(db_patient)
        db.commit()
    return {"message": "Patient added successfully!"}

@app.get("/getpatients")
def get_patients():
    with SessionLocal() as db:
        patients = db.query(Patient).all()
    return patients

@app.get("/getpatient/{patient_id}")
def get_patient(patient_id: int):
    try:
        patient_id = int(patient_id)
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()

        if patient:
            return patient
        else:
            raise HTTPException(status_code=404, detail="Patient not found")

    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid patient ID format")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/deletepatient/{patient_id}")
def delete_patient(patient_id: int):
    try:
        with SessionLocal() as db:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")

            db.query(Recording).filter(Recording.patient_id == patient_id).delete()
            db.delete(patient)

            db.commit()
            return {"message": "Patient and their analysis deleted successfully!"}

    except HTTPException as e:
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/deleteanalysis/{analysis_id}")
def delete_analysis(analysis_id: int):
    try:
        with SessionLocal() as db:
            analysis = db.query(Recording).filter(Recording.id == analysis_id).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")

            db.delete(analysis)
            db.commit()
            return {"message": "Analysis deleted successfully!"}

    except HTTPException as e:
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/getanalysis/{patient_id}")
def get_analysis(patient_id: int):
    try:
        with SessionLocal() as db:
            analysis_results = db.query(Recording).filter(Recording.patient_id == patient_id).all()

        if not analysis_results:
            raise HTTPException(status_code=404, detail="No analysis found for the specified patient")

        return analysis_results

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=10000)
