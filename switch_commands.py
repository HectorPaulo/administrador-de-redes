def generar_config_base(sw_name, vlan_ids, vlans_nombres=None):
    """Genera configuración base del switch"""
    comandos = ["en", "conf t", f"hostname {sw_name}"]
    
    # Configurar VLANs
    for vlan_id in sorted(vlan_ids):
        nombre_vlan = vlans_nombres.get(vlan_id, str(vlan_id)) if vlans_nombres else str(vlan_id)
        comandos.extend([
            f"vlan {vlan_id}",
            f"name {nombre_vlan}"
        ])
    
    comandos.append("exit")
    return comandos

def anadir_config_gestion(comandos, mgmt_hosts_iterator=None, mgmt_mask_decimal="", mgmt_gateway=""):
    """Añade configuración de gestión SSH"""
    from config import SSH_CONFIG  # Import here to avoid circular imports
    
    if mgmt_hosts_iterator:
        try:
            mgmt_ip = str(next(mgmt_hosts_iterator))
            comandos.extend([
                "\n",
                "int vlan 1",
                f"ip address {mgmt_ip} {mgmt_mask_decimal}",
                "no shutdown",
                "exit",
                f"ip default-gateway {mgmt_gateway}"
            ])
            
            comandos.extend([
                f"ip domain-name {SSH_CONFIG['domain']}",
                "crypto key generate rsa",
                "yes",
                str(SSH_CONFIG['rsa_key_size']),
                f"ip ssh version {SSH_CONFIG['ssh_version']}",
                "line vty 0 15",
                "transport input ssh",
                "login local",
                f"username {SSH_CONFIG['username']} privilege 1 secret {SSH_CONFIG['password']}",
                f"enable secret {SSH_CONFIG['enable_secret']}"
            ])
        except StopIteration:
            print(f"⚠️ No hay más IPs de gestión disponibles en el combo para {comandos[2]}.")
    
    return comandos

