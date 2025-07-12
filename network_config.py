"""
Configuración de redes y VLANs - Sistema secuencial mejorado
"""
import ipaddress
from ip_utils import obtener_direccion_de_red
from vlan_utils import validar_vlan_personalizada
from validaciones import validar_entrada

def configurar_redes_entre_routers(num_redes, base_ip, subredes_ocupadas, aleatorio):
    """
    Configura redes punto a punto entre routers usando sistema secuencial.
    Fase 1: Solo recopila las solicitudes de redes P2P
    """
    from ip_utils import diagonal_manager
    
    print(f"\nRECOPILANDO {num_redes} SOLICITUDES DE REDES P2P (/30)")
    print("=" * 60)
    
    solicitudes_p2p = []
    for i in range(num_redes):
        solicitud_id = diagonal_manager.solicitar_combo(30, f"Enlace WAN P2P-{i+1}")
        solicitudes_p2p.append(solicitud_id)
    
    # Guardar las solicitudes para procesamiento posterior
    if not hasattr(diagonal_manager, 'solicitudes_p2p_guardadas'):
        diagonal_manager.solicitudes_p2p_guardadas = []
    diagonal_manager.solicitudes_p2p_guardadas.extend(solicitudes_p2p)
    
    print(f"OK {num_redes} solicitudes P2P registradas para procesamiento")
    
    # Devolver lista vacía por ahora - se procesarán todas juntas después
    return []

def configurar_vlans(num_vlans, base_ip, subredes_ocupadas):
    """
    Configura VLANs con sus subredes usando sistema secuencial.
    Fase 1: Solo recopila todas las solicitudes de VLANs
    """
    from ip_utils import diagonal_manager
    
    print(f"\nRECOPILANDO SOLICITUDES PARA {num_vlans} VLANs")
    print("=" * 60)
    
    vlans_info = []  # Información temporal de VLANs
    vlans_nombres = {}
    
    for i in range(num_vlans):
        print(f"\n--- Configurando VLAN {i+1} de {num_vlans} ---")
        
        # Obtener ID y nombre personalizado
        while True:
            vlan_id, vlan_nombre = validar_vlan_personalizada()
            
            # Verificar que no se repita el ID
            if vlan_id in vlans_nombres:
                print(f"❌ Error: Ya existe una VLAN con ID {vlan_id}. Intenta con otro número.")
                continue
            break
        
        # Guardar el nombre de la VLAN
        vlans_nombres[vlan_id] = vlan_nombre
        
        print(f"\n--- Configurando subredes para VLAN {vlan_id} ({vlan_nombre}) ---")
        mascara_vlan = validar_entrada(f'Introduce la máscara de prefijo para la VLAN {vlan_id} (ej: 24): ', "mascara")
        num_combos = validar_entrada(f'¿Cuántas subredes (combos) necesitas para la VLAN {vlan_id}?: ', "numero_positivo")
        
        # Recopilar solicitudes de combos para esta VLAN
        solicitudes_combos = []
        for j in range(num_combos):
            descripcion = f"VLAN {vlan_id} Combo-{j+1}"
            solicitud_id = diagonal_manager.solicitar_combo(mascara_vlan, descripcion)
            solicitudes_combos.append(solicitud_id)
        
        vlans_info.append((vlan_id, vlan_nombre, mascara_vlan, solicitudes_combos))
        print(f"OK VLAN {vlan_id} ({vlan_nombre}): {num_combos} combos /{mascara_vlan} registrados")
    
    # Guardar info para procesamiento posterior
    diagonal_manager.vlans_info_guardada = vlans_info
    
    print(f"\nOK Recopilacion completada: {len(vlans_info)} VLANs configuradas")
    print("⏳ Las asignaciones se procesarán al finalizar la configuración...")
    
    # Devolver formato vacío por ahora - se procesará después
    return [], vlans_nombres

