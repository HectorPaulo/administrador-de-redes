"""
Gestión de sesiones: guardar, cargar y utilidades para el generador de comandos de red
"""
import json
import os

def guardar_sesion(nombre_sesion_json, estado):
    """Guarda el estado de la sesión en un archivo JSON"""
    with open(nombre_sesion_json, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)

def cargar_sesion(nombre_sesion_json):
    """Carga el estado de la sesión desde un archivo JSON"""
    try:
        with open(nombre_sesion_json, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error al cargar la sesión: {e}")
        return None

def revertir_paso_router(estado, router_num):
    """Revierte la configuración de un router específico en la sesión"""
    progreso = estado["progreso_routers"]
    for key in ["comandos_router", "comandos_switches"]:
        if key in progreso and str(router_num) in progreso[key]:
            del progreso[key][str(router_num)]
    estado["ultimo_paso_completado"] = router_num - 1
    print(f"\n🔄 Paso revertido. Listo para reconfigurar R{router_num}.")
    return estado

def generar_archivo_final(estado, nombre_archivo_final):
    """Genera el archivo final de configuración Cisco"""
    progreso = estado["progreso_routers"]
    with open(nombre_archivo_final, "w", encoding="utf-8") as f:
        for r_num, comandos in progreso.get("comandos_router", {}).items():
            f.write(f"! Configuración Router R{r_num}\n")
            f.write("\n".join(comandos))
            f.write("\n\n")
        for r_num, switches in progreso.get("comandos_switches", {}).items():
            for sw_name, sw_cmds in switches.items():
                f.write(f"! Configuración Switch {sw_name}\n")
                f.write("\n".join(sw_cmds))
                f.write("\n\n")
    print(f"\n✅ Archivo final '{nombre_archivo_final}' generado correctamente.")
