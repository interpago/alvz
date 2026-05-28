# 📖 Glosario de Palabras Reservadas

Para dominar Alvz, es fundamental saber qué palabras "pertenecen" al lenguaje y no puedes usar como nombres de variables.

## 1. Estructuras de Control (Lógica)
Estas palabras definen el flujo de tu programa:
- `si`: Inicia una condición.
- `sino`: Define qué hacer si la condición no se cumple.
- `mientras`: Inicia un bucle basado en una condición.
- `para`: Inicia un bucle basado en un rango numérico.
- `cada`: Inicia un bucle para recorrer elementos de una lista.
- `retornar`: Devuelve un valor desde una función.

## 2. Conectores (Gramática)
Son palabras que ayudan a que el código se lea como una oración:
- `de`: Indica el inicio de un rango (ej: `para i de 1 ...`).
- `a`: Indica el fin de un rango (ej: `... a 10`).
- `en`: Indica sobre qué lista estamos iterando (ej: `cada x en lista`).

## 3. Definiciones
- `variable`: Para crear un nuevo espacio de memoria.
- `funcion`: Para agrupar código reutilizable.
- `clase`: Para crear plantillas de objetos.
- `nuevo`: Para crear una instancia de una clase.
- `importar`: Para traer código de otros archivos.

## 4. Valores Especiales
- `verdadero` / `falso`: Valores lógicos (booleanos).
- `y` / `o`: Operadores lógicos para combinar condiciones.

---
### 💡 Un truco para identificar palabras reservadas:
En VS Code, gracias a nuestra extensión, las palabras reservadas siempre cambiarán de color (generalmente a amarillo o púrpura, dependiendo de tu tema). Si escribes una palabra y se queda blanca, ¡es una variable que tú has creado!
