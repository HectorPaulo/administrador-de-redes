"""
Script de prueba para verificar el sistema de interfaces dinámicas
"""
import sys
import os

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from interface_manager import *

def test_interfaces():
    """Prueba las funciones de interfaces dinámicas"""
    
    print("🧪 PRUEBA DEL SISTEMA DE INTERFACES DINÁMICAS")
    print("=" * 70)
    
    # Probar interfaces WAN
    print("\n📡 INTERFACES WAN:")
    print("-" * 30)
    
    for modo in [1, 2]:  # 1=Simulación, 2=Físico
        modo_nombre = "Simulación" if modo == 1 else "Físico"
        print(f"\n🔧 Modo {modo_nombre}:")
        
        for router in [1, 2, 3, 4, 5]:
            for idx in range(3):
                try:
                    interfaz = get_wan_interface(router, idx, modo)
                    print(f"  R{router} WAN[{idx}]: {interfaz}")
                except ValueError as e:
                    print(f"  R{router} WAN[{idx}]: ❌ {e}")
    
    # Probar interfaces LAN
    print("\n🏠 INTERFACES LAN:")
    print("-" * 30)
    
    for modo in [1, 2]:
        modo_nombre = "Simulación" if modo == 1 else "Físico"
        print(f"\n🔧 Modo {modo_nombre}:")
        
        for router in [1, 2, 3, 4, 5]:
            for idx in range(2):
                try:
                    interfaz = get_lan_interface(router, idx, modo)
                    print(f"  R{router} LAN[{idx}]: {interfaz}")
                except ValueError as e:
                    print(f"  R{router} LAN[{idx}]: ❌ {e}")
    
    # Probar interfaces de switch
    print("\n🔌 INTERFACES SWITCH:")
    print("-" * 30)
    
    for modo in [1, 2]:
        modo_nombre = "Simulación" if modo == 1 else "Físico"
        print(f"\n🔧 Modo {modo_nombre}:")
        
        for switch in [1, 2, 3, 4, 5]:
            for idx in range(3):
                try:
                    interfaz = get_switch_trunk_interface(switch, idx, modo)
                    print(f"  SW{switch} TRUNK[{idx}]: {interfaz}")
                except ValueError as e:
                    print(f"  SW{switch} TRUNK[{idx}]: ❌ {e}")
    
    # Probar EtherChannel
    print("\n🔗 ETHERCHANNEL:")
    print("-" * 30)
    
    for modo in [1, 2]:
        modo_nombre = "Simulación" if modo == 1 else "Físico"
        print(f"\n🔧 Modo {modo_nombre}:")
        
        for router in [1, 2, 3, 4, 5]:
            try:
                port_channel = get_port_channel_interface(router, modo)
                eth_interfaces = get_etherchannel_interfaces(router, modo)
                print(f"  R{router} Port-Channel: {port_channel}")
                print(f"  R{router} EtherChannel: {eth_interfaces}")
            except ValueError as e:
                print(f"  R{router}: ❌ {e}")
    
    # Probar SWC3
    print("\n⚙️ INTERFACES SWC3:")
    print("-" * 30)
    
    for modo in [1, 2]:
        modo_nombre = "Simulación" if modo == 1 else "Físico"
        print(f"\n🔧 Modo {modo_nombre}:")
        
        for swc3 in [1, 2, 3, 4, 5]:
            try:
                hacia_router = get_swc3_interface_hacia_router(swc3, modo)
                hacia_switch = get_swc3_interface_hacia_switch(swc3, 0, modo)
                print(f"  SWC3-{swc3} → R{swc3}: {hacia_router}")
                print(f"  SWC3-{swc3} → SW: {hacia_switch}")
            except ValueError as e:
                print(f"  SWC3-{swc3}: ❌ {e}")
    
    print(f"\n✅ PRUEBA COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_interfaces()
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
