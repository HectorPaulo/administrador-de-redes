"""
Algoritmos de enrutamiento
"""
import heapq
import ipaddress
from collections import deque
from ip_utils import obtener_ip_usable, convertir_mascara_prefijo_a_decimal

def generar_rutas_estaticas_dijkstra(router_actual_num, todas_las_conexiones, vlans_por_router, config_swc3):
    """Genera rutas estáticas usando algoritmo de Dijkstra para rutas óptimas"""
    rutas_finales = set()
    router_actual_num_str = str(router_actual_num)
    
    # Construir grafo con pesos (costo = 1 por salto)
    grafo = {str(k): {} for k in vlans_por_router.keys()}
    conexiones_info = {}  # Para almacenar info detallada de conexiones
    
    for conn_str, conn_data in todas_las_conexiones.items():
        if isinstance(conn_data, list):
            # Formato antiguo: convertir a nuevo formato
            red, mascara = conn_data
            r1, r2 = eval(conn_str)
            ip_r1 = obtener_ip_usable(red, mascara, 0)
            ip_r2 = obtener_ip_usable(red, mascara, -1)
        else:
            # Formato nuevo con IPs específicas
            red, mascara = conn_data['red'], conn_data['mascara']
            r1, r2 = conn_data['r1'], conn_data['r2']
            ip_r1, ip_r2 = conn_data['ip_r1'], conn_data['ip_r2']
        
        # Agregar aristas bidireccionales con costo 1
        grafo[str(r1)][str(r2)] = 1
        grafo[str(r2)][str(r1)] = 1
        
        # Guardar info de conexión para obtener next-hop
        conexiones_info[(str(r1), str(r2))] = {
            'red': red, 'mascara': mascara, 
            'ip_r1': ip_r1, 'ip_r2': ip_r2,
            'r1': r1, 'r2': r2
        }
        conexiones_info[(str(r2), str(r1))] = {
            'red': red, 'mascara': mascara,
            'ip_r1': ip_r2, 'ip_r2': ip_r1,  # Invertir para la dirección opuesta
            'r1': r2, 'r2': r1
        }
    
    # Recopilar todas las redes destino
    todas_las_redes = []
    
    # 1. VLANs de otros routers
    for r_owner_str, vlan_data in vlans_por_router.items():
        if r_owner_str != router_actual_num_str:
            for vid, (net, mask) in vlan_data.items():
                todas_las_redes.append({'net': net, 'mask': mask, 'owner': r_owner_str, 'tipo': 'VLAN'})
    
    # 2. Redes SWC3 de otros routers
    for r_owner_str, data in config_swc3.items():
        if r_owner_str != router_actual_num_str:
            net, mask = data['red_hacia_router']
            todas_las_redes.append({'net': net, 'mask': mask, 'owner': r_owner_str, 'tipo': 'SWC3'})
    
    # 3. NUEVO: Redes P2P que el router actual NO conoce directamente
    for conn_str, conn_data in todas_las_conexiones.items():
        if isinstance(conn_data, dict):
            red, mascara = conn_data['red'], conn_data['mascara']
            r1, r2 = conn_data['r1'], conn_data['r2']
        else:
            red, mascara = conn_data
            r1, r2 = eval(conn_str)
        
        # Si el router actual NO está en esta conexión P2P, debe enrutar hacia ella
        if router_actual_num not in [r1, r2]:
            # Determinar cuál router está más cerca para enrutar
            if str(r1) in grafo and str(r2) in grafo:
                # Elegir el router con menor distancia usando Dijkstra temporal
                dist_r1 = calcular_distancia_dijkstra(router_actual_num_str, str(r1), grafo)
                dist_r2 = calcular_distancia_dijkstra(router_actual_num_str, str(r2), grafo)
                router_destino = str(r1) if dist_r1 <= dist_r2 else str(r2)
                todas_las_redes.append({'net': red, 'mask': mascara, 'owner': router_destino, 'tipo': 'P2P'})
    
    # Identificar redes directas del router actual
    redes_directas = set()
    
    # VLANs propias
    for net, mask in vlans_por_router.get(router_actual_num_str, {}).values():
        redes_directas.add(net)
    
    # Conexiones P2P directas
    for conn_str, conn_data in todas_las_conexiones.items():
        if isinstance(conn_data, dict):
            red = conn_data['red']
            r1, r2 = conn_data['r1'], conn_data['r2']
        else:
            red = conn_data[0]
            r1, r2 = eval(conn_str)
        
        if router_actual_num in [r1, r2]:
            redes_directas.add(red)
    
    # Red SWC3 propia
    if router_actual_num_str in config_swc3:
        redes_directas.add(config_swc3[router_actual_num_str]['red_hacia_router'][0])
    
    # Aplicar Dijkstra para cada red destino
    for red_info in todas_las_redes:
        if red_info['net'] in redes_directas:
            continue  # Skip redes directas
        
        destino_router = red_info['owner']
        
        # Algoritmo de Dijkstra
        distancias = {nodo: float('infinity') for nodo in grafo}
        distancias[router_actual_num_str] = 0
        predecesores = {}
        cola_prioridad = [(0, router_actual_num_str)]
        visitados = set()
        
        while cola_prioridad:
            distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)
            
            if nodo_actual in visitados:
                continue
            
            visitados.add(nodo_actual)
            
            if nodo_actual == destino_router:
                break  # Encontramos el camino más corto
            
            for vecino, peso in grafo.get(nodo_actual, {}).items():
                distancia_nueva = distancia_actual + peso
                
                if distancia_nueva < distancias[vecino]:
                    distancias[vecino] = distancia_nueva
                    predecesores[vecino] = nodo_actual
                    heapq.heappush(cola_prioridad, (distancia_nueva, vecino))
        
        # Reconstruir camino más corto
        if destino_router in predecesores or destino_router == router_actual_num_str:
            camino = []
            nodo = destino_router
            while nodo != router_actual_num_str:
                camino.append(nodo)
                nodo = predecesores.get(nodo)
                if nodo is None:
                    break
            camino.append(router_actual_num_str)
            camino.reverse()
            
            if len(camino) > 1:
                siguiente_salto = camino[1]
                
                # Obtener next-hop IP correcta
                conn_key = (router_actual_num_str, siguiente_salto)
                if conn_key in conexiones_info:
                    conn_info = conexiones_info[conn_key]
                    next_hop_ip = conn_info['ip_r2']  # IP del siguiente salto
                    
                    ruta_cmd = f"ip route {red_info['net']} {convertir_mascara_prefijo_a_decimal(red_info['mask'])} {next_hop_ip}"
                    rutas_finales.add(ruta_cmd)
    
    return sorted(list(rutas_finales))

