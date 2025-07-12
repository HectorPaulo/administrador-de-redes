#!/usr/bin/env python3
"""
GENERADOR DE CONFIGURACIONES CISCO  
Versión Modular

Este es el archivo principal que integra todos los módulos del sistema.
"""

# Importar todos los módulos necesarios
from config import *
from validaciones import validar_entrada
from session_manager import guardar_sesion, cargar_sesion, revertir_paso_router, generar_archivo_final
from session_init import iniciar_nueva_sesion, verificar_compatibilidad_sesion
from router_config import configurar_router_individual

def main():
    """Función principal del programa"""
    print("=" * 70)
    print("GENERADOR DE CONFIGURACIONES CISCO")
    print("=" * 70)
    
    estado = None
    nombre_sesion_json = ""
    
    # Cargar o crear sesión
    if validar_entrada("¿Deseas cargar una sesion existente? (s/n): ", "si_no"):
        nombre_sesion = validar_entrada("Introduce el nombre de la sesion a cargar: ")
        nombre_sesion_json = f"{nombre_sesion}.json"
        estado = cargar_sesion(nombre_sesion_json)
        
        if not estado:
            print("No se pudo cargar la sesion. Saliendo.")
            return
    else:
        estado = iniciar_nueva_sesion()
        if not estado:
            return
        
        nombre_sesion_json = f"{estado['nombre_sesion']}.json"
        guardar_sesion(nombre_sesion_json, estado)
        print(f"Sesion inicial '{nombre_sesion_json}' creada.")
    
    # Verificar compatibilidad de sesiones antiguas
    estado, conexiones_convertidas = verificar_compatibilidad_sesion(estado)
    if conexiones_convertidas:
        guardar_sesion(nombre_sesion_json, estado)
    
    # Extraer datos principales
    datos_iniciales = estado["datos_iniciales"]
    num_routers = datos_iniciales["num_routers"]
    
    # Determinar rango de routers a configurar
    rango_inicio = estado["ultimo_paso_completado"] + 1
    
    # Manejar continuación o edición
    if estado["ultimo_paso_completado"] > 0 and estado["ultimo_paso_completado"] < num_routers:
        accion = validar_entrada(
            f"\nUltimo paso completado fue R{estado['ultimo_paso_completado']}. "
            "¿Deseas (C)ontinuar o (E)ditar el ultimo paso?: ",
            "texto",
            ['c', 'e']
        ).lower()
        
        if accion == 'e':
            r_a_revertir = estado["ultimo_paso_completado"]
            estado = revertir_paso_router(estado, r_a_revertir)
            rango_inicio = r_a_revertir
    
    # Configurar routers uno por uno
    for r_num in range(rango_inicio, num_routers + 1):
        estado = configurar_router_individual(r_num, estado, nombre_sesion_json)
    
    # Generar archivo final
    nombre_archivo_final = f"{estado['nombre_sesion']}_config.cisco"
    generar_archivo_final(estado, nombre_archivo_final)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()
