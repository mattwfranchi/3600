import json


jsontext = {'Records': [{'eventID': '0b710a893261f64cc9332025d09bcc24', 'eventName': 'INSERT', 'eventVersion': '1.1', 'eventSource': 'aws:dynamodb', 'awsRegion': 'us-east-1', 'dynamodb': {'ApproximateCreationDateTime': 1605485564.0, 'Keys': {'query': {'S': 'Clemson'}}, 'NewImage': {'emails': {'L': [{'S': 'mwfranc@clemson.edu'}, {'S': 'rkahn@clemson.edu'}]}, 'timeframe': {'S': 'w'}, 'query': {'S': 'Clemson'}}, 'SequenceNumber': '262500000000019827576131', 'SizeBytes': 81, 'StreamViewType': 'NEW_IMAGE'}, 'eventSourceARN': 'arn:aws:dynamodb:us-east-1:265913726939:table/NewsItems/stream/2020-11-15T20:23:49.112'}]}

records = jsontext['Records']
print(records)
record = records[0]



query = jsontext['Records'][0]["dynamodb"]["NewImage"]["query"]["S"]
timeframe = jsontext['Records'][0]["dynamodb"]["NewImage"]["timeframe"]["S"]
raw_emails = jsontext['Records'][0]["dynamodb"]["NewImage"]["emails"]["L"]
emails = []
for email in raw_emails:
    emails.append(email["S"])
print(emails)
print(query)
print(timeframe)