def generar_comandos_switches_acceso(router_num, vlans_asignadas, l2_config, mgmt_combo, 
                                   vlans_nombres=None, modo_config=1, conectado_a_swc3=False):
    """Genera comandos para switches de acceso"""
    from utils import validar_limites_dispositivos, get_switch_trunk_interface, get_switch_access_interface
    
    if not vlans_asignadas:
        return {}
    
    configs = {}
    
    # Validar límites
    validar_limites_dispositivos(router_num=router_num)
    
    # Configurar gestión
    mgmt_hosts_iterator = None
    mgmt_gateway = ""
    mgmt_mask_decimal = ""
    
    if mgmt_combo:
        mgmt_hosts_iterator = mgmt_combo.hosts()
        mgmt_gateway = str(list(mgmt_combo.hosts())[-1])
        mgmt_mask_decimal = str(mgmt_combo.netmask)

    vlan_ids = [int(v_id) for v_id in vlans_asignadas.keys()]
    tipo = l2_config.get("type", "simple")
    
    if tipo == "star":
        num_switches = l2_config.get("count", 1)
        for i in range(1, num_switches + 1):
            sw_name = f"SW-{router_num}-{i}"
            sw_cmds = generar_config_base(sw_name, vlan_ids, vlans_nombres)
            puerto_hacia_arriba = get_switch_trunk_interface(i, 0, modo_config, "swc3" if conectado_a_swc3 else "router")
            sw_cmds.extend([
                f"int {puerto_hacia_arriba}",
                "switchport mode trunk",
                "exit"
            ])
            sw_cmds = anadir_config_gestion(sw_cmds, mgmt_hosts_iterator, mgmt_mask_decimal, mgmt_gateway)
            sw_cmds.append("\nend")
            configs[sw_name] = sw_cmds
    
    elif tipo == "etherchannel":
        proto = l2_config.get("protocol", "lacp")
        mode1 = "active" if proto == "lacp" else "desirable"
        mode2 = "passive" if proto == "lacp" else "auto"
        
        # Switch 1 (conectado al router)
        sw1_name = f"SW-{router_num}-1"
        sw1_cmds = generar_config_base(sw1_name, vlan_ids, vlans_nombres)
        
        # EtherChannel hacia Switch 2 (fa0/1-3) + trunk hacia Switch 2 (fa0/4)
        sw1_cmds.extend([
            "int range fa0/1-3",
            "switchport mode trunk",
            f"channel-group 1 mode {mode1}",
            "exit",
            "int fa0/4",
            "switchport mode trunk",
            "exit"
        ])
        sw1_cmds = anadir_config_gestion(sw1_cmds, mgmt_hosts_iterator, mgmt_mask_decimal, mgmt_gateway)
        sw1_cmds.append("\nend")
        configs[sw1_name] = sw1_cmds
        
        # Switch 2 (conectado solo al Switch 1)
        sw2_name = f"SW-{router_num}-2"
        sw2_cmds = generar_config_base(sw2_name, vlan_ids, vlans_nombres)
        
        # Solo EtherChannel (fa0/1-3), NO hay conexión directa al router
        sw2_cmds.extend([
            "int range fa0/1-3",
            "switchport mode trunk",
            f"channel-group 1 mode {mode2}",
            "exit"
        ])
        sw2_cmds = anadir_config_gestion(sw2_cmds, mgmt_hosts_iterator, mgmt_mask_decimal, mgmt_gateway)
        sw2_cmds.append("\nend")
        configs[sw2_name] = sw2_cmds
    
    elif tipo == "spanning_tree":
        # Usar interfaces dinámicas para spanning tree
        puerto_hacia_arriba = get_switch_trunk_interface(1, 0, modo_config, "swc3" if conectado_a_swc3 else "router")
        
        # Switch 1 (Root)
        sw1_name = f"SW-{router_num}-1"
        sw1_cmds = generar_config_base(sw1_name, vlan_ids, vlans_nombres)
        trunk_int1 = get_switch_trunk_interface(1, 1, modo_config)
        trunk_int2 = get_switch_trunk_interface(1, 2, modo_config)
        sw1_cmds.extend([
            "spanning-tree vlan 1 priority 4096",
            f"int {puerto_hacia_arriba}",
            "switchport mode trunk",
            f"int {trunk_int1}",
            "switchport mode trunk",
            f"int {trunk_int2}",
            "switchport mode trunk",
            "exit"
        ])
        sw1_cmds = anadir_config_gestion(sw1_cmds, mgmt_hosts_iterator, mgmt_mask_decimal, mgmt_gateway)
        sw1_cmds.append("\nend")
        configs[sw1_name] = sw1_cmds
        
        # Switch 2
        sw2_name = f"SW-{router_num}-2"
        sw2_cmds = generar_config_base(sw2_name, vlan_ids, vlans_nombres)
        trunk_int1 = get_switch_trunk_interface(2, 1, modo_config)
        trunk_int3 = get_switch_trunk_interface(2, 3, modo_config)
        sw2_cmds.extend([
            f"int {trunk_int1}",
            "switchport mode trunk",
            f"int {trunk_int3}",
            "switchport mode trunk",
            "exit"
        ])
        sw2_cmds = anadir_config_gestion(sw2_cmds, mgmt_hosts_iterator, mgmt_mask_decimal, mgmt_gateway)
        sw2_cmds.append("\nend")
        configs[sw2_name] = sw2_cmds
        
        # Switch 3
        sw3_name = f"SW-{router_num}-3"
        sw3_cmds = generar_config_base(sw3_name, vlan_ids, vlans_nombres)
        trunk_int2 = get_switch_trunk_interface(3, 2, modo_config)
        trunk_int3 = get_switch_trunk_interface(3, 3, modo_config)
        sw3_cmds.extend([
            f"int {trunk_int2}",
            "switchport mode trunk",
            f"int {trunk_int3}",
            "switchport mode trunk",
            "exit"
        ])
        sw3_cmds = anadir_config_gestion(sw3_cmds, mgmt_hosts_iterator, mgmt_mask_decimal, mgmt_gateway)
        sw3_cmds.append("\nend")
        configs[sw3_name] = sw3_cmds
    
    else:  # simple o daisy_chain
        num_switches = l2_config.get("count", 1)
        for i in range(1, num_switches + 1):
            puerto_hacia_arriba = get_switch_trunk_interface(i, 0, modo_config, "swc3" if conectado_a_swc3 else "router") if i == 1 else get_switch_trunk_interface(i, 0, modo_config)
            sw_name = f"SW-{router_num}" if num_switches == 1 else f"SW-{router_num}-{i}"
            sw_cmds = generar_config_base(sw_name, vlan_ids, vlans_nombres)
            
            sw_cmds.extend([
                f"int {puerto_hacia_arriba}",
                "switchport mode trunk"
            ])
            
            if tipo == "daisy_chain" and i < num_switches:
                puerto_siguiente = get_switch_trunk_interface(i, 1, modo_config)
                sw_cmds.extend([
                    f"int {puerto_siguiente}",
                    "switchport mode trunk"
                ])
            
            if tipo == "simple":
                for vlan_id in vlan_ids:
                    port = get_switch_access_interface(router_num, vlan_id, modo_config)
                    sw_cmds.extend([
                        f"int {port}",
                        "switchport mode access",
                        f"switchport access vlan {vlan_id}"
                    ])
            
            sw_cmds = anadir_config_gestion(sw_cmds, mgmt_hosts_iterator, mgmt_mask_decimal, mgmt_gateway)
            sw_cmds.append("\nend")
            configs[sw_name] = sw_cmds
    
    return configs

