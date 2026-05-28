# Lección 5: FastAPI y Supabase (Nivel Pro)

¡El poder real de Alvz! Conecta tu app al mundo.

## 1. Crear una API con FastAPI
Configura rutas y lanza un servidor en un puerto.

```alvz
funcion inicio() {
    retornar {"mensaje": "Bienvenido a mi API"}
}

variable rutas = {
    "/": "inicio"
}

iniciar_servidor(8000, rutas)
```

## 2. Supabase (Base de Datos)
Guarda y consulta datos en la nube.

```alvz
variable url = "https://tu-url.supabase.co"
variable key = "tu-anon-key"

# Consultar una tabla llamada 'usuarios'
variable datos = supabase_consultar(url, key, "usuarios")
imprimir(datos)
```

---
### 🛠️ Reto Final:
Crea una API que tenga una ruta `/usuarios` que al consultarla devuelva los datos obtenidos desde Supabase. ¡Has dominado Alvz!