def procesar_todas_las_asignaciones():
    """
    Procesa todas las asignaciones recopiladas de manera secuencial optimizada.
    Esta función debe llamarse después de recopilar TODAS las solicitudes.
    """
    from ip_utils import diagonal_manager
    
    print(f"\nINICIANDO PROCESAMIENTO SECUENCIAL DE TODAS LAS ASIGNACIONES")
    print("=" * 80)
    
    # Verificar que haya solicitudes pendientes
    if not diagonal_manager.solicitudes_pendientes:
        print("⚠️ No hay solicitudes pendientes para procesar")
        return [], []
    
    # Ejecutar el procesamiento secuencial
    diagonal_manager.procesar_asignaciones()
    
    # Convertir resultados al formato esperado por el código existente
    vlans_con_combos = []
    redes_p2p_disponibles = []
    
    # Procesar VLANs si existen
    if hasattr(diagonal_manager, 'vlans_info_guardada'):
        print(f"\nCONVIRTIENDO RESULTADOS DE VLANs AL FORMATO REQUERIDO:")
        
        for vlan_id, vlan_nombre, mascara_vlan, solicitudes_combos in diagonal_manager.vlans_info_guardada:
            combos = []
            print(f"   VLAN {vlan_id} ({vlan_nombre}):")
            
            for solicitud_id in solicitudes_combos:
                resultado = diagonal_manager.obtener_combo_asignado(solicitud_id)
                if resultado:
                    red_asignada, mascara_real = resultado
                    combos.append([red_asignada, mascara_real])
                    print(f"     OK {red_asignada}/{mascara_real}")
            
            vlans_con_combos.append([vlan_id, combos])
    
    # Procesar redes P2P si existen
    if hasattr(diagonal_manager, 'solicitudes_p2p_guardadas'):
        print(f"\nCONVIRTIENDO RESULTADOS DE REDES P2P:")
        
        for solicitud_id in diagonal_manager.solicitudes_p2p_guardadas:
            resultado = diagonal_manager.obtener_combo_asignado(solicitud_id)
            if resultado:
                red_asignada, mascara_real = resultado
                redes_p2p_disponibles.append([red_asignada, mascara_real])
                print(f"     OK P2P: {red_asignada}/{mascara_real}")
    
    print(f"\nCONVERSION COMPLETADA:")
    print(f"   📊 VLANs procesadas: {len(vlans_con_combos)}")
    print(f"   📊 Redes P2P procesadas: {len(redes_p2p_disponibles)}")
    
    return vlans_con_combos, redes_p2p_disponibles

def preparar_combos_gestion(mgmt_base_ip, mgmt_prefijo_combo, num_dominios):
    """Prepara combos de gestión para switches (sin cambios)"""
    try:
        red_padre_ip = mgmt_base_ip.split('.')
        red_padre_ip[1] = red_padre_ip[2] = red_padre_ip[3] = '0'
        red_padre = ipaddress.ip_network(f"{'.'.join(red_padre_ip)}/8", strict=False)
        
        if mgmt_prefijo_combo < red_padre.prefixlen:
            print(f"❌ Error: El prefijo del combo de gestión (/{mgmt_prefijo_combo}) no puede ser más pequeño que el de la red padre /8.")
            return []
        
        combos = list(red_padre.subnets(new_prefix=mgmt_prefijo_combo))
        indice_inicio = 0
        ip_base_obj = ipaddress.ip_address(mgmt_base_ip)
        
        for i, combo in enumerate(combos):
            if ip_base_obj in combo:
                indice_inicio = i
                break
        
        combos_finales = combos[indice_inicio:]
        
        if len(combos_finales) > 0:
            print(f"ℹ️ Red de gestión base {mgmt_base_ip} con combos de /{mgmt_prefijo_combo}. Omitiendo el primer combo: {combos_finales[0]}")
            combos_finales.pop(0)
        
        if len(combos_finales) < num_dominios:
            print(f"⚠️ Aviso: No hay suficientes combos de gestión ({len(combos_finales)}) para los {num_dominios} dominios de router. Algunos switches no recibirán configuración.")
        
        return combos_finales
        
    except Exception as e:
        print(f"❌ Error al preparar los combos de la red de gestión: {e}")
        return []
