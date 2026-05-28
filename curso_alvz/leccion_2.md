# Lección 2: Lógica y Control de Flujo

Aprenderás a que tu programa tome decisiones y repita tareas.

## 1. Condicionales (si / sino)
La estructura `si` evalúa una condición.

```alvz
variable edad = 20

si edad >= 18 {
    imprimir("Acceso concedido")
} sino {
    imprimir("Acceso denegado")
}
```

## 2. El Bucle Mientras
Repite código mientras una condición sea verdadera.

```alvz
variable contador = 1
mientras contador <= 3 {
    imprimir("Contando: " + contador)
    contador = contador + 1
}
```

## 3. El Bucle Para (Rangos)
Ideal para contar de forma sencilla.

```alvz
para i de 1 a 5 {
    imprimir("Número: " + i)
}
```

---
### 🛠️ Reto de la Lección 2:
Crea un programa que imprima solo los números PARES del 1 al 10 usando un bucle `para`.
(Pista: usa el operador módulo `%` para saber si un número es par: `si i % 2 == 0`)