def calcular_distancia_dijkstra(origen, destino, grafo):
    """Calcula la distancia más corta entre dos nodos usando Dijkstra"""
    if origen == destino:
        return 0
    
    distancias = {nodo: float('infinity') for nodo in grafo}
    distancias[origen] = 0
    cola_prioridad = [(0, origen)]
    visitados = set()
    
    while cola_prioridad:
        distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)
        
        if nodo_actual in visitados:
            continue
        
        visitados.add(nodo_actual)
        
        if nodo_actual == destino:
            return distancia_actual
        
        for vecino, peso in grafo.get(nodo_actual, {}).items():
            distancia_nueva = distancia_actual + peso
            
            if distancia_nueva < distancias[vecino]:
                distancias[vecino] = distancia_nueva
                heapq.heappush(cola_prioridad, (distancia_nueva, vecino))
    
    return float('infinity')

def generar_rutas_estaticas_completas(router_actual_num, todas_las_conexiones, vlans_por_router, config_swc3):
    """Genera rutas estáticas usando BFS (algoritmo alternativo)"""
    rutas_finales = set()
    router_actual_num_str = str(router_actual_num)
    
    # Construir grafo
    grafo = {str(k): {} for k in vlans_por_router.keys()}
    for conn_str, conn_data in todas_las_conexiones.items():
        if isinstance(conn_data, dict):
            # Formato nuevo con IPs específicas
            net, mask = conn_data['red'], conn_data['mascara']
        else:
            # Formato antiguo para compatibilidad
            net, mask = conn_data
            
        r1, r2 = eval(conn_str)
        grafo[str(r1)][str(r2)] = 1
        grafo[str(r2)][str(r1)] = 1
    
    # Recopilar todas las redes
    todas_las_redes = []
    for r_owner_str, vlan_data in vlans_por_router.items():
        for vid, (net, mask) in vlan_data.items():
            todas_las_redes.append({'net': net, 'mask': mask, 'owner': r_owner_str})
    
    for conn_str, conn_data in todas_las_conexiones.items():
        if isinstance(conn_data, dict):
            # Formato nuevo con IPs específicas
            net, mask = conn_data['red'], conn_data['mascara']
        else:
            # Formato antiguo para compatibilidad
            net, mask = conn_data
            
        r1, r2 = eval(conn_str)
        todas_las_redes.append({'net': net, 'mask': mask, 'owner': str(r1)})
    
    for r_owner_str, data in config_swc3.items():
        net, mask = data['red_hacia_router']
        todas_las_redes.append({'net': net, 'mask': mask, 'owner': r_owner_str})
    
    # Identificar redes directas
    redes_directas = set()
    for net, mask in vlans_por_router.get(router_actual_num_str, {}).values():
        redes_directas.add(net)
    
    for conn_str, conn_data in todas_las_conexiones.items():
        if isinstance(conn_data, dict):
            # Formato nuevo con IPs específicas
            net = conn_data['red']
        else:
            # Formato antiguo para compatibilidad
            net, mask = conn_data
            
        if router_actual_num_str in conn_str:
            redes_directas.add(net)
    
    if router_actual_num_str in config_swc3:
        redes_directas.add(config_swc3[router_actual_num_str]['red_hacia_router'][0])
    
    # Generar rutas usando BFS
    for red_info in todas_las_redes:
        if red_info['net'] in redes_directas:
            continue
        
        destino_para_path = red_info['owner']
        cola = deque([(router_actual_num_str, [router_actual_num_str])])
        visitados = {router_actual_num_str}
        camino = None
        
        while cola:
            nodo, path = cola.popleft()
            if nodo == destino_para_path:
                camino = path
                break
            
            for vecino in grafo.get(nodo, {}):
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append((vecino, path + [vecino]))
        
        if camino and len(camino) > 1:
            siguiente_salto_router_str = camino[1]
            conexion_key = tuple(sorted((int(router_actual_num_str), int(siguiente_salto_router_str))))
            
            if str(conexion_key) in todas_las_conexiones:
                conn_data = todas_las_conexiones[str(conexion_key)]
                if isinstance(conn_data, dict):
                    # Formato nuevo con IPs específicas
                    red_conexion, mascara_conexion = conn_data['red'], conn_data['mascara']
                else:
                    # Formato antiguo para compatibilidad
                    red_conexion, mascara_conexion = conn_data
                    
                offset = -1 if int(router_actual_num_str) < int(siguiente_salto_router_str) else 0
                ip_siguiente_salto = obtener_ip_usable(red_conexion, mascara_conexion, offset)
                
                ruta_cmd = f"ip route {red_info['net']} {convertir_mascara_prefijo_a_decimal(red_info['mask'])} {ip_siguiente_salto}"
                rutas_finales.add(ruta_cmd)
    
    return sorted(list(rutas_finales))
