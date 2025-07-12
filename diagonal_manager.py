"""
Gestión de diagonales para asignación secuencial de IPs
Implementa "mejor ajuste" asignando primero redes más grandes (máscaras numéricamente mayores)
"""
import ipaddress
from collections import defaultdict

class DiagonalManager:
    """Maneja la asignación de IPs usando el sistema de diagonales secuencial"""
    
    def __init__(self, base_ip):
        self.base_ip = base_ip
        self.base_ip_int = int(ipaddress.IPv4Address(base_ip))
        
        # Sistema de dos fases: recopilación y asignación
        self.solicitudes_pendientes = []  # [(mascara, descripcion, id_solicitud)]
        self.combos_asignados = {}  # {id_solicitud: (red, mascara)}
        self.espacio_ocupado = []  # [(inicio, fin, mascara)] ordenado
        self.siguiente_id = 0
        self.fase_recopilacion = True
        
        print(f"Sistema secuencial inicializado con IP base: {base_ip}")
        
    def solicitar_combo(self, mascara, descripcion=""):
        """Solicita un combo - en fase de recopilación solo registra"""
        if self.fase_recopilacion:
            solicitud_id = self.siguiente_id
            self.solicitudes_pendientes.append((mascara, descripcion, solicitud_id))
            self.siguiente_id += 1
            print(f"Solicitud #{solicitud_id}: /{mascara} - {descripcion}")
            return solicitud_id
        else:
            raise Exception("Ya se completó la fase de asignación")
    
    def obtener_siguiente_combo(self, mascara):
        """
        Método de compatibilidad con el sistema anterior.
        Para el sistema secuencial, usa solicitar_combo() + procesar_asignaciones()
        """
        # Para mantener compatibilidad temporal, usar el algoritmo anterior
        if hasattr(self, 'combos_usados'):
            # Sistema anterior para compatibilidad inmediata
            return self._obtener_combo_antiguo(mascara)
        else:
            # Inicializar sistema anterior para compatibilidad
            self.combos_usados = {}
            self.puntero_por_mascara = {}
            return self._obtener_combo_antiguo(mascara)
    
    def _obtener_combo_antiguo(self, mascara):
        """Implementación del algoritmo anterior para compatibilidad"""
        if mascara not in self.puntero_por_mascara:
            self.puntero_por_mascara[mascara] = 1  # Empezar en el segundo combo
            self.combos_usados[mascara] = []
        
        tamano_combo = 2 ** (32 - mascara)
        combo_num = self.puntero_por_mascara[mascara]
        
        inicio_combo = self.base_ip_int + (combo_num * tamano_combo)
        red_combo = str(ipaddress.IPv4Address(inicio_combo))
        
        while self._hay_solapamiento_antiguo(inicio_combo, inicio_combo + tamano_combo - 1):
            combo_num += 1
            inicio_combo = self.base_ip_int + (combo_num * tamano_combo)
            red_combo = str(ipaddress.IPv4Address(inicio_combo))
        
        self.combos_usados[mascara].append(combo_num)
        self.puntero_por_mascara[mascara] = combo_num + 1
        
        return red_combo
    
    def _hay_solapamiento_antiguo(self, inicio, fin):
        """Verificación de solapamiento del sistema anterior"""
        for mascara, combos in self.combos_usados.items():
            tamano = 2 ** (32 - mascara)
            for combo_num in combos:
                combo_inicio = self.base_ip_int + (combo_num * tamano)
                combo_fin = combo_inicio + tamano - 1
                if not (fin < combo_inicio or inicio > combo_fin):
                    return True
        return False
    
    def procesar_asignaciones(self):
        """Procesa todas las solicitudes de manera secuencial optimizada"""
        if not self.fase_recopilacion:
            print("⚠️ Ya se procesaron las asignaciones")
            return
            
        print(f"\nPROCESANDO {len(self.solicitudes_pendientes)} SOLICITUDES SECUENCIALMENTE")
        print("=" * 70)
        
        # Mostrar resumen de solicitudes
        solicitudes_por_mascara = defaultdict(list)
        for mascara, desc, sol_id in self.solicitudes_pendientes:
            solicitudes_por_mascara[mascara].append((desc, sol_id))
        
        print("Solicitudes por mascara:")
        for mascara in sorted(solicitudes_por_mascara.keys(), reverse=True):
            cantidad = len(solicitudes_por_mascara[mascara])
            hosts = 2 ** (32 - mascara)
            print(f"   /{mascara}: {cantidad} solicitudes ({hosts} hosts cada una)")
        
        print("\nProcesando en orden: MASCARAS GRANDES -> PEQUENAS")
        print("=" * 70)
        
        # Ordenar por máscara (grandes primero: /30, /29, /28, ... /24, /23, etc.)
        solicitudes_ordenadas = sorted(self.solicitudes_pendientes, 
                                     key=lambda x: x[0], reverse=True)
        
        # Asignar secuencialmente
        for mascara, descripcion, solicitud_id in solicitudes_ordenadas:
            red_asignada = self._asignar_combo_optimizado(mascara)
            self.combos_asignados[solicitud_id] = (red_asignada, mascara)
            
            # Mostrar asignación
            red_obj = ipaddress.IPv4Network(f"{red_asignada}/{mascara}")
            fin_ip = str(red_obj.broadcast_address)
            print(f"   OK #{solicitud_id:2d}: {red_asignada} - {fin_ip} (/{mascara}) | {descripcion}")
        
        self.fase_recopilacion = False
        print(f"\nASIGNACION SECUENCIAL COMPLETADA")
        self._mostrar_resumen()
    
    def _asignar_combo_optimizado(self, mascara):
        """Asigna un combo de manera optimizada evitando fragmentación"""
        tamano_combo = 2 ** (32 - mascara)
        combo_num = 1  # Empezar desde el segundo combo
        
        while True:
            inicio_combo = self.base_ip_int + (combo_num * tamano_combo)
            fin_combo = inicio_combo + tamano_combo - 1
            
            if not self._hay_solapamiento(inicio_combo, fin_combo):
                red_combo = str(ipaddress.IPv4Address(inicio_combo))
                self._agregar_espacio_ocupado(inicio_combo, fin_combo, mascara)
                return red_combo
            
            combo_num += 1
    
    def _hay_solapamiento(self, inicio, fin):
        """Verifica solapamiento con rangos ya asignados"""
        for ocupado_inicio, ocupado_fin, _ in self.espacio_ocupado:
            if not (fin < ocupado_inicio or inicio > ocupado_fin):
                return True
        return False
    
    def _agregar_espacio_ocupado(self, inicio, fin, mascara):
        """Agrega un rango al espacio ocupado manteniendo orden"""
        self.espacio_ocupado.append((inicio, fin, mascara))
        self.espacio_ocupado.sort(key=lambda x: x[0])
    
    def obtener_combo_asignado(self, solicitud_id):
        """Obtiene la red asignada para una solicitud específica"""
        return self.combos_asignados.get(solicitud_id)
    
    def _mostrar_resumen(self):
        """Muestra resumen organizado por diagonal"""
        print("\nRESUMEN POR DIAGONAL:")
        print("=" * 70)
        
        # Agrupar por máscara
        por_mascara = defaultdict(list)
        for inicio, fin, mascara in self.espacio_ocupado:
            inicio_ip = str(ipaddress.IPv4Address(inicio))
            fin_ip = str(ipaddress.IPv4Address(fin))
            
            # Buscar descripción
            descripcion = "Desconocido"
            for sol_id, (red, mask) in self.combos_asignados.items():
                if red == inicio_ip and mask == mascara:
                    # Buscar en solicitudes originales
                    for m, desc, s_id in self.solicitudes_pendientes:
                        if s_id == sol_id:
                            descripcion = desc
                            break
                    break
            
            por_mascara[mascara].append((inicio_ip, fin_ip, descripcion))
        
        # Mostrar ordenado por máscara (grandes primero)
        for mascara in sorted(por_mascara.keys(), reverse=True):
            asignaciones = por_mascara[mascara]
            print(f"\nDIAGONAL /{mascara}:")
            for inicio, fin, desc in asignaciones:
                print(f"   {desc:25s} | {inicio} - {fin} (/{mascara})")
        
        print("=" * 70)
        print(f"Total asignado: {len(self.espacio_ocupado)} redes")
