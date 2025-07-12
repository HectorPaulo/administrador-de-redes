"""
Configuración inicial y constantes del sistema
"""
import os
import sys

# --- CONFIGURACIÓN INICIAL ---
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Constantes del sistema
MAX_VLAN_ID = 4094
MIN_VLAN_ID = 2
DEFAULT_TIMEOUT = 30000  # milliseconds
DEFAULT_FILE_ENCODING = 'utf-8'

# Interfaces por defecto según el modo
INTERFACES_WAN = ["eth0/0/0", "eth0/1/0", "eth0/2/0", "eth0/3/0"]
INTERFACES_LAN = ["fa0/0", "fa0/1"]

# Configuración de red por defecto
DEFAULT_MASK_RANGES = {
    'wan': 30,
    'lan': 24,
    'management': 24
}

# Mensajes de error comunes
ERROR_MESSAGES = {
    'empty_field': "❌ Error: No puedes dejar este campo vacío.",
    'invalid_ip': "❌ Error: La dirección IP no es válida.",
    'invalid_mask': "❌ Error: La máscara de prefijo debe estar entre 1 y 30.",
    'invalid_number': "❌ Error: Debes introducir un número entero válido.",
    'invalid_vlan': "❌ Error: Las VLANs de usuario deben tener un ID de 2 o superior.",
    'duplicate_connection': "❌ Error: Ya existe una conexión definida con este router.",
    'self_connection': "❌ Error: No puedes conectar un router consigo mismo.",
    'invalid_filename': "❌ Error: El nombre del archivo contiene caracteres no válidos."
}

# Caracteres no válidos para nombres de archivo
INVALID_FILENAME_CHARS = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

# Configuración SSH por defecto
SSH_CONFIG = {
    'domain': 'cisco.com',
    'username': 'SLuis',
    'password': 'SLuis',
    'enable_secret': 'cisco',
    'ssh_version': 2,
    'rsa_key_size': 1024
}

# Configuración WLC por defecto
WLC_CONFIG = {
    'default_native_vlan': 4,
    'wlc_interface': 'g1/0/2',
    'switch_interfaces': ['g1/0/3', 'g1/0/4']
}
