# Lección 3: Funciones y Listas

Organiza tu código y maneja grupos de datos.

## 1. Funciones
Usa `funcion` para agrupar lógica y `retornar` para devolver resultados.

```alvz
funcion saludar(nombre) {
    retornar "Hola, " + nombre + "!"
}

variable mensaje = saludar("Usuario")
imprimir(mensaje)
```

## 2. Listas y el bucle Cada
Las listas guardan múltiples elementos. `cada` es la forma más fácil de recorrerlas.

```alvz
variable frutas = ["Manzana", "Pera", "Uva"]
agregar(frutas, "Mango")

cada f en frutas {
    imprimir("Fruta: " + f)
}
```

---
### 🛠️ Reto de la Lección 3:
Crea una función llamada `promedio` que reciba una lista de números y retorne el promedio.
(Pista: usa `longitud(lista)` para saber cuántos elementos hay).
