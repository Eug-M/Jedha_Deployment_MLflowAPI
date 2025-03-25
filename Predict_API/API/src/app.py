import os
import uvicorn
import mlflow 
import pandas as pd 
from pydantic import BaseModel
from typing import Literal, List, Union
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse

default_port = os.environ.get('DEFAULT_PORT')
mlops_server_uri = os.environ.get('MLOPS_SERVER_URI')
model_path = os.environ.get('MODEL_PATH')

description = """
Getaround Predict prices API helps you optimize your car's pricing based on its features. 
It has one endpoint:

## Predict 

Where you can:
* Get the price prediction according to your car's features

Check out documentation for more information on this endpoint. 
"""

tags_metadata = [
    {
        "name": "Predict",
        "description": "Get the price prediction according to your car's features",
    }
]

app = FastAPI(
    title="🚗 Getaround Predict prices",
    description=description,
    version="1.0",
    contact={
        "name": "GetAround API - by Eugénie",
        "url": "https://eug-m-jedha-api.hf.space",
    },
    openapi_tags=tags_metadata
)

class PredictionFeatures(BaseModel):
    model_key: str
    mileage: float
    engine_power: float
    fuel: str
    paint_color: str
    car_type: str
    private_parking_available: bool
    has_gps: bool
    has_air_conditioning: bool
    automatic_car: bool
    has_getaround_connect: bool
    has_speed_regulator: bool
    winter_tires: bool


@app.post("/predict", tags=["Predict"])
async def predict(predictionFeatures: PredictionFeatures):
    """
    Prediction for one observation. Endpoint will return a dictionnary like this:

    ```
    {'prediction': PREDICTION_VALUE[0,500]}
    ```

    You need to give this endpoint all columns values as dictionnary, or form data, in this order: 
    - model of your car, as string (accepted values: Citroën, Renault, BMW, Peugeot, Audi, Nissan, 
    Mitsubishi, Mercedes, Volkswagen, Toyota, SEAT, Subaru, Opel, Ferrari, PGO, Maserati, Suzuki, 
    Porsche, Ford, KIA Motors, Alfa Romeo, Fiat, Lexus, Lamborghini, Mini, Mazda, Honda, Yamaha)
    - mileage of your car, as integer or float
    - engine power of your car, as integer or float
    - fuel type of your car, as string (accepted values: diesel, petrol, hybrid_petrol, electro)
    - color of your car, as string (accepted values: black, grey, blue, white, brown, silver, 
    red, beige, green, orange)
    - type of your car, as string (accepted values: estate, sedan, suv, hatchback, subcompact, 
    coupe, convertible, van)
    - is a private parking available, as a boolean
    - do you provide a GPS, as a boolean
    - does your car have air conditioning, as a boolean
    - is your car automatic, as a boolean
    - do you have getaroung connect, as a boolean
    - does your car have a speed regulator, as a boolean
    - do you have winter tires, as a boolean
    """
    # Read data 
    pricing = pd.DataFrame(dict(predictionFeatures), index=[0])
    dict_changes = {}
    dict_changes['model_key'] = {'Fiat': 'low_price', 'Mazda': 'low_price', 'Ford': 'low_price', 'Mercedes': 'low_price',
                                    'Porsche': 'medium_price', 'Honda': 'medium_price', 'Yamaha': 'medium_price', 
                                    'Lamborghini': 'medium_price', 'Alfa Romeo': 'medium_price', 'KIA Motors': 'medium_price', 
                                    'Opel': 'medium_price',
                                    'Suzuki': 'high_price', 'Mini': 'high_price', 'Lexus': 'high_price', 'Maserati': 'high_price'
                                    }
    dict_changes['fuel'] = {'hybrid_petrol': 'high_price', 'electro': 'high_price'}
    dict_changes['paint_color'] = {'orange': 'high_price', 'white': 'high_price'}
    for col in dict_changes.keys():
        pricing = pricing.replace({col: dict_changes[col]})

    # Load model as a PyFuncModel from mlflow
    mlflow.set_tracking_uri(mlops_server_uri)
    print('tracking OK')
    loaded_model = mlflow.pyfunc.load_model(model_path)
    print('loaded OK')
    prediction = loaded_model.predict(pricing)
    print('prediction OK')

    # Format response
    response = {"prediction": prediction.tolist()[0]}
    return response

# @app.exception_handler(Exception)
# async def global_exception_handler(_: Request, ex: Exception):
#     return JSONResponse(
#         status_code=500,
#         content={"detail": str(ex)}
#     )

if __name__=="__main__":
    uvicorn.run(app, host='localhost', port=default_port)