import network
import time
from machine import Pin, I2C
import urequests

# ===== CONFIGURAÇÕES =====
SSID = "Visitantes"
PASSWORD = "Wy@2023.2"

ADAFRUIT_IO_USERNAME = "Arthur_M0tta"
ADAFRUIT_IO_KEY = "aio_MQnE96sItt37B9dVCeUezhEl2GyZ"

FEED_PRESSAO = "pressao"
FEED_TEMP = "temp"
FEED_ALT = "alt"  # novo feed para altitude

BASE_URL = "https://io.adafruit.com/api/v2"

# ===== FUNÇÃO PARA CONECTAR AO WIFI =====
def conecta_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando ao WiFi...")
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
    print("Conectado! IP:", wlan.ifconfig()[0])
    return wlan

# ===== DRIVER SIMPLES BMP280 =====
class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        self.dig_T1 = self._read16(0x88)
        self.dig_T2 = self._read_s16(0x8A)
        self.dig_T3 = self._read_s16(0x8C)
        self.dig_P1 = self._read16(0x8E)
        self.dig_P2 = self._read_s16(0x90)
        self.dig_P3 = self._read_s16(0x92)
        self.dig_P4 = self._read_s16(0x94)
        self.dig_P5 = self._read_s16(0x96)
        self.dig_P6 = self._read_s16(0x98)
        self.dig_P7 = self._read_s16(0x9A)
        self.dig_P8 = self._read_s16(0x9C)
        self.dig_P9 = self._read_s16(0x9E)
        self.t_fine = 0
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x27')
        self.i2c.writeto_mem(self.addr, 0xF5, b'\xA0')

    def _read16(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return data[0] | (data[1] << 8)

    def _read_s16(self, reg):
        result = self._read16(reg)
        if result > 32767:
            result -= 65536
        return result

    def read_raw(self):
        data = self.i2c.readfrom_mem(self.addr, 0xF7, 6)
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return temp_raw, pres_raw

    def compensate_T(self, adc_T):
        var1 = (((adc_T >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_T >> 4) - self.dig_T1) * ((adc_T >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        T = (self.t_fine * 5 + 128) >> 8
        return T / 100

    def compensate_P(self, adc_P):
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33

        if var1 == 0:
            return 0

        p = 1048576 - adc_P
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
        return p / 25600

    def read(self):
        temp_raw, pres_raw = self.read_raw()
        temp = self.compensate_T(temp_raw)
        pres = self.compensate_P(pres_raw)
        return temp, pres

# ===== CALCULA ALTITUDE (m) COM PRESSÃO AO NÍVEL DO MAR LOCAL =====
def calcular_altitude(p_hpa, t_celsius, p0_hpa=1022):
    # Ajuste da pressão ao nível do mar para Salvador (Pituaçu)
    altitude = (( (p0_hpa / p_hpa) ** (1/5.257) ) - 1) * (t_celsius + 273.15) / 0.0065
    return altitude

# ===== FUNÇÃO PARA ENVIAR DADOS =====
def enviar_dado(feed_key, valor):
    url = f"{BASE_URL}/{ADAFRUIT_IO_USERNAME}/feeds/{feed_key}/data"
    headers = {
        "X-AIO-Key": ADAFRUIT_IO_KEY,
        "Content-Type": "application/json"
    }
    data = '{{"value": "{}"}}'.format(valor)
    try:
        response = urequests.post(url, data=data, headers=headers)
        response.close()
        if response.status_code in (200, 201):
            print(f"✅ Enviado {valor} para {feed_key}")
            return True
        else:
            print(f"❌ Erro HTTP {response.status_code} ao enviar {feed_key}")
            return False
    except Exception as e:
        print(f"❌ Erro ao enviar dados: {e}")
        return False

# ===== PROGRAMA PRINCIPAL =====
def main():
    conecta_wifi(SSID, PASSWORD)

    i2c = I2C(scl=Pin(5), sda=Pin(4))
    bmp = BMP280(i2c)

    leituras = 0
    max_leituras = 6  # 2 minutos / 20 segundos = 6 leituras

    while leituras < max_leituras:
        temp, pres = bmp.read()
        print("Temperatura: {:.2f} °C".format(temp))
        print("Pressão: {:.2f} hPa".format(pres))

        altitude = calcular_altitude(pres, temp)
        print("Altitude aproximada: {:.2f} m".format(altitude))

        enviar_dado(FEED_TEMP, temp)
        enviar_dado(FEED_PRESSAO, pres)
        enviar_dado(FEED_ALT, altitude)

        leituras += 1
        if leituras < max_leituras:
            time.sleep(20)

    print("✅ Simulação finalizada após 2 minutos.")

if __name__ == "__main__":
    main()