def generar_comandos_switches_acceso_con_wlc(router_num, vlans_asignadas, wlc_config, 
                                           topologia_switches, mgmt_combo, vlans_nombres=None, modo_config=1):
    """Genera comandos para switches de acceso con WLC"""
    from utils import validar_limites_dispositivos, get_switch_trunk_interface, get_switch_access_interface
    from config import SSH_CONFIG
    
    if not vlans_asignadas:
        return {}
    
    configs = {}
    
    # Validar límites
    validar_limites_dispositivos(router_num=router_num)
    
    # Configurar gestión
    mgmt_hosts_iterator = None
    mgmt_gateway = ""
    mgmt_mask_decimal = ""
    
    if mgmt_combo:
        mgmt_hosts_iterator = mgmt_combo.hosts()
        mgmt_gateway = str(list(mgmt_combo.hosts())[-1])
        mgmt_mask_decimal = str(mgmt_combo.netmask)
    
    def generar_config_base_wlc(sw_name, vlan_ids, vlan_nativa):
        """Genera configuración base del switch con WLC"""
        comandos = ["en", "conf t", f"hostname {sw_name}"]
        
        # Configurar VLANs
        for vlan_id in sorted(vlan_ids):
            if vlan_id == vlan_nativa:
                nombre_vlan = "native"
            else:
                nombre_vlan = vlans_nombres.get(vlan_id, str(vlan_id)) if vlans_nombres else str(vlan_id)
            comandos.extend([
                f"vlan {vlan_id}",
                f"name {nombre_vlan}"
            ])
        
        comandos.append("exit")
        return comandos
    
    def anadir_config_gestion_local(comandos):
        """Añade configuración de gestión SSH"""
        if mgmt_hosts_iterator:
            try:
                mgmt_ip = str(next(mgmt_hosts_iterator))
                comandos.extend([
                    "int vlan 1",
                    f"ip address {mgmt_ip} {mgmt_mask_decimal}",
                    "no shutdown",
                    "exit",
                    f"ip default-gateway {mgmt_gateway}",
                    f"ip domain-name {SSH_CONFIG['domain']}",
                    "crypto key generate rsa",
                    "yes",
                    str(SSH_CONFIG['rsa_key_size']),
                    f"ip ssh version {SSH_CONFIG['ssh_version']}",
                    "line vty 0 15",
                    "transport input ssh",
                    "login local",
                    f"username {SSH_CONFIG['username']} privilege 1 secret {SSH_CONFIG['password']}",
                    f"enable secret {SSH_CONFIG['enable_secret']}"
                ])
            except StopIteration:
                print(f"⚠️ No hay más IPs de gestión disponibles en el combo para {comandos[2]}.")
        
        return comandos
    
    vlan_ids = [int(v_id) for v_id in vlans_asignadas.keys()]
    vlan_nativa = wlc_config['vlan_nativa']
    count = topologia_switches["count"]
    tipo = topologia_switches["type"]
    
    if count == 1:
        # Un solo switch
        sw_name = f"SW-{router_num}"
        sw_cmds = generar_config_base_wlc(sw_name, vlan_ids, vlan_nativa)
        
        # Puerto hacia SWC3
        puerto_swc3 = get_switch_trunk_interface(1, 0, modo_config, "swc3")
        sw_cmds.extend([
            f"int {puerto_swc3}",
            "switchport mode trunk",
            f"switchport trunk native vlan {vlan_nativa}"
        ])
        
        # Puerto para AP
        puerto_ap = get_switch_trunk_interface(1, 1, modo_config)
        sw_cmds.extend([
            f"int {puerto_ap}",
            "switchport mode trunk",
            f"switchport trunk native vlan {vlan_nativa}"
        ])
        
        # Puerto para PC
        puerto_pc = get_switch_access_interface(router_num, vlan_ids[0] if vlan_ids else vlan_nativa, modo_config)
        sw_cmds.extend([
            f"int {puerto_pc}",
            f"switchport access vlan {vlan_ids[0] if vlan_ids else vlan_nativa}"
        ])
        
        sw_cmds = anadir_config_gestion_local(sw_cmds)
        sw_cmds.append("end")
        configs[sw_name] = sw_cmds
        
    elif count == 2:
        if tipo == "estrella":
            # Dos switches conectados directamente al SWC3
            for i in range(1, 3):
                sw_name = f"SW-{router_num}-{i}"
                sw_cmds = generar_config_base_wlc(sw_name, vlan_ids, vlan_nativa)
                
                # Puerto hacia SWC3
                puerto_swc3 = get_switch_trunk_interface(i, 0, modo_config, "swc3")
                sw_cmds.extend([
                    f"int {puerto_swc3}",
                    "switchport mode trunk",
                    f"switchport trunk native vlan {vlan_nativa}"
                ])
                
                # Puerto para AP/PC
                puerto_device = get_switch_trunk_interface(i, 1, modo_config)
                sw_cmds.extend([
                    f"int {puerto_device}",
                    "switchport mode trunk",
                    f"switchport trunk native vlan {vlan_nativa}"
                ])
                
                sw_cmds = anadir_config_gestion_local(sw_cmds)
                sw_cmds.append("end")
                configs[sw_name] = sw_cmds
                
        else:  # cadena
            # Switch 1 conectado al SWC3
            sw1_name = f"SW-{router_num}-1"
            sw1_cmds = generar_config_base_wlc(sw1_name, vlan_ids, vlan_nativa)
            
            # Puerto hacia SWC3
            puerto_swc3 = get_switch_trunk_interface(1, 0, modo_config, "swc3")
            sw1_cmds.extend([
                f"int {puerto_swc3}",
                "switchport mode trunk",
                f"switchport trunk native vlan {vlan_nativa}"
            ])
            
            # Puerto hacia segundo switch
            puerto_switch2 = get_switch_trunk_interface(1, 1, modo_config)
            sw1_cmds.extend([
                f"int {puerto_switch2}",
                "switchport mode trunk",
                f"switchport trunk native vlan {vlan_nativa}"
            ])
            
            sw1_cmds = anadir_config_gestion_local(sw1_cmds)
            sw1_cmds.append("end")
            configs[sw1_name] = sw1_cmds
            
            # Switch 2 conectado al Switch 1
            sw2_name = f"SW-{router_num}-2"
            sw2_cmds = generar_config_base_wlc(sw2_name, vlan_ids, vlan_nativa)
            
            # Puerto hacia primer switch
            puerto_switch1 = get_switch_trunk_interface(2, 0, modo_config)
            sw2_cmds.extend([
                f"int {puerto_switch1}",
                "switchport mode trunk",
                f"switchport trunk native vlan {vlan_nativa}"
            ])
            
            # Puerto para AP
            puerto_ap = get_switch_trunk_interface(2, 1, modo_config)
            sw2_cmds.extend([
                f"int {puerto_ap}",
                "switchport mode trunk",
                f"switchport trunk native vlan {vlan_nativa}"
            ])
            
            sw2_cmds = anadir_config_gestion_local(sw2_cmds)
            sw2_cmds.append("end")
            configs[sw2_name] = sw2_cmds
    
    return configs
