"""
Inicialización y configuración inicial de sesiones - Sistema secuencial
"""
from validaciones import validar_entrada, validar_nombre_archivo
from network_config import configurar_vlans, configurar_redes_entre_routers, procesar_todas_las_asignaciones
from ip_utils import inicializar_diagonal_manager

def iniciar_nueva_sesion():
    """Inicia una nueva sesión de configuración con sistema secuencial"""
    print("\n--- INICIANDO NUEVA SESION DE CONFIGURACION (SISTEMA SECUENCIAL) ---")
    
    # Datos básicos de la sesión
    nombre_sesion = validar_nombre_archivo("Asigna un nombre a esta sesion (para guardarla): ")
    modo_config = validar_entrada("Selecciona el tipo (1-Simulacion, 2-Fisico): ", "numero", ['1', '2'])
    base_ip = validar_entrada("IP base para las subredes de usuario (ej: 19.0.0.0): ", "ip")
    
    # Inicializar el manejador de diagonales secuencial
    inicializar_diagonal_manager(base_ip)
    
    # Configuración de red de gestión
    print("\n--- Configuracion de Red de Gestion para Switches ---")
    mgmt_base_ip = validar_entrada("Red base de gestion SSH (ej: 192.168.100.0): ", "ip")
    mgmt_prefijo_combo = validar_entrada("Prefijo para cada combo de gestion SSH (ej: 24 para /24): ", "mascara")
    
    # Configuración de VLANs y routers
    num_vlans = validar_entrada("\nNumero total de VLANs a crear (de 2 en adelante): ", "numero_positivo")
    num_routers = validar_entrada("Numero total de routers en la topologia: ", "numero_positivo")
    
    print(f"\nINICIANDO SISTEMA SECUENCIAL DE ASIGNACION")
    print("=" * 70)
    print("OK Primero recopilaremos TODAS las solicitudes")
    print("OK Luego las procesaremos en orden optimizado")
    print("OK Mascaras grandes (/30) antes que pequenas (/24)")
    
    # FASE 1: RECOPILAR TODAS LAS SOLICITUDES
    print(f"\nFASE 1: RECOPILACION DE SOLICITUDES")
    print("=" * 50)
    
    # Configurar VLANs (solo recopila solicitudes)
    subredes_ocupadas = []
    vlans_con_combos_temp, vlans_nombres = configurar_vlans(num_vlans, base_ip, subredes_ocupadas)
    
    # Configurar SWC3
    usar_swc3 = validar_entrada("\n¿Deseas usar Switch Capa 3 en esta topologia? (s/n): ", "si_no")
    num_swc3_enlaces = 0
    usar_wlc = False
    if usar_swc3:
        num_swc3_enlaces = validar_entrada("¿Cuantos routers tendran un SWC3 asociado?: ", "numero")
        usar_wlc = validar_entrada("¿Algun SWC3 tendra WLC asociado? (s/n): ", "si_no")
    
    # Configurar conexiones WAN (solo recopila solicitudes)
    num_conexiones_wan = validar_entrada("¿Cuantas conexiones WAN entre routers necesitas en total?: ", "numero_positivo")
    
    # Calcular redes P2P necesarias
    total_redes_p2p = num_conexiones_wan + num_swc3_enlaces
    redes_p2p_temp = configurar_redes_entre_routers(total_redes_p2p, base_ip, subredes_ocupadas, aleatorio=False)
    
    # FASE 2: PROCESAR TODAS LAS ASIGNACIONES DE MANERA SECUENCIAL
    print(f"\nFASE 2: PROCESAMIENTO SECUENCIAL OPTIMIZADO")
    print("=" * 60)
    
    vlans_con_combos, redes_p2p_disponibles = procesar_todas_las_asignaciones()
    
    print(f"\nSISTEMA SECUENCIAL COMPLETADO")
    print("=" * 50)
    print(f"Resultados finales:")
    print(f"   🏷️ VLANs configuradas: {len(vlans_con_combos)}")
    print(f"   🔗 Redes P2P disponibles: {len(redes_p2p_disponibles)}")
    
    # Crear estado inicial
    estado = {
        "nombre_sesion": nombre_sesion,
        "ultimo_paso_completado": 0,
        "datos_iniciales": {
            "modo_config": modo_config,
            "base_ip": base_ip,
            "mgmt_base_ip": mgmt_base_ip,
            "mgmt_prefijo_combo": mgmt_prefijo_combo,
            "num_vlans": num_vlans,
            "num_routers": num_routers,
            "usar_swc3": usar_swc3,
            "num_swc3_enlaces": num_swc3_enlaces,
            "usar_wlc": usar_wlc
        },
        "config_calculada": {
            "vlans_con_combos": vlans_con_combos,
            "vlans_nombres": vlans_nombres,
            "redes_p2p_disponibles": redes_p2p_disponibles,
            "subredes_ocupadas": subredes_ocupadas
        },
        "progreso_routers": {
            "vlans_por_router": {str(i): {} for i in range(1, num_routers + 1)},
            "conexiones_por_router": {str(i): {} for i in range(1, num_routers + 1)},
            "l2_config_por_router": {str(i): {} for i in range(1, num_routers + 1)},
            "todas_las_conexiones": {},
            "routers_con_swc3": {},
            "config_swc3": {},
            "config_wlc": {},
            "topologia_switches": {}
        },
        "recursos_usados": {
            "redes": []
        }
    }
    
    return estado

def verificar_compatibilidad_sesion(estado):
    """Verifica y actualiza compatibilidad de sesiones antiguas"""
    config_calculada = estado["config_calculada"]
    progreso = estado["progreso_routers"]
    
    # Compatibilidad con sesiones antiguas: agregar vlans_nombres si no existe
    if "vlans_nombres" not in config_calculada:
        from vlan_utils import numero_a_letras
        config_calculada["vlans_nombres"] = {}
        
        # Generar nombres automáticos para VLANs existentes
        for vlan_data in config_calculada.get("vlans_con_combos", []):
            vlan_id = vlan_data[0]
            config_calculada["vlans_nombres"][vlan_id] = numero_a_letras(vlan_id)
        
        print("Sesion antigua detectada. Generados nombres automaticos para VLANs existentes.")
    
    # Compatibilidad: convertir conexiones de formato antiguo a nuevo
    from ip_utils import obtener_ip_usable
    conexiones_convertidas = False
    
    for conn_key, conn_data in progreso["todas_las_conexiones"].items():
        if isinstance(conn_data, list):
            # Formato antiguo: [red, mascara]
            red, mascara = conn_data
            r1, r2 = eval(conn_key)
            ip_r1 = obtener_ip_usable(red, mascara, 0)
            ip_r2 = obtener_ip_usable(red, mascara, -1)
            
            # Convertir a nuevo formato
            progreso["todas_las_conexiones"][conn_key] = {
                'red': red,
                'mascara': mascara,
                'r1': min(r1, r2),
                'r2': max(r1, r2),
                'ip_r1': ip_r1,
                'ip_r2': ip_r2,
                f'ip_r{r1}': ip_r1 if r1 < r2 else ip_r2,
                f'ip_r{r2}': ip_r2 if r1 < r2 else ip_r1
            }
            conexiones_convertidas = True
    
    if conexiones_convertidas:
        print("Conexiones convertidas al nuevo formato con IPs especificas.")
    
    return estado, conexiones_convertidas