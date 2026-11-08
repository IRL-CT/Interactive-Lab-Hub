"""Paho 1.6/2.x compatible connection; subscriptions restored on reconnect."""
import json
import logging
import threading
import uuid
import paho.mqtt.client as mqtt
import config


class MQTTConnection:
    def __init__(self, name, subscriptions=(), handler=None):
        kwargs = {'client_id': f'pet-{name}-{uuid.uuid4().hex[:12]}'}
        if hasattr(mqtt, 'CallbackAPIVersion'):
            kwargs['callback_api_version'] = mqtt.CallbackAPIVersion.VERSION1
        self.client = mqtt.Client(**kwargs)
        self.connected = threading.Event()
        self.subscriptions = subscriptions
        self.handler = handler
        self.client.on_connect = self._connect
        self.client.on_disconnect = self._disconnect
        self.client.on_message = self._message
        self.client.on_connect_fail = lambda c, u: logging.error('Broker unavailable; retrying automatically')
        self.client.reconnect_delay_set(1, 10)
        self.client.max_queued_messages_set(100)
        if config.USERNAME:
            self.client.username_pw_set(config.USERNAME, config.PASSWORD)
        if config.TLS:
            self.client.tls_set()

    def _connect(self, client, userdata, flags, rc, properties=None):
        if rc:
            logging.error('MQTT connection rejected (%s); check credentials', rc)
            return
        for topic in self.subscriptions:
            client.subscribe(config.PREFIX + '/' + topic, qos=1)
        self.connected.set()
        logging.info('MQTT connected to %s:%s', config.BROKER, config.PORT)

    def _disconnect(self, client, userdata, rc, properties=None):
        self.connected.clear()
        logging.warning('MQTT disconnected (%s); automatic reconnect enabled', rc)

    def _message(self, client, userdata, message):
        if self.handler:
            try:
                self.handler(message)
            except Exception:
                logging.exception('Rejected message / callback failure')

    def start(self):
        self.client.connect_async(config.BROKER, config.PORT, keepalive=15)
        self.client.loop_start()

    def publish(self, suffix, payload, retain=False, wait=False):
        if not self.connected.is_set():
            raise ConnectionError('MQTT disconnected; action not sent. Retry after reconnect.')
        info = self.client.publish(config.PREFIX + '/' + suffix,
                                   json.dumps(payload, allow_nan=False), qos=1, retain=retain)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(f'MQTT publish failed: {info.rc}')
        if wait:
            info.wait_for_publish(timeout=5)
            if not info.is_published():
                raise TimeoutError('Broker acknowledgement timed out; delivery uncertain')
        return info

    def close(self):
        self.client.disconnect()
        self.client.loop_stop()
