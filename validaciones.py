"""
Funciones de validación de entrada
"""
import ipaddress
from config import ERROR_MESSAGES, INVALID_FILENAME_CHARS

def validar_entrada(mensaje, tipo_entrada="texto", opciones=None):
    """Valida entrada del usuario según el tipo especificado"""
    while True:
        entrada = input(mensaje).strip()
        if not entrada:
            print(ERROR_MESSAGES['empty_field'])
            continue
            
        if opciones and entrada.lower() not in opciones:
            print(f"❌ Error: La opción no es válida. Elige entre: {', '.join(opciones)}")
            continue
            
        if tipo_entrada == "numero":
            try:
                return int(entrada)
            except ValueError:
                print(ERROR_MESSAGES['invalid_number'])
        elif tipo_entrada == "numero_positivo":
            try:
                numero = int(entrada)
                if numero <= 0:
                    print("❌ Error: El número debe ser mayor que 0.")
                    continue
                return numero
            except ValueError:
                print(ERROR_MESSAGES['invalid_number'])
        elif tipo_entrada == "si_no":
            if entrada.lower() in ['s', 'si', 'sí']:
                return True
            elif entrada.lower() in ['n', 'no']:
                return False
            else:
                print("❌ Error: Responde con 's' para sí o 'n' para no.")
        elif tipo_entrada == "ip":
            try:
                ipaddress.IPv4Address(entrada)
                return entrada
            except ipaddress.AddressValueError:
                print(f"❌ Error: '{entrada}' no es una dirección IP válida.")
        elif tipo_entrada == "mascara":
            try:
                mascara = int(entrada)
                if not (1 <= mascara <= 30):
                    print(ERROR_MESSAGES['invalid_mask'])
                    continue
                return mascara
            except ValueError:
                print("❌ Error: La máscara debe ser un número entero.")
        elif tipo_entrada == "cidr":
            try:
                ipaddress.IPv4Network(entrada, strict=False)
                return entrada
            except ValueError:
                print(f"❌ Error: '{entrada}' no es una red en formato CIDR válida.")
        else:
            return entrada

def validar_nombre_archivo(mensaje):
    """Valida nombre de archivo para evitar caracteres no válidos"""
    while True:
        nombre = validar_entrada(mensaje)
        if any(char in nombre for char in INVALID_FILENAME_CHARS):
            print(f"❌ Error: El nombre del archivo contiene caracteres no válidos ({' '.join(INVALID_FILENAME_CHARS)}).")
        else:
            return nombre

def validar_vlan_id(mensaje, vlans_disponibles):
    """Valida ID de VLAN disponible"""
    while True:
        vlan_id = validar_entrada(mensaje, "numero_positivo")
        if vlan_id < 2:
            print(ERROR_MESSAGES['invalid_vlan'])
            continue
        vlan_ids_disponibles = [v[0] for v in vlans_disponibles]
        if vlan_id not in vlan_ids_disponibles:
            print(f"❌ Error: La VLAN {vlan_id} no está en la lista de VLANs configuradas. Disponibles: {vlan_ids_disponibles}")
            continue
        return vlan_id

def validar_router_destino(mensaje, router_actual, num_routers, conexiones_actuales):
    """Valida router destino para conexiones"""
    while True:
        hacia_router = validar_entrada(mensaje, "numero_positivo")
        if hacia_router == router_actual:
            print(ERROR_MESSAGES['self_connection'])
            continue
        if hacia_router > num_routers:
            print(f"❌ Error: El número del router no puede ser mayor que {num_routers}.")
            continue
        if hacia_router in [int(r) for r in conexiones_actuales]:
            print(ERROR_MESSAGES['duplicate_connection'])
            continue
        return hacia_router
