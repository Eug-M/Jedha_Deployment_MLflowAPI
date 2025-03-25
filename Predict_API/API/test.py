import requests 
import json
import pandas as pd 


#### Test ML Model 

def test_prediction():

    df = pd.read_csv('https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_pricing_project.csv')
    df = df.iloc[:,1:].sample(1)

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
        df = df.replace({col: dict_changes[col]})
    print(df)

    values = []
    for element in df.iloc[0,:].values.tolist():
        if type(element) != str:
            values.append(element.item())
        else:
            values.append(element)
    df_dict = {key:value for key, value in zip(df.columns, values)}
    response = requests.post(
        "https://eug-m-jedha-api.hf.space/predict",
        data=json.dumps(df_dict)
    )

    print('response: ', response, response.content)

test_prediction()

