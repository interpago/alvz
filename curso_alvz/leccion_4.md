# Lección 4: Objetos (POO)

Alvz te permite crear tus propios tipos de objetos usando `clase`.

## 1. Definir una Clase
Las clases pueden tener variables (propiedades) y funciones (métodos).

```alvz
clase Mascota {
    variable nombre = ""
    variable especie = ""

    funcion hablar(esto) {
        imprimir(esto.nombre + " dice ¡Hola!")
    }
}

variable mi_perro = nuevo Mascota()
mi_perro.nombre = "Firulais"
mi_perro.hablar()
```

## 2. Herencia
Puedes crear clases que hereden de otras.

```alvz
clase Perro de Animal {
    # Hereda todo lo de Animal
}
```

---
### 🛠️ Reto de la Lección 4:
Crea una clase `CuentaBancaria` con una variable `saldo` y dos funciones: `depositar(monto)` y `retirar(monto)`. Prueba creando una instancia y realizando operaciones.
