import pika
import json
import os
from typing import Dict, Any
from datetime import datetime, timezone
import pybreaker

# Circuit breaker listener for logging state changes
class CircuitBreakerListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        print(f"Circuit Breaker state changed from {old_state.name} to {new_state.name}")

# Initialize circuit breaker with appropriate thresholds
rabbitmq_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=5,  # Open circuit after 5 consecutive failures
    reset_timeout=60,  # Try to recover after 60 seconds
    listeners=[CircuitBreakerListener()],
    name="RabbitMQ_Publisher"
)

class RabbitMQPublisher:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        self.connection = None
        self.channel = None
        
    @rabbitmq_circuit_breaker
    def connect(self):
        if not self.rabbitmq_url:
            print("WARNING: RABBITMQ_URL not set; skipping RabbitMQ connection")
            return False

        params = pika.URLParameters(self.rabbitmq_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange='user_events', exchange_type='fanout')
        print("Connected to RabbitMQ")
        return True

    def close(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print("RabbitMQ connection closed")
        except Exception as e:
            print(f"ERROR: Failed to close RabbitMQ connection: {e}")
            
    @rabbitmq_circuit_breaker
    def _publish_with_circuit_breaker(self, event_type: str, message: Dict[str, Any]) -> bool:
        """Internal method wrapped with circuit breaker for actual publishing."""
        if not self.channel or self.connection.is_closed:
            if not self.connect():
                raise Exception("Failed to connect to RabbitMQ")
        
        # Publish message to queue
        self.channel.basic_publish(
            exchange='',
            routing_key='user_events_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'                  
            ))

        print(f"Published event: {event_type}")
        return True

    def publish_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Public method that handles circuit breaker exceptions gracefully."""
        try:
            message = {
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            }
            
            return self._publish_with_circuit_breaker(event_type, message)

        except pybreaker.CircuitBreakerError:
            print(f"WARNING: Circuit breaker is OPEN - skipping event {event_type}")
            return False
        except Exception as e:
            print(f"ERROR: Failed to publish event {event_type}: {e}")
            # Attempt to reconnect once
            try:
                self.close()
                if self.connect():
                    # Retry once after reconnection
                    try:
                        return self._publish_with_circuit_breaker(event_type, message)
                    except:
                        pass
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

    # publish user logout
    def publish_user_logout(self, user_id: str, username: str):
        return self.publish_event("user_logout", {
            "user_id": user_id,
            "username": username
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