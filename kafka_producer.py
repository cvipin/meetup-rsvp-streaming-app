# @Vipin Chaudhari

import time
import requests
from kafka import KafkaProducer
from json import dumps
import json
import constants as const

if __name__ == "__main__":

    print("Meetup stream started ... ")

    kafka_producer = KafkaProducer(bootstrap_servers=const.kafka_server, value_serializer=lambda x: dumps(x).encode('utf-8'),api_version=(0, 10, 1))

    while True:
        try:
            res_stream_api = requests.get(const.meetup_rsvp_stream_api_url, stream=True)
            if res_stream_api.status_code == 200:
                for api_response in res_stream_api.iter_lines():
                    
                    print("Message received from meetup")

                    # convert message from bytes to disctionary
                    api_response = json.loads(api_response)
                    
                    print("Ready to send message to kafka topic")
                    kafka_producer.send(const.kafka_topic, api_response)
                    
                    # wait for 1 second to stream next message/s
                    time.sleep(1)

        except Exception as ex:
            print('Error connecting Meetup stream api.')