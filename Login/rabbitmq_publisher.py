import pika
import json
import os
from typing import Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RabbitMQPublisher:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        self.connection = None
        self.channel = None
        
    def connect(self):
        try:
            if not self.rabbitmq_url:
                logger.warning("RABBITMQ_URL not set; skipping RabbitMQ connection")
                return False

            params = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

            self.channel.exchange_declare(exchange='user_events', exchange_type='fanout')
            logger.info("Connected to RabbitMQ")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            # Do not raise here to allow the application to start without RabbitMQ
            return False

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
                "timestamp": datetime.utcnow().isoformat(),
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

            logger.info(f"Published event: {event_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            # Attempt to reconnect once
            try:
                self.close()
                self.connect()
            except:
                pass
            return False

    # publish user registration event#
    def publish_user_registration(self, user_id: str, username:str, email:str):
        return self.publish_event("user_registration", {
            "user_id": user_id,
            "username": username,
            "email": email
        })

    # publish user login
    def publish_user_login(self, user_id: str, username:str):
        return self.publish_event("user_login", {
            "user_id": user_id,
            "username": username
        })

    # publish user update
    def publish_user_update(self, user_id: str, username:str, updated_fields: Dict[str, Any]):
        return self.publish_event("user_update", {
            "user_id": user_id,
            "username": username,
            "updated_fields": updated_fields
        })
    
    # publish user deletion
    def publish_user_deletion(self, user_id: str, username:str):
        return self.publish_event("user_deletion", {
            "user_id": user_id,
            "username": username
        })
    

_publisher = RabbitMQPublisher()

def get_rabbitmq_publisher() -> RabbitMQPublisher:
    global _publisher
    if _publisher is None:
        _publisher = RabbitMQPublisher()
    return _publisher