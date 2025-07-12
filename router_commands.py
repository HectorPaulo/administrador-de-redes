"""
Generación de comandos para routers
"""
from ip_utils import obtener_ip_usable, convertir_mascara_prefijo_a_decimal
from routing import generar_rutas_estaticas_dijkstra
from config import SSH_CONFIG
from interface_manager import (
    get_wan_interface, get_lan_interface, get_port_channel_interface, 
    get_etherchannel_interfaces, validar_limites_dispositivos
)

def generar_comandos_router_ROAS(router_num, vlans_asignadas, conexiones, modo_config, 
                                todas_las_conexiones, vlans_por_router, config_swc3, l2_config):
    """Genera comandos para router con configuración ROAS (Router on a Stick)"""
    # Validar límites
    validar_limites_dispositivos(router_num=router_num)
    
    comandos = ["en", "conf t", f"hostname R{router_num}"]
    
    # Para ROAS, el router SIEMPRE usa la interfaz LAN normal
    # El EtherChannel se configura en los SWITCHES, no en el router
    interfaz_hacia_switch = get_lan_interface(router_num, 0, modo_config)
    
    # Configurar interfaces WAN
    conexiones_ordenadas = sorted(conexiones.items())
    for idx, (hacia_router, connection_data) in enumerate(conexiones_ordenadas):
        interfaz = get_wan_interface(router_num, idx, modo_config)
        
        # Obtener IP específica de este router desde todas_las_conexiones
        conexion_key = str(tuple(sorted((router_num, int(hacia_router)))))
        if conexion_key in todas_las_conexiones:
            conn_info = todas_las_conexiones[conexion_key]
            if isinstance(conn_info, dict):
                # Nuevo formato con IPs específicas
                ip_propia = conn_info[f'ip_r{router_num}']
                mascara = conn_info['mascara']
            else:
                # Formato antiguo: usar lógica previa como fallback
                red, mascara = conn_info
                es_primer_router = router_num < int(hacia_router)
                ip_propia = obtener_ip_usable(red, mascara, 0 if es_primer_router else -1)
        else:
            # Fallback usando connection_data local
            red, mascara, es_primer_router = connection_data
            ip_propia = obtener_ip_usable(red, mascara, 0 if es_primer_router else -1)
        
        comandos.extend([
            f"int {interfaz}",
            f"ip add {ip_propia} {convertir_mascara_prefijo_a_decimal(mascara)}",
            "no shut"
        ])
    
    # Configurar subinterfaces para VLANs
    if vlans_asignadas:
        # IMPORTANTE: Levantar la interfaz principal ANTES de las subinterfaces
        comandos.extend([
            f"int {interfaz_hacia_switch}", 
            "no shut",
            "exit"
        ])
        
        for vlan_id, (red, mascara) in vlans_asignadas.items():
            ip_gateway = obtener_ip_usable(red, mascara, -1)
            comandos.extend([
                f"int {interfaz_hacia_switch}.{vlan_id}",
                f"encapsulation dot1Q {vlan_id}",
                f"ip add {ip_gateway} {convertir_mascara_prefijo_a_decimal(mascara)}",
                "no shut"
            ])
    
    comandos.append("exit\n\n\n")
    
    # Configurar pools DHCP
    if vlans_asignadas:
        for vlan_id, (red, mascara) in vlans_asignadas.items():
            ip_gateway = obtener_ip_usable(red, mascara, -1)
            comandos.extend([
                f"ip dhcp pool vlan{vlan_id}",
                f"default-router {ip_gateway}",
                f"network {red} {convertir_mascara_prefijo_a_decimal(mascara)}"
            ])
    
    # Configurar seguridad SSH
    comandos.extend([
        f"ip domain-name {SSH_CONFIG['domain']}",
        f"username {SSH_CONFIG['username']} privilege 1 secret {SSH_CONFIG['password']}",
        "\n\n\ncrypto key generate rsa",
        "yes",
        str(SSH_CONFIG['rsa_key_size']),
        f"ip ssh version {SSH_CONFIG['ssh_version']}",
        f"enable secret {SSH_CONFIG['enable_secret']}",
        "line vty 0 4",
        "transport input ssh",
        "login local"
    ])
    
    # Generar rutas estáticas
    rutas = generar_rutas_estaticas_dijkstra(router_num, todas_las_conexiones, vlans_por_router, config_swc3)
    if rutas:
        comandos.extend(rutas)
    
    comandos.append("\nend")
    return comandos

