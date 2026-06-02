"""Tests para el formateador de codigo Alvz."""

import pytest
from alvz.core.formatter import formatear, _tokenize


def test_formatear_funcion_simple():
    codigo = 'funcion saludar(){imprimir("hola")}'
    esperado = 'funcion saludar() {\n\timprimir("hola")\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_variable_y_asignacion():
    codigo = 'variable x=10'
    esperado = 'variable x = 10\n'
    assert formatear(codigo) == esperado


def test_formatear_si_condicional():
    codigo = 'si(x>5){imprimir("mayor")}'
    esperado = 'si(x > 5) {\n\timprimir("mayor")\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_mientras():
    codigo = 'mientras(x<10){imprimir(x)\nx=x+1}'
    esperado = 'mientras(x < 10) {\n\timprimir(x)\n\tx = x + 1\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_para():
    codigo = 'para i=1 a 10{imprimir(i)}'
    esperado = 'para i = 1 a 10 {\n\timprimir(i)\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_comentarios():
    codigo = '# esto es un comentario\nvariable x = 1 # inline'
    esperado = '# esto es un comentario\nvariable x = 1\n# inline\n'
    assert formatear(codigo) == esperado


def test_formatear_string_con_llaves():
    """Los strings con {} no deben romper indentacion."""
    codigo = 'variable msg = "hola {mundo}"'
    esperado = 'variable msg = "hola {mundo}"\n'
    assert formatear(codigo) == esperado


def test_formatear_operadores():
    codigo = 'variable r= a+b*c-d/e%f'
    esperado = 'variable r = a + b * c - d / e % f\n'
    assert formatear(codigo) == esperado


def test_formatear_comparaciones():
    codigo = 'si(a>=b y c!=d o e==f){}'
    esperado = 'si(a >= b y c != d o e == f) {\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_lista():
    codigo = 'variable lst=[1,2,3]'
    esperado = 'variable lst = [1, 2, 3]\n'
    assert formatear(codigo) == esperado


def test_formatear_diccionario():
    codigo = 'variable d={"a":1,"b":2}'
    esperado = 'variable d = {\n\t"a": 1, "b": 2\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_anidado():
    codigo = 'si(a>0){si(b>0){imprimir("ambos")}}'
    esperado = 'si(a > 0) {\n\tsi(b > 0) {\n\t\timprimir("ambos")\n\t}\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_clase():
    codigo = 'clase Persona{propiedad nombre\nfuncion saludar(){imprimir("hola")}}'
    esperado = 'clase Persona {\n\tpropiedad nombre\n\tfuncion saludar() {\n\t\timprimir("hola")\n\t}\n}\n'
    assert formatear(codigo) == esperado


def test_tokenize_string_triple():
    codigo = '"""texto largo"""'
    tokens = _tokenize(codigo)
    assert any(k == 'STRING_TRIPLE' for k, _, _ in tokens)


def test_tokenize_comentario():
    tokens = _tokenize('# comentario\n')
    assert any(k == 'COMENTARIO' for k, _, _ in tokens)


def test_tokenize_error():
    with pytest.raises(RuntimeError, match='Caracter inesperado'):
        _tokenize('variable x = @')


def test_formatear_llamada_metodo():
    codigo = 'objeto.metodo(1,2)'
    esperado = 'objeto.metodo(1, 2)\n'
    assert formatear(codigo) == esperado


def test_formatear_retornar():
    codigo = 'funcion suma(a,b){retornar a+b}'
    esperado = 'funcion suma(a, b) {\n\tretornar a + b\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_sino():
    codigo = 'si(x){a} sino {b}'
    esperado = 'si(x) {\n\ta\n} sino {\n\tb\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_vacio():
    assert formatear('') == '\n'
    assert formatear('   ') == '\n'
    assert formatear('\n\n\n') == '\n'


def test_formatear_cada():
    codigo = 'cada elem en lista{imprimir(elem)}'
    esperado = 'cada elem en lista {\n\timprimir(elem)\n}\n'
    assert formatear(codigo) == esperado


def test_formatear_operadores_asignacion():
    codigo = 'x+=1\ny-=2\nz*=3\nw/=4\nv%=5'
    esperado = 'x += 1\ny -= 2\nz *= 3\nw /= 4\nv %= 5\n'
    assert formatear(codigo) == esperado
