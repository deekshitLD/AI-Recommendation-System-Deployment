import pandas as pd
import numpy as np
import boto3
from surprise import Dataset, Reader, KNNWithMeans

# Load the user-item rating data
data = pd.read_csv('ratings.csv')

# Preprocess the data
reader = Reader(rating_scale=(1, 5))
dataset = Dataset.load_from_df(data[['user_id', 'item_id', 'rating']], reader)

# Train the collaborative filtering model
model = KNNWithMeans(k=50, sim_options={'name': 'pearson_baseline', 'user_based': False})
trainset = dataset.build_full_trainset()
model.fit(trainset)

# Save the model to a file
model_file = 'recommendation_model.pkl'
model.save(model_file)

# Upload the model file to AWS S3
bucket_name = 'your-bucket-name'
s3_client = boto3.client('s3')
s3_client.upload_file(model_file, bucket_name, model_file)

# Deploy the model using AWS Lambda and API Gateway
lambda_client = boto3.client('lambda')
api_gateway_client = boto3.client('apigateway')

# Create the Lambda function
lambda_function_name = 'recommendation_function'
lambda_function_handler = 'lambda_function.lambda_handler'
lambda_function_runtime = 'python3.8'
lambda_function_role = 'arn:aws:iam::your-account-id:role/lambda-role'

lambda_response = lambda_client.create_function(
    FunctionName=lambda_function_name,
    Runtime=lambda_function_runtime,
    Role=lambda_function_role,
    Handler=lambda_function_handler,
    Code={'S3Bucket': bucket_name, 'S3Key': model_file}
)

# Create the API Gateway REST API
api_name = 'recommendation_api'
api_description = 'API for recommendation system'
api_response = api_gateway_client.create_rest_api(name=api_name, description=api_description)

# Create the API Gateway Lambda integration
integration_response = api_gateway_client.put_integration(
    restApiId=api_response['id'],
    resourceId=api_response['rootResourceId'],
    httpMethod='POST',
    integrationHttpMethod='POST',
    type='AWS',
    uri='arn:aws:apigateway:your-region:lambda:path/2015-03-31/functions/' + lambda_response['FunctionArn'] + '/invocations'
)

# Deploy the API
deployment_response = api_gateway_client.create_deployment(
    restApiId=api_response['id'],
    stageName='prod'
)

# Get the API Gateway endpoint URL
endpoint_url = deployment_response['response']['url']

print("Recommendation system deployed successfully.")
print("API Gateway Endpoint URL:", endpoint_url)
