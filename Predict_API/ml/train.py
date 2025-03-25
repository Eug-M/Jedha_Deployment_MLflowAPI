import os
#import argparse
import pandas as pd
import numpy as np
import time
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.model_selection import train_test_split 
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import  StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])


if __name__ == "__main__":

    ### MLFLOW Experiment setup
    experiment_name="Getaround_PredictPricing"
    mlflow.set_experiment(experiment_name)
    experiment = mlflow.get_experiment_by_name(experiment_name)
    MODEL_NAME = "XGBRegressor" # RandomForestRegressor, LinearRegression, XGBRegressor, AdaBoostRegressor
    DF_PREPROCESS = "wo10Cats" # wo10Cats, AllCats

    client = mlflow.tracking.MlflowClient()
    #run = client.create_run(experiment.experiment_id)

    # Parse arguments given in shell script
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--n_estimators")
    # parser.add_argument("--min_samples_split")
    # args = parser.parse_args()

    # Import and preprocess dataset
    pricing = pd.read_csv('https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_pricing_project.csv')
    pricing.drop("Unnamed: 0", axis=1, inplace=True)

    indexes_mileage = []
    indexes_mileage.append(pricing.loc[(pricing['mileage'] < 0), 'mileage'].index.to_list())
    indexes_mileage.append(pricing.loc[(pricing['mileage'] > 1000000), 'mileage'].index.to_list())
    indexes_power = []
    indexes_power.append(pricing.loc[(pricing['engine_power'] == 0),'engine_power'].index.to_list())
    indexes_power.append(pricing.loc[(pricing['engine_power'] > 400),'engine_power'].index.to_list())

    for index in indexes_mileage:
        for ind in index:
            pricing.at[ind, 'mileage'] = np.nan
    for index in indexes_power:
        for ind in index:
            pricing.at[ind, 'engine_power'] = np.nan

    if DF_PREPROCESS == 'wo10Cats':
        for col in ["fuel", 'model_key', 'paint_color']:
            df_counts = pd.DataFrame(pricing[col].value_counts())
            for category in df_counts.loc[df_counts['count']<=10,:].index.to_list():
                for row in pricing.loc[pricing[col]==category].index.to_list():
                    pricing.drop(row, axis=0, inplace=True)
    else:
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

    # X, y split 
    features_list = list(pricing.columns)
    features_list.remove('rental_price_per_day')
    target_variable = 'rental_price_per_day'
    X = pricing.loc[:, features_list]
    Y = pricing.loc[:, target_variable]
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=0)

    # Preprocessing 
    categorical_features = features_list
    categorical_features.remove("mileage")
    categorical_features.remove("engine_power")
    numeric_features = ["mileage", "engine_power"]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="mean")),  
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = OneHotEncoder(drop="first")
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    print("training model...")
    
    # Time execution
    start_time = time.time()

    # Define model 
    if MODEL_NAME == 'RandomForestRegressor':
        model = Pipeline(steps=[
        ("Preprocessing", preprocessor),
        ("Regressor", RandomForestRegressor(max_depth=15, min_samples_leaf=2, 
                    min_samples_split=4, n_estimators=200))
        ], verbose=True)
    elif MODEL_NAME == 'XGBRegressor':
        model = Pipeline(steps=[
        ("Preprocessing", preprocessor),
        ("Regressor", XGBRegressor(max_depth=4, min_child_weight=10, n_estimators=125))
        ], verbose=True)
    elif MODEL_NAME == 'LinearRegression':
        model = Pipeline(steps=[
        ("Preprocessing", preprocessor),
        ("Regressor", LinearRegression())
        ], verbose=True)
    else: # AdaBoostRegressor
        model = Pipeline(steps=[
        ("Preprocessing", preprocessor),
        ("Regressor", AdaBoostRegressor(learning_rate=1.0, loss='exponential', n_estimators=10))
        ], verbose=True)

    # Log experiment to MLFlow
    with mlflow.start_run(experiment_id = experiment.experiment_id) as run:
        mlflow.sklearn.autolog() 
        mlflow.log_param("type_MLmodel", MODEL_NAME) 
        mlflow.log_param("type_preprocess", DF_PREPROCESS) 

        model.fit(X_train, Y_train)
        Y_train_pred = model.predict(X_train)
        Y_test_pred = model.predict(X_test)

        mlflow.log_metric('R2_train', r2_score(Y_train, Y_train_pred))
        mlflow.log_metric('R2_test', r2_score(Y_test, Y_test_pred))

        # Log model separately to have more flexibility on setup 
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="Getaround_PredictPricing",
            #registered_model_name="Getaround_PredictPricing_"+str(MODEL_NAME)+"_"+str(DF_PREPROCESS),
            signature=infer_signature(X_train, Y_train_pred)
        )
        #mlflow.end_run()
        
    print("...Done!")
    print(f"---Total training time: {time.time()-start_time}")