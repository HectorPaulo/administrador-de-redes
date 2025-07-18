"""
Configuración y flujo principal para la configuración de routers
"""
from router_commands import (
    generar_comandos_router_ROAS,
    generar_comandos_router_para_swc3,
    generar_comandos_router_con_wlc
)
from switch_commands import (
    generar_comandos_switches_acceso_con_wlc
)
from config import ERROR_MESSAGES

def configurar_router_individual(router_num, estado, nombre_sesion_json):
    """Configura un router individual y actualiza el estado"""
    # Extraer datos relevantes
    datos_iniciales = estado["datos_iniciales"]
    progreso = estado["progreso_routers"]
    modo_config = int(datos_iniciales["modo_config"])
    vlans_por_router = progreso["vlans_por_router"]
    conexiones_por_router = progreso["conexiones_por_router"]
    l2_config_por_router = progreso["l2_config_por_router"]
    todas_las_conexiones = progreso["todas_las_conexiones"]
    config_swc3 = progreso["config_swc3"]
    config_wlc = progreso["config_wlc"]
    topologia_switches = progreso.get("topologia_switches", {})

    # Determinar tipo de configuración (ROAS, SWC3, WLC)
    vlans_asignadas = vlans_por_router.get(str(router_num), {})
    conexiones = conexiones_por_router.get(str(router_num), {})
    l2_config = l2_config_por_router.get(str(router_num), {})
    conectado_a_swc3 = str(router_num) in config_swc3
    tiene_wlc = str(router_num) in config_wlc

    comandos_router = []
    comandos_switches = {}

    if tiene_wlc:
        wlc_config = config_wlc[str(router_num)]
        comandos_router = generar_comandos_router_con_wlc(
            router_num, vlans_asignadas, conexiones, wlc_config,
            todas_las_conexiones, vlans_por_router, config_swc3
        )
        # Generar comandos para switches con WLC
        mgmt_combo = None  # Aquí podrías pasar la red de gestión si aplica
        comandos_switches = generar_comandos_switches_acceso_con_wlc(
            router_num, vlans_asignadas, wlc_config,
            topologia_switches, mgmt_combo,
            modo_config=modo_config
        )
    elif conectado_a_swc3:
        swc3_config = config_swc3[str(router_num)]
        progreso_actual = {"config_swc3": config_swc3}
        comandos_router = generar_comandos_router_para_swc3(
            router_num, conexiones, swc3_config, modo_config,
            todas_las_conexiones, vlans_por_router, progreso_actual
        )
        # Aquí podrías agregar comandos para switches si aplica
    else:
        comandos_router = generar_comandos_router_ROAS(
            router_num, vlans_asignadas, conexiones, modo_config,
            todas_las_conexiones, vlans_por_router, config_swc3, l2_config
        )
        # Aquí podrías agregar comandos para switches si aplica

    # Guardar los comandos generados en el estado
    progreso.setdefault("comandos_router", {})[str(router_num)] = comandos_router
    progreso.setdefault("comandos_switches", {})[str(router_num)] = comandos_switches
    estado["ultimo_paso_completado"] = router_num

    # Aquí podrías guardar la sesión si es necesario
    from session_manager import guardar_sesion
    guardar_sesion(nombre_sesion_json, estado)

    print(f"\n✅ Configuración de R{router_num} completada y guardada.")
    return estado

def revertir_paso_router(estado, router_num):
    """Revierte la configuración de un router específico"""
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

def guardar_sesion(nombre_sesion_json, estado):
    """Guarda el estado de la sesión en un archivo JSON"""
    import json
    with open(nombre_sesion_json, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)

def cargar_sesion(nombre_sesion_json):
    """Carga el estado de la sesión desde un archivo JSON"""
    import json
    try:
        with open(nombre_sesion_json, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error al cargar la sesión: {e}")
        return None

