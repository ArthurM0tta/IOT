import network
import time
import ubinascii
from umqtt.simple import MQTTClient
import gc

# 📡 Configurações WiFi
WIFI_SSID = "NET_2G422C8E"
WIFI_SENHA = "E2422C8E"

# 🌐 Configurações MQTT
MQTT_BROKER = "mqttengenharias.tech"
MQTT_USER = "656b8200"
PORTA = 1883
MQTT_TOPICO = "GRUPO2"

# 📄 Caminho do arquivo PDF já presente no NodeMCU
CAMINHO_PDF = "/exemplo.pdf"

def conecta_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_SENHA)
    while not wlan.isconnected():
        time.sleep(1)
        print("Conectando ao WiFi...")
    print("Conectado! IP:", wlan.ifconfig()[0])

def conecta_mqtt():
    cliente = MQTTClient(MQTT_USER, MQTT_BROKER, PORTA)
    cliente.connect()
    print("Conectado ao MQTT!")
    return cliente

def codifica_pdf_em_base64(caminho):
    try:
        with open(caminho, "rb") as f:
            dados = f.read()
        print("Arquivo lido:", len(dados), "bytes")
        base64_pdf = ubinascii.b2a_base64(dados).decode("utf-8").replace("\n", "")
        return base64_pdf
    except Exception as e:
        print("Erro ao ler PDF:", e)
        return None

def main():
    conecta_wifi()
    mqtt = conecta_mqtt()
    gc.collect()

    print("Lendo e codificando PDF...")
    base64_pdf = codifica_pdf_em_base64(CAMINHO_PDF)
    if base64_pdf:
        print("Enviando via MQTT...")
        try:
            mqtt.publish(MQTT_TOPICO, base64_pdf)
            print("Publicado com sucesso!")
        except Exception as e:
            print("Erro ao publicar:", e)
    else:
        print("Erro ao codificar PDF.")
    
    mqtt.disconnect()
    print("Finalizado.")

main()
