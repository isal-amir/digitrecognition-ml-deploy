# Part 3: FastAPI Backend for Digit Recognition
# Save this as: main.py

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
import joblib
import io
import base64

# Initialize FastAPI app
app = FastAPI(
    title="Digit Recognition API",
    description="API for recognizing handwritten digits using ML",
    version="1.0.0"
)

# Add CORS middleware - allows our HTML frontend to talk to this API
# CORS = Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Load the trained model when the app starts
# This happens ONCE when server starts, not on every request
print("Loading model...")
try:
    model = joblib.load('digit_classifier_rf.pkl')
    print("✓ Model loaded successfully!")
except FileNotFoundError:
    print("❌ Model file not found! Please run Part 2 to train the model.")
    model = None


def preprocess_image(image_data):
    """
    Preprocess image to match training data format
    
    Args:
        image_data: PIL Image object
        
    Returns:
        numpy array ready for prediction, shape (1, 64)
    """
    # Convert to grayscale
    img_gray = image_data.convert('L')
    
    # Resize to 8x8 pixels (same as training data)
    img_resized = img_gray.resize((8, 8), Image.Resampling.LANCZOS)
    
    # Convert to numpy array
    img_array = np.array(img_resized)
    
    # Invert if background is white (model expects dark background)
    if img_array.mean() > 127:
        img_array = 255 - img_array
    
    # Normalize to 0-16 range (same as training data)
    img_normalized = img_array / 255.0 * 16.0
    
    # Flatten and reshape for prediction
    img_flattened = img_normalized.flatten()
    img_ready = img_flattened.reshape(1, -1)
    
    return img_ready


# Route 1: Root endpoint - just to check if API is running
@app.get("/")
def read_root():
    """
    Root endpoint - returns welcome message
    Access at: http://localhost:8000/
    """
    return {
        "message": "Welcome to Digit Recognition API!",
        "status": "running",
        "endpoints": {
            "predict_file": "/predict/file",
            "predict_base64": "/predict/base64",
            "docs": "/docs"
        }
    }


# Route 2: Health check
@app.get("/health")
def health_check():
    """
    Check if API and model are working
    Access at: http://localhost:8000/health
    """
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }


# Route 3: Predict from uploaded file
@app.post("/predict/file")
async def predict_from_file(file: UploadFile = File(...)):
    """
    Predict digit from uploaded image file (JPG, PNG)
    
    How to use:
    - Send POST request to /predict/file
    - Include image file in form-data with key 'file'
    
    Returns:
        JSON with prediction and confidence scores
    """
    if model is None:
        return JSONResponse(
            status_code=500,
            content={"error": "Model not loaded. Please train the model first."}
        )
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Open image with PIL
        image = Image.open(io.BytesIO(contents))
        
        # Preprocess image
        processed_img = preprocess_image(image)
        
        # Make prediction
        prediction = model.predict(processed_img)
        
        # Get probability scores for all digits (0-9)
        probabilities = model.predict_proba(processed_img)[0]
        
        # Create result
        result = {
            "prediction": int(prediction[0]),
            "confidence": float(probabilities[prediction[0]]),
            "all_probabilities": {
                str(i): float(prob) for i, prob in enumerate(probabilities)
            }
        }
        
        return result
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Error processing image: {str(e)}"}
        )


# Route 4: Predict from base64 encoded image
@app.post("/predict/base64")
async def predict_from_base64(data: dict):
    """
    Predict digit from base64 encoded image
    
    Expected JSON format:
    {
        "image": "data:image/png;base64,iVBORw0KG..."
    }
    
    This is what our HTML canvas will use!
    
    Returns:
        JSON with prediction and confidence
    """
    if model is None:
        return JSONResponse(
            status_code=500,
            content={"error": "Model not loaded. Please train the model first."}
        )
    
    try:
        # Get base64 string from request
        image_data = data.get("image")
        
        if not image_data:
            return JSONResponse(
                status_code=400,
                content={"error": "No image data provided"}
            )
        
        # Remove data URL prefix if present
        # Canvas sends: "data:image/png;base64,actual_base64_here"
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Open image with PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # Preprocess image
        processed_img = preprocess_image(image)
        
        # Make prediction
        prediction = model.predict(processed_img)
        probabilities = model.predict_proba(processed_img)[0]
        
        # Create result
        result = {
            "prediction": int(prediction[0]),
            "confidence": float(probabilities[prediction[0]]),
            "all_probabilities": {
                str(i): float(prob) for i, prob in enumerate(probabilities)
            }
        }
        
        return result
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Error processing image: {str(e)}"}
        )


# This runs when you execute: python main.py
if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("Starting Digit Recognition API Server...")
    print("=" * 60)
    print("📍 API will be available at: http://localhost:8000")
    print("📖 Interactive docs at: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)