import streamlit as st
import json
import os
import pandas as pd

def load_taxonomy_map():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    map_path = os.path.join(base_dir, "models", "taxonomy_mapping.json")
    
    if os.path.exists(map_path):
        with open(map_path, 'r', encoding='utf-8') as f:
            return json.load(f), map_path
    return {}, map_path

def save_taxonomy_map(data, path):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        return False

def render_taxonomy_manager():
    st.title("🏷️ Gestor de Taxonomía")
    st.markdown("""
    Aquí puedes personalizar cómo FORXIME/2 nombra a las especies. 
    - **Traducción**: Cambia el nombre científico a Español.
    - **Unificación**: Asigna el mismo nombre común a diferentes entradas científicas para agruparlas.
    """)
    
    current_map, map_path = load_taxonomy_map()
    
    if not current_map:
        st.error(f"No se encontró el archivo de mapeo en: {map_path}")
        return

    # Convert to DataFrame for editing
    data = []
    for k, v in current_map.items():
        data.append({"Clave Científica (Original)": k, "Nombre Común (Unificado)": v})
    
    df = pd.DataFrame(data)
    
    # Editor
    st.info("📝 Edita la columna 'Nombre Común' para traducir o unificar.")
    edited_df = st.data_editor(
        df, 
        width="stretch",
        num_rows="dynamic",
        column_config={
            "Clave Científica (Original)": st.column_config.TextColumn(disabled=False, help="Nombre científico en minúsculas (ej. panthera_onca)"),
            "Nombre Común (Unificado)": st.column_config.TextColumn(help="El nombre que aparecerá en los resultados")
        }
    )
    
    # Save Button
    if st.button("💾 Guardar Cambios"):
        new_map = {}
        for index, row in edited_df.iterrows():
            key = str(row["Clave Científica (Original)"]).strip()
            val = str(row["Nombre Común (Unificado)"]).strip()
            if key and val:
                new_map[key] = val
        
        if save_taxonomy_map(new_map, map_path):
            st.success("✅ Taxonomía actualizada correctamente. Los nuevos análisis usarán estos nombres.")
            # Force reload of engine implies restart or re-init, user needs to know
            st.warning("⚠️ Para que los cambios surtan efecto inmediato en tus reportes, por favor vuelve a 'Procesar Datos'.")
        else:
            st.error("Error al guardar el archivo.")

    # Add New Helper
    with st.expander("➕ Agregar Nueva Especie Manualmente"):
        c1, c2 = st.columns(2)
        new_k = c1.text_input("Clave Científica (ej. canis_latrans)")
        new_v = c2.text_input("Nombre Común (ej. Coyote)")
        if st.button("Agregar"):
            if new_k and new_v:
                current_map[new_k] = new_v
                save_taxonomy_map(current_map, map_path)
                st.rerun()
