"""
Gestión de interfaces para routers y switches según modo (simulación/físico)
"""

def get_wan_interface(router_num, interface_index, modo_config):
    """
    Obtiene la interfaz WAN para un router según el modo y número de router
    
    Args:
        router_num (int): Número del router (1-5)
        interface_index (int): Índice de la interfaz (0, 1, 2...)
        modo_config (int): 1=Simulación, 2=Físico
    
    Returns:
        str: Nombre de la interfaz (ej: "gi0/0/0", "eth0/0/0")
    """
    if modo_config == 1:  # Simulación
        return f"eth0/{interface_index}/0"
    else:  # Físico
        if router_num <= 3:  # Routers 1-3: gi0/x (x: 0-2)
            if interface_index > 2:
                raise ValueError(f"Router {router_num} solo soporta índices 0-2, recibido: {interface_index}")
            return f"gi0/{interface_index}"
        elif router_num <= 5:  # Routers 4-5: gi0/0/x (x: 0-1)
            if interface_index > 1:
                raise ValueError(f"Router {router_num} solo soporta índices 0-1, recibido: {interface_index}")
            return f"gi0/0/{interface_index}"
        else:
            raise ValueError(f"Máximo 5 routers soportados, recibido: {router_num}")

def get_lan_interface(router_num, interface_index, modo_config, es_etherchannel=False):
    """
    Obtiene la interfaz LAN para un router (hacia switches)
    
    Args:
        router_num (int): Número del router (1-5)
        interface_index (int): Índice de la interfaz (0, 1)
        modo_config (int): 1=Simulación, 2=Físico
        es_etherchannel (bool): Si va a usar EtherChannel
    
    Returns:
        str: Nombre de la interfaz
    """
    if modo_config == 1:  # Simulación
        if es_etherchannel:
            return f"fa0/{interface_index}"
        return "fa0/0" if interface_index == 0 else "fa0/1"
    else:  # Físico
        if router_num <= 3:  # Routers 1-3: usar las últimas gi0/x
            # Para LAN usar gi0/2, gi0/1 (en orden inverso para no chocar con WAN)
            if interface_index == 0:
                return "gi0/2"
            elif interface_index == 1:
                return "gi0/1"  # Solo si necesita segunda interfaz
            else:
                raise ValueError(f"Router {router_num} LAN solo soporta índices 0-1")
        elif router_num <= 5:  # Routers 4-5: usar gi0/0/1, luego agregar más si es necesario
            # Para LAN usar gi0/0/1, y si necesita más podríamos usar gi0/1/0
            if interface_index == 0:
                return "gi0/0/1"  # Segunda interfaz disponible
            else:
                # Si necesita más interfaces, usamos el formato extendido
                return f"gi0/1/{interface_index-1}"
        else:
            raise ValueError(f"Máximo 5 routers soportados, recibido: {router_num}")

def get_switch_trunk_interface(switch_num, interface_index, modo_config, hacia_donde="router"):
    """
    Obtiene interfaz de trunk para switch
    
    Args:
        switch_num (int): Número del switch (1-5)
        interface_index (int): Índice de la interfaz
        modo_config (int): 1=Simulación, 2=Físico
        hacia_donde (str): "router", "switch", "swc3"
    
    Returns:
        str: Nombre de la interfaz
    """
    if modo_config == 1:  # Simulación
        return f"fa0/{interface_index}"
    else:  # Físico
        if switch_num <= 3:  # Switches 1-3: gi0/x primero, luego fa0/x
            if interface_index <= 1:  # Usar gi0/1, gi0/2 primero
                return f"gi0/{interface_index+1}"
            else:  # Luego fa0/1-24
                fa_index = interface_index - 1  # Ajustar índice
                if fa_index > 24:
                    raise ValueError(f"Switch {switch_num} excede interfaces disponibles")
                return f"fa0/{fa_index}"
        elif switch_num <= 5:  # Switches 4-5: gi1/0/x
            if interface_index > 24:
                raise ValueError(f"Switch {switch_num} solo soporta hasta 24 interfaces")
            return f"gi1/0/{interface_index+1}"
        else:
            raise ValueError(f"Máximo 5 switches soportados, recibido: {switch_num}")

