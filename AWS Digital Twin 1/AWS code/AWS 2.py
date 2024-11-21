import json
import boto3

# Initialize clients (add more as needed, e.g., DynamoDB, S3)
dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Log the incoming event
    print("Received event: ", json.dumps(event, indent=2))
    
    # Extract the sensor data
    try:
        message = json.loads(event['Records'][0]['Sns']['Message'])
        temperature = message['temperature']
        humidity = message['humidity']
        soil_moisture = message['soil_moisture']
        timestamp = message['timestamp']
    except KeyError as e:
        print(f"Error extracting data: {e}")
        return {"statusCode": 400, "body": "Bad Data Format"}

    # Example: Save to DynamoDB (adjust table name and attributes)
    dynamodb.put_item(
        TableName='SensorData',
        Item={
            'timestamp': {'S': timestamp},
            'temperature': {'N': str(temperature)},
            'humidity': {'N': str(humidity)},
            'soil_moisture': {'N': str(soil_moisture)}
        }
    )
    print("Data saved to DynamoDB")

    # Example: Save to S3 (adjust bucket name and object key)
    s3.put_object(
        Bucket='your-s3-bucket-name',
        Key=f'sensor_data/{timestamp}.json',
        Body=json.dumps(message)
    )
    print("Data saved to S3")

    return {"statusCode": 200, "body": "Data processed successfully"}
