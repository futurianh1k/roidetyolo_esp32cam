"""
간단한 MQTT 브로커 테스트
mosquitto-go-auth를 대체하는 간단한 브로커
"""
import asyncio
import logging

try:
    from hbmqtt.broker import Broker
    
    config = {
        'listeners': {
            'default': {
                'type': 'tcp',
                'bind': '0.0.0.0:1883',
            }
        },
        'auth': {
            'allow-anonymous': True,
        }
    }
    
    broker = Broker(config)
    
    @asyncio.coroutine
    def start_broker():
        yield from broker.start()
        print("=" * 60)
        print("MQTT 브로커 시작됨: 0.0.0.0:1883")
        print("Ctrl+C로 종료")
        print("=" * 60)
    
    if __name__ == '__main__':
        asyncio.get_event_loop().run_until_complete(start_broker())
        asyncio.get_event_loop().run_forever()

except ImportError:
    print("hbmqtt가 설치되지 않았습니다.")
    print("설치: pip install hbmqtt")
    print("\n또는 Mosquitto를 사용하세요:")
    print("https://mosquitto.org/download/")

