import pika
import json
import os
from typing import Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RabbitMQPublisher::
    def __init__(self, rabbitmq_url: str = None):):
        self.rabbitmq_url = rabbitmq_url or os.getenv(
            "RABBITMQ_URL",
            "amqp://guest:guest@localhost:5672/"
        )
        self.connection = None
        self.channel = None
        
    def connect(self):
        try:
            params = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            self.channel.exchange_declare(exchange='user_events', exchange_type='fanout')
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def close(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Failed to close RabbitMQ connection: {e}")
            
    def publish_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        try:
            if not self.channel or self.connection.is_closed:
                if not self.connect():
                    return False
            
            message = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),,
                "data": data
            }

            #pulish message to queue 
            self.channel.basic_publish(
                exchange='',
                routing_key='user_events',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,# make message persistent
                    content_type='application/json'                  
                    ))