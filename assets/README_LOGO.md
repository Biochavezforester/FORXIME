# Instrucciones para añadir tu logo a FORXIME/2

## Paso 1: Preparar tu logo

1. **Formato recomendado**: PNG con fondo transparente
2. **Dimensiones recomendadas**: 400x200 píxeles (ancho x alto)
3. **Nombre del archivo**: `logo.png` (o `logo.jpg`, `logo.svg`)

## Paso 2: Colocar el logo

Coloca tu archivo de logo en la carpeta:

```
FORXIME2/assets/logo.png
```

## Paso 3: El código ya está actualizado

El código en `app.py` ya está configurado para buscar tu logo en `assets/logo.png`.

Si tu logo tiene un nombre diferente o extensión diferente, actualiza la línea 86 en `app.py`:

```python
# Para PNG
st.image("assets/logo.png", use_container_width=True)

# Para JPG
st.image("assets/logo.jpg", use_container_width=True)

# Para SVG
st.image("assets/logo.svg", use_container_width=True)
```

## Paso 4: Subir a GitHub

Después de colocar tu logo, súbelo a GitHub:

```bash
git add assets/logo.png
git commit -m "Add: Logo de FORXIME/2"
git push origin main
```

## Alternativa: Usar URL externa

Si prefieres usar una URL de imagen externa (ej: desde tu sitio web):

```python
st.image("https://tu-sitio.com/logo.png", use_container_width=True)
```

## Notas importantes

- El logo aparecerá en el **sidebar** (barra lateral) de la aplicación
- Se ajustará automáticamente al ancho del sidebar
- Formatos soportados: PNG, JPG, JPEG, SVG, GIF
- Para mejor calidad, usa PNG con fondo transparente
