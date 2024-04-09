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
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
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
# Create tables in the database
# Bind the engine to the Base class
Base.metadata.bind = engine

# Create tables in the database
Base.metadata.create_all(engine)

MODEL = tf.keras.models.load_model("../models/models/1")

emotion_classes = ["sad", "disgust", "happy", "neutral", "angry", "calm", "surprise", "fear"]

@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI application!"}

@app.get("/ping")
async def ping():
    return "Hello, I am alive"

# Function to save uploaded file to a temporary location
async def save_uploaded_file(file: UploadFile) -> str:
    # Create a temporary file in a custom temporary directory
    _, temp_file_path = tempfile.mkstemp(dir="E:/mentalhealth/api/temp", suffix=".wav")
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())
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
    # Get a list of all files in the folder
    files = os.listdir(folder_path)
    
    # Iterate over each file and delete it
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
    # ZCR
    result = np.array([])
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
    result=np.hstack((result, zcr)) # stacking horizontally

    # Chroma_stft
    stft = np.abs(librosa.stft(data))
    chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)
    result = np.hstack((result, chroma_stft)) # stacking horizontally

    # MFCC
    mfcc = np.mean(librosa.feature.mfcc(y=data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mfcc)) # stacking horizontally

    # Root Mean Square Value
    rms = np.mean(librosa.feature.rms(y=data).T, axis=0)
    result = np.hstack((result, rms)) # stacking horizontally

    # MelSpectogram
    mel = np.mean(librosa.feature.melspectrogram(y=data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mel)) # stacking horizontally

    return result

def get_features(path):
    # duration and offset are used to take care of the no audio in start and the ending of each audio files as seen above.
    data, sample_rate = librosa.load(path, duration=2.5, offset=0.6)

    # without augmentation
    res1 = extract_features(data,sample_rate)
    result = np.array(res1)

    # data with noise
    noise_data = noise(data)
    res2 = extract_features(noise_data,sample_rate)
    result = np.vstack((result, res2)) # stacking vertically
    rate = 0.8
    # data with stretching and pitching
    new_data = stretch(data)
    data_stretch_pitch = pitch(new_data, sample_rate)
    res3 = extract_features(data_stretch_pitch,sample_rate)
    result = np.vstack((result, res3)) # stacking vertically

    return result


@app.post("/predict")
async def predict(patient_id: int, patient_age: int, patient_name: str, file: UploadFile = File(...)) -> Dict:
    print(0)
    file_path = await save_uploaded_file(file)  # Save uploaded file to a temporary location
    print(4)
    segments = divide_audio(file_path, segment_length=5, temp_dir="E://mentalhealth//api//temp")  # Divide audio into segments
    print(5)
    predictions = []
    for segment in segments:
        scaler = StandardScaler()
        segment_features = scaler.fit_transform(segment)
        prediction = MODEL.predict(segment_features)
        predictions.append(prediction)

    delete_files_in_folder("E://mentalhealth# api//temp")
    # Aggregate predictions for all segments
    aggregated_prediction = np.mean(predictions, axis=0)

    # Extract all confidences for all predictions
    confidences = [[round(float(conf), 2) for conf in confidence_probs] for confidence_probs in aggregated_prediction]

    # Calculate total confidence for each emotion across all segments
    total_confidences = [sum(confidence) for confidence in zip(*confidences)]

    # Calculate total sum of confidence scores
    total_sum = sum(total_confidences)

    # Calculate percentage of each emotion present in the call recording
    emotion_percentages = [round(float(conf / total_sum) * 100, 2) for conf in total_confidences]

    # Convert prediction probabilities to emotion labels
    predicted_emotions = [emotion_classes[np.argmax(emotion_probs)] for emotion_probs in aggregated_prediction]

    timestamp = datetime.now()

    # Store data in the PostgreSQL database
    async with SessionLocal() as db:
        db_recording = Recording(
            patient_id=patient_id,
            patient_name=patient_name,
            patient_age=patient_age,
            emotions=emotion_classes,
            emotion_percentages=emotion_percentages,
            timestamp=timestamp,
        )
        db.add(db_recording)
        await db.commit()

    # Return predicted emotions, confidences, and paths to generated plots
    return {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "patient_age": patient_age,
        "emotions": emotion_classes,
        "emotion_percentages": emotion_percentages,
        "timestamp": timestamp,
    }

@app.post("/addnewpatient")
async def create_patient(patient: PatientIn):
    async with SessionLocal() as db:
        db_patient = Patient(name=patient.name, age=patient.age)
        db.add(db_patient)
        await db.commit()
    return {"message": "Patient added successfully!"}

@app.get("/getpatients")
async def get_patients():
    async with SessionLocal() as db:
        patients = db.query(Patient).all()
    return patients

@app.get("/getpatient/{patient_id}")
async def get_patient(patient_id: int):
    try:
        # Convert patient_id to integer
        patient_id = int(patient_id)

        async with SessionLocal() as db:
            # Find the patient with the specified ID
            patient = db.query(Patient).filter(Patient.id == patient_id).first()

        if patient:
            return patient
        else:
            raise HTTPException(status_code=404, detail="Patient not found")

    except ValueError as e:
        # Handle invalid patient_id format
        raise HTTPException(status_code=400, detail="Invalid patient ID format")

    except Exception as e:
        # Handle any other unexpected exceptions
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/deletepatient/{patient_id}")
async def delete_patient(patient_id: int):
    try:
        async with SessionLocal() as db:
            # Check if the patient exists
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")

            # Delete all recordings associated with the patient
            db.query(Recording).filter(Recording.patient_id == patient_id).delete()

            # Delete the patient
            db.delete(patient)

            await db.commit()
            return {"message": "Patient and their analysis deleted successfully!"}

    except HTTPException as e:
        raise e

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/deleteanalysis/{analysis_id}")
async def delete_analysis(analysis_id: int):
    try:
        async with SessionLocal() as db:
            # Check if the analysis exists
            analysis = db.query(Recording).filter(Recording.id == analysis_id).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")

            # Delete the specific analysis
            db.delete(analysis)

            await db.commit()
            return {"message": "Analysis deleted successfully!"}

    except HTTPException as e:
        raise e

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/getanalysis/{patient_id}")
async def get_analysis(patient_id: int):
    try:
        async with SessionLocal() as db:
            analysis_results = db.query(Recording).filter(Recording.patient_id == patient_id).all()

        if not analysis_results:
            raise HTTPException(status_code=404, detail="No analysis found for the specified patient")

        return analysis_results

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8000)