def generar_comandos_router_para_swc3(router_num, conexiones, swc3_config, modo_config, 
                                     todas_las_conexiones, vlans_por_router, progreso):
    """Genera comandos para router que se conecta a SWC3"""
    # Validar límites
    validar_limites_dispositivos(router_num=router_num)
    
    comandos = ["en", "conf t", f"hostname R{router_num}"]
    
    # Configurar interfaz hacia SWC3
    interfaz_hacia_swc3 = get_lan_interface(router_num, 0, modo_config)
    red_r_swc3, mascara_r_swc3 = swc3_config['red_hacia_router']
    ip_router = obtener_ip_usable(red_r_swc3, mascara_r_swc3, 0)
    ip_swc3 = obtener_ip_usable(red_r_swc3, mascara_r_swc3, -1)
    mascara_decimal = convertir_mascara_prefijo_a_decimal(mascara_r_swc3)
    
    comandos.extend([
        f"int {interfaz_hacia_swc3}",
        f"ip add {ip_router} {mascara_decimal}",
        "no shut"
    ])
    
    # Configurar interfaces WAN
    for idx, (hacia_router, connection_data) in enumerate(sorted(conexiones.items())):
        interfaz = get_wan_interface(router_num, idx, modo_config)
        
        # Obtener IP específica desde todas_las_conexiones
        conexion_key = str(tuple(sorted((router_num, int(hacia_router)))))
        if conexion_key in todas_las_conexiones:
            conn_info = todas_las_conexiones[conexion_key]
            if isinstance(conn_info, dict):
                ip_propia = conn_info[f'ip_r{router_num}']
                mascara = conn_info['mascara']
            else:
                red, mascara = conn_info
                es_primer_router = router_num < int(hacia_router)
                ip_propia = obtener_ip_usable(red, mascara, 0 if es_primer_router else -1)
        else:
            red, mascara, es_primer_router = connection_data
            ip_propia = obtener_ip_usable(red, mascara, 0 if es_primer_router else -1)
        
        comandos.extend([
            f"int {interfaz}",
            f"ip add {ip_propia} {convertir_mascara_prefijo_a_decimal(mascara)}",
            "no shut"
        ])
    
    comandos.append("exit\n\n\n")
    
    # Configurar seguridad SSH
    comandos.extend([
        f"ip domain-name {SSH_CONFIG['domain']}",
        f"username {SSH_CONFIG['username']} privilege 1 secret {SSH_CONFIG['password']}",
        "\n\n\ncrypto key generate rsa",
        "yes",
        str(SSH_CONFIG['rsa_key_size']),
        f"ip ssh version {SSH_CONFIG['ssh_version']}",
        f"enable secret {SSH_CONFIG['enable_secret']}",
        "line vty 0 4",
        "transport input ssh",
        "login local"
    ])
    
    # Configurar rutas hacia VLANs vía SWC3
    for vlan_id_str, (vlan_red, vlan_mascara) in vlans_por_router.get(str(router_num), {}).items():
        comandos.append(f"ip route {vlan_red} {convertir_mascara_prefijo_a_decimal(vlan_mascara)} {ip_swc3}")
    
    # Generar rutas estáticas remotas
    rutas_remotas = generar_rutas_estaticas_dijkstra(router_num, todas_las_conexiones, vlans_por_router, progreso['config_swc3'])
    if rutas_remotas:
        comandos.extend(rutas_remotas)
    
    comandos.append("\nend")
    return comandos

