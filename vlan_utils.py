"""
Conversión de números a letras para nombres de VLAN
"""

def numero_a_letras(numero):
    """Convierte un número a su equivalente en letras para nombres de VLAN"""
    numeros_basicos = {
        1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 
        6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez", 
        11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince", 
        16: "dieciseis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve", 
        20: "veinte", 21: "veintiuno", 22: "veintidos", 23: "veintitres", 
        24: "veinticuatro", 25: "veinticinco", 26: "veintiseis", 
        27: "veintisiete", 28: "veintiocho", 29: "veintinueve", 
        30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta", 
        70: "setenta", 80: "ochenta", 90: "noventa", 100: "cien", 
        200: "doscientos", 300: "trescientos", 400: "cuatrocientos", 
        500: "quinientos"
    }
    
    if numero in numeros_basicos:
        return numeros_basicos[numero]
    elif 31 <= numero <= 99:
        decenas = (numero // 10) * 10
        unidades = numero % 10
        return f"{numeros_basicos[decenas]}_{numeros_basicos[unidades]}"
    elif 101 <= numero <= 999:
        if numero < 200:
            return f"ciento_{numero_a_letras(numero - 100)}"
        else:
            centenas = (numero // 100) * 100
            resto = numero % 100
            if resto == 0:
                return numeros_basicos[centenas]
            else:
                return f"{numeros_basicos[centenas]}_{numero_a_letras(resto)}"
    else:
        return f"vlan{numero}"  # Fallback para números muy grandes

def validar_vlan_personalizada():
    """Valida y obtiene ID y nombre personalizado de VLAN"""
    from validaciones import validar_entrada
    
    while True:
        vlan_id = validar_entrada("🏷️ ¿ID de VLAN? (ej: 20, 100): ", "numero_positivo")
        if vlan_id < 2:
            print("❌ Error: Las VLANs de usuario deben tener un ID de 2 o superior.")
            continue
        if vlan_id > 4094:
            print("❌ Error: El ID de VLAN debe ser menor o igual a 4094.")
            continue
        break
    
    # Generar nombre automático
    nombre_auto = numero_a_letras(vlan_id)
    
    # Preguntar si quiere personalizar el nombre
    nombre_personalizado = input(f"📝 ¿Nombre personalizado? (Enter para usar '{nombre_auto}'): ").strip()
    
    if not nombre_personalizado:
        nombre_final = nombre_auto
        print(f"✅ Usando nombre automático: '{nombre_auto}'")
    else:
        # Validar que el nombre no tenga caracteres especiales
        caracteres_invalidos = [' ', '<', '>', ':', '"', '/', '\\', '|', '?', '*', '\t', '\n']
        if any(char in nombre_personalizado for char in caracteres_invalidos):
            print(f"⚠️ Nombre contiene caracteres no válidos. Usando nombre automático: '{nombre_auto}'")
            nombre_final = nombre_auto
        else:
            nombre_final = nombre_personalizado
            print(f"✅ Usando nombre personalizado: '{nombre_final}'")
    
    return vlan_id, nombre_final