def get_switch_access_interface(switch_num, vlan_id, modo_config):
    """
    Obtiene interfaz de acceso para un switch según VLAN
    
    Args:
        switch_num (int): Número del switch
        vlan_id (int): ID de la VLAN
        modo_config (int): 1=Simulación, 2=Físico
    
    Returns:
        str: Nombre de la interfaz de acceso
    """
    if modo_config == 1:  # Simulación - mantener lógica actual
        access_ports_map = {2: 'fa0/2', 3: 'fa0/1', 4: 'fa0/3'}
        return access_ports_map.get(vlan_id, f'fa0/{vlan_id}')
    else:  # Físico
        if switch_num <= 3:  # Switches 1-3
            # Usar fa0/x para acceso (x: 3-24, evitando gi0/1-2 para trunks)
            if vlan_id == 2:
                return "fa0/3"
            elif vlan_id == 3:
                return "fa0/4"
            elif vlan_id == 4:
                return "fa0/5"
            else:
                return f"fa0/{vlan_id + 1}"  # Fórmula general
        elif switch_num <= 5:  # Switches 4-5
            # Usar gi1/0/x para acceso (x: 20-24, dejando 1-19 para trunks)
            if vlan_id == 2:
                return "gi1/0/20"
            elif vlan_id == 3:
                return "gi1/0/21"
            elif vlan_id == 4:
                return "gi1/0/22"
            else:
                return f"gi1/0/{min(20 + vlan_id, 24)}"
        else:
            raise ValueError(f"Máximo 5 switches soportados, recibido: {switch_num}")

def get_swc3_interface_hacia_router(swc3_num, modo_config):
    """
    Obtiene interfaz del SWC3 hacia el router
    
    Args:
        swc3_num (int): Número del SWC3 (asociado al router)
        modo_config (int): 1=Simulación, 2=Físico
    
    Returns:
        str: Nombre de la interfaz
    """
    if modo_config == 1:  # Simulación
        return "GigabitEthernet1/0/1"
    else:  # Físico
        if swc3_num <= 3:  # SWC3 para routers 1-3
            return "gi0/1"  # Primera interfaz gi disponible
        elif swc3_num <= 5:  # SWC3 para routers 4-5
            return "gi1/0/1"  # Primera interfaz gi1/0 disponible
        else:
            raise ValueError(f"SWC3 {swc3_num} no soportado")

def get_swc3_interface_hacia_switch(swc3_num, switch_index, modo_config):
    """
    Obtiene interfaz del SWC3 hacia switches de acceso
    
    Args:
        swc3_num (int): Número del SWC3
        switch_index (int): Índice del switch (0, 1, 2...)
        modo_config (int): 1=Simulación, 2=Físico
    
    Returns:
        str: Nombre de la interfaz
    """
    if modo_config == 1:  # Simulación
        return f"GigabitEthernet1/0/{switch_index+2}"
    else:  # Físico
        if swc3_num <= 3:  # SWC3 para routers 1-3
            return f"gi0/{switch_index+2}"  # gi0/2, gi0/3, etc.
        elif swc3_num <= 5:  # SWC3 para routers 4-5
            return f"gi1/0/{switch_index+2}"  # gi1/0/2, gi1/0/3, etc.
        else:
            raise ValueError(f"SWC3 {swc3_num} no soportado")

def validar_limites_dispositivos(router_num=None, switch_num=None):
    """
    Valida que no se excedan los límites de dispositivos
    
    Args:
        router_num (int, optional): Número del router a validar
        switch_num (int, optional): Número del switch a validar
    
    Raises:
        ValueError: Si se exceden los límites
    """
    if router_num is not None and router_num > 5:
        raise ValueError(f"Máximo 5 routers soportados, recibido: {router_num}")
    
    if switch_num is not None and switch_num > 5:
        raise ValueError(f"Máximo 5 switches soportados, recibido: {switch_num}")

def get_port_channel_interface(router_num, modo_config):
    """
    Obtiene el nombre del Port-Channel para EtherChannel
    
    Args:
        router_num (int): Número del router
        modo_config (int): 1=Simulación, 2=Físico
    
    Returns:
        str: Nombre del Port-Channel
    """
    # El Port-Channel es igual en ambos modos
    return "port-channel 1"

def get_etherchannel_interfaces(router_num, modo_config):
    """
    Obtiene las interfaces que formarán el EtherChannel
    
    Args:
        router_num (int): Número del router
        modo_config (int): 1=Simulación, 2=Físico
    
    Returns:
        list: Lista de interfaces para EtherChannel
    """
    if modo_config == 1:  # Simulación
        return ["fa0/0", "fa0/1"]
    else:  # Físico
        if router_num <= 3:  # Routers 1-3
            return ["gi0/1", "gi0/2"]  # Usar las interfaces LAN
        elif router_num <= 5:  # Routers 4-5
            return ["gi0/0/1", "gi0/1/0"]  # Usar interfaces extendidas
        else:
            raise ValueError(f"Router {router_num} no soportado para EtherChannel")
