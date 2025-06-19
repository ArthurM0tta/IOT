import network
import urequests
import ujson
import time

# 📡 Configurações WiFi
SSID = "Visitantes"
PASSWORD = "Wy@2023.2"


# Token do dispositivo no ThingsBoard
ACCESS_TOKEN = 'Yb5z4jh2cB1cHtoe0i4R'

# Endpoint HTTP do ThingsBoard
url = 'https://thingsboard.cloud/api/v1/{}/telemetry'.format(ACCESS_TOKEN)
headers = {'Content-Type': 'application/json'}

# 📄 URL do arquivo PDF
URL_PDF = "https://github.com/ArthurM0tta/IOT"  # Link para o arquivo PDF


def conecta_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
        print("Conectando ao WiFi...")
    print("Conectado! IP:", wlan.ifconfig()[0])



def main():
    conecta_wifi()
    payload = {
        'pdf-file': URL_PDF
    }
    try:
        response = urequests.post(url, headers=headers, data=ujson.dumps(payload))
        print('Enviado:', payload, '| Status:', response.status_code)
        response.close()
        if response.status_code == 200 or response.status_code == 201 or response.status_code == 204:
            print("✅ Envio concluído com sucesso. Encerrando.")
            return  # Finaliza o programa
    except Exception as e:
        print('❌ Erro ao enviar:', e)

main()