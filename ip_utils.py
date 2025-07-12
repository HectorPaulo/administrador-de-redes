"""
Utilidades para manejo de IPs y redes
"""
import ipaddress
from diagonal_manager import DiagonalManager

# Variable global para el manejador de diagonales
diagonal_manager = None

def inicializar_diagonal_manager(base_ip):
    """Inicializa el manejador de diagonales"""
    global diagonal_manager
    diagonal_manager = DiagonalManager(base_ip)

def calcular_rango_subred(base_ip, mascara, subredes_ocupadas, aleatorio=True):
    """Función modificada para usar el sistema de diagonales"""
    global diagonal_manager
    
    if diagonal_manager is None:
        diagonal_manager = DiagonalManager(base_ip)
    
    # Obtener el siguiente combo de la diagonal correspondiente
    red_combo = diagonal_manager.obtener_siguiente_combo(mascara)
    
    # Calcular el rango para compatibilidad con el código existente
    red_obj = ipaddress.IPv4Network(f"{red_combo}/{mascara}", strict=False)
    inicio_subred = int(red_obj.network_address)
    fin_subred = int(red_obj.broadcast_address)
    
    # Agregar a subredes ocupadas para compatibilidad
    subredes_ocupadas.append((inicio_subred, fin_subred))
    
    return (str(red_obj.network_address), str(red_obj.broadcast_address))

def obtener_ip_usable(red, mascara, offset):
    """Obtiene IP usable de una red con offset específico"""
    try:
        red_obj = ipaddress.IPv4Network(f"{red}/{mascara}", strict=False)
        return str(list(red_obj.hosts())[offset])
    except IndexError:
        return None

def convertir_mascara_prefijo_a_decimal(mascara_prefijo):
    """Convierte máscara de prefijo a decimal"""
    return str(ipaddress.IPv4Network(f"0.0.0.0/{mascara_prefijo}").netmask)

def obtener_direccion_de_red(ip, mascara_prefijo):
    """Obtiene dirección de red de una IP con máscara"""
    return str(ipaddress.IPv4Network(f"{ip}/{mascara_prefijo}", strict=False).network_address)