def generar_comandos_router_con_wlc(router_num, vlans_asignadas, conexiones, wlc_config, 
                                   todas_las_conexiones, vlans_por_router, config_swc3):
    """Genera comandos para router con WLC usando subinterfaces dot1Q"""
    comandos = ["en", "conf t", f"hostname R{router_num}"]
    
    # Configurar interfaz hacia servidor
    servidor_interface = f"eth0/{len(conexiones)}/0"
    comandos.extend([
        f"int {servidor_interface}",
        f"ip add {wlc_config['ip_servidor']} {convertir_mascara_prefijo_a_decimal(wlc_config['mascara_servidor'])}",
        "no shut"
    ])
    
    # Configurar interfaces WAN (conexiones entre routers)
    conexiones_ordenadas = sorted(conexiones.items())
    for idx, (hacia_router, connection_data) in enumerate(conexiones_ordenadas):
        interfaz = f"eth0/{idx}/0"
        
        # Obtener IP específica desde todas_las_conexiones
        conexion_key = str(tuple(sorted((router_num, int(hacia_router)))))
        if conexion_key in todas_las_conexiones:
            conn_info = todas_las_conexiones[conexion_key]
            if isinstance(conn_info, dict):
                ip_propia = conn_info[f'ip_r{router_num}']
                mascara = conn_info['mascara']
            else:
                red, mascara = conn_info
                es_primer_router = router_num < int(hacia_router)
                ip_propia = obtener_ip_usable(red, mascara, 0 if es_primer_router else -1)
        else:
            red, mascara, es_primer_router = connection_data
            ip_propia = obtener_ip_usable(red, mascara, 0 if es_primer_router else -1)
        
        comandos.extend([
            f"int {interfaz}",
            f"ip add {ip_propia} {convertir_mascara_prefijo_a_decimal(mascara)}",
            "no shut"
        ])
    
    # Configurar conexión a SWC3
    if str(router_num) in config_swc3:
        red_swc3, mascara_swc3 = config_swc3[str(router_num)]['red_hacia_router']
        ip_router = obtener_ip_usable(red_swc3, mascara_swc3, 0)
        # Usar la segunda interfaz LAN disponible
        swc3_interface = get_lan_interface(router_num, 1, modo_config)
        comandos.extend([
            f"int {swc3_interface}",
            f"ip add {ip_router} {convertir_mascara_prefijo_a_decimal(mascara_swc3)}",
            "no shut"
        ])
    
    # Configurar interfaz principal para subinterfaces
    # Usar la primera interfaz LAN disponible (diferente de SWC3 si existe)
    main_interface = get_lan_interface(router_num, 0, modo_config)
    
    comandos.extend([
        f"int {main_interface}",
        "no shut"
    ])
    
    # Configurar subinterfaces para VLANs
    for vlan_id_str, (red, mascara) in vlans_asignadas.items():
        vlan_id = int(vlan_id_str)
        ip_gateway = obtener_ip_usable(red, mascara, -1)
        
        if vlan_id == wlc_config['vlan_nativa']:
            comandos.extend([
                f"int {main_interface}.{vlan_id}",
                f"encapsulation dot1Q {vlan_id} native",
                f"ip add {ip_gateway} {convertir_mascara_prefijo_a_decimal(mascara)}",
                "no shut"
            ])
        else:
            comandos.extend([
                f"int {main_interface}.{vlan_id}",
                f"encapsulation dot1Q {vlan_id}",
                f"ip add {ip_gateway} {convertir_mascara_prefijo_a_decimal(mascara)}",
                "no shut"
            ])
    
    comandos.append("exit")
    
    # Configurar pools DHCP para todas las VLANs
    for vlan_id_str, (red, mascara) in vlans_asignadas.items():
        vlan_id = int(vlan_id_str)
        ip_gateway = obtener_ip_usable(red, mascara, -1)
        pool_name = "native" if vlan_id == wlc_config['vlan_nativa'] else vlan_id_str
        comandos.extend([
            f"ip dhcp pool {pool_name}",
            f"network {red} {convertir_mascara_prefijo_a_decimal(mascara)}",
            f"default-router {ip_gateway}"
        ])
    
    # Configurar seguridad SSH
    comandos.extend([
        f"ip domain-name {SSH_CONFIG['domain']}",
        f"username {SSH_CONFIG['username']} privilege 1 secret {SSH_CONFIG['password']}",
        "crypto key generate rsa",
        "yes",
        str(SSH_CONFIG['rsa_key_size']),
        f"ip ssh version {SSH_CONFIG['ssh_version']}",
        f"enable secret {SSH_CONFIG['enable_secret']}",
        "line vty 0 4",
        "transport input ssh",
        "login local"
    ])
    
    # Generar rutas estáticas
    rutas = generar_rutas_estaticas_dijkstra(router_num, todas_las_conexiones, vlans_por_router, config_swc3)
    if rutas:
        comandos.extend(rutas)
    
    comandos.append("end")
    return comandos
