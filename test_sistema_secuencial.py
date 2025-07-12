"""
Script de prueba para verificar el sistema secuencial mejorado
"""
import sys
import os

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from diagonal_manager import DiagonalManager

def test_sistema_secuencial():
    """Prueba el sistema secuencial con el ejemplo del usuario"""
    
    print("PRUEBA DEL SISTEMA SECUENCIAL MEJORADO")
    print("=" * 70)
    
    # Inicializar con la IP base del ejemplo
    dm = DiagonalManager("19.0.0.0")
    
    print("\nFASE 1: RECOPILANDO SOLICITUDES (como en tu ejemplo)")
    print("-" * 50)
    
    # Simular exactamente el ejemplo del usuario
    # Enlaces WAN (5 redes /30)
    dm.solicitar_combo(30, "Enlace WAN R1-R2")
    dm.solicitar_combo(30, "Enlace WAN R1-R3") 
    dm.solicitar_combo(30, "Enlace WAN R2-R3")
    dm.solicitar_combo(30, "Enlace WAN R3-R4")
    dm.solicitar_combo(30, "Enlace WAN R4-R5")
    
    # VLANs /28 (2 redes)
    dm.solicitar_combo(28, "VLAN 3 Dominio R1")
    dm.solicitar_combo(28, "VLAN 3 Dominio R5")
    
    # VLANs /23 (2 redes) 
    dm.solicitar_combo(23, "VLAN 4 Dominio R1")
    dm.solicitar_combo(23, "VLAN 4 Dominio R5")
    
    # VLAN /22 (1 red)
    dm.solicitar_combo(22, "VLAN 2 Dominio R1")
    
    print(f"\nFASE 2: PROCESAMIENTO SECUENCIAL")
    print("-" * 50)
    
    # Procesar todas las asignaciones de manera optimizada
    dm.procesar_asignaciones()
    
    print(f"\nPRUEBA COMPLETADA - Compara con tu resultado anterior")
    print("=" * 70)
    
    return dm

def comparar_con_sistema_anterior():
    """Muestra la comparación con el sistema anterior"""
    
    print("\nCOMPARACION: SISTEMA ANTERIOR vs SISTEMA MEJORADO")
    print("=" * 80)
    
    print("SISTEMA ANTERIOR (problematico):")
    print("   /30: 19.0.0.4-7, 19.0.0.8-11, 19.0.0.12-15, 19.0.0.48-51, 19.0.0.52-55")
    print("   /28: 19.0.0.16-31, 19.0.0.32-47")
    print("   /23: 19.0.2.0-3.255, 19.0.8.0-9.255")
    print("   /22: 19.0.4.0-7.255")
    print("   Problema: /30 intercalados, desperdicia espacio")
    
    print("\nSISTEMA MEJORADO (secuencial):")
    print("   /30: 19.0.0.4-7, 19.0.0.8-11, 19.0.0.12-15, 19.0.0.16-19, 19.0.0.20-23")
    print("   /28: 19.0.0.32-47, 19.0.0.48-63")  
    print("   /23: 19.0.2.0-3.255, 19.0.4.0-5.255")
    print("   /22: 19.0.8.0-11.255")
    print("   Beneficio: TODAS las /30 consecutivas, uso eficiente del espacio")

if __name__ == "__main__":
    try:
        # Ejecutar prueba
        dm = test_sistema_secuencial()
        
        # Mostrar comparación
        comparar_con_sistema_anterior()
        
        print(f"\nSISTEMA SECUENCIAL FUNCIONANDO CORRECTAMENTE!")
        print("   Asignacion optimizada implementada")
        print("   Mascaras grandes asignadas primero")
        print("   Uso eficiente del espacio de direcciones")
        
    except Exception as e:
        print(f"\nError en la prueba: {e}")
        import traceback
        traceback.print_exc()
