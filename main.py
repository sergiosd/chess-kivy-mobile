from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.window import Window

# Simulamos la proporción de una pantalla de teléfono móvil para el entorno de PC
Window.size = (450, 800)

# El diseño declarativo (KV) integrado.
# Usamos BoxLayouts para evitar que ningún texto pise el área de juego jamás.
Builder.load_string("""
<Casilla@RelativeLayout>:
    ruta_fondo: ''
    ruta_pieza: ''
    
    Image:
        source: root.ruta_fondo
        allow_stretch: True
        keep_ratio: False
        
    Image:
        source: root.ruta_pieza
        opacity: 1 if root.ruta_pieza else 0
        allow_stretch: True
        keep_ratio: True
        size_hint: 0.85, 0.85
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

<VistaTablero>:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(20)

    # Fondo general de la aplicación
    canvas.before:
        Color:
            rgba: 0.1, 0.15, 0.2, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # Zona Superior: Título
    Label:
        text: 'SALA DE MANDO'
        font_size: '28sp'
        bold: True
        size_hint_y: 0.15
        color: 0, 0.9, 0.8, 1

    # Zona Central: El Tablero
    AnchorLayout:
        size_hint_y: 0.6
        GridLayout:
            id: cuadricula_tablero
            cols: 8
            rows: 8
            size_hint: None, None
            # Aseguramos que sea un cuadrado perfecto basado en el ancho disponible
            width: min(root.width - dp(40), root.height * 0.6)
            height: self.width

    # Zona Inferior: Información (Imposible que solape al tablero gracias al BoxLayout)
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 0.25
        Label:
            text: 'Despliegue activo'
            font_size: '22sp'
            bold: True
            color: 0.9, 0.9, 0.9, 1
        Label:
            text: 'ELO: 1008 | ID: 00207'
            font_size: '18sp'
            color: 0.7, 0.7, 0.8, 1
""")


class Casilla(RelativeLayout):
    """Componente que representa una única casilla del tablero."""
    pass


class VistaTablero(BoxLayout):
    """Controlador principal de la vista."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dibujar_tablero_demostracion()

    def dibujar_tablero_demostracion(self):
        cuadricula = self.ids.cuadricula_tablero

        # Generamos las 64 casillas
        for i in range(64):
            fila = i // 8
            columna = i % 8

            # Lógica matemática básica para alternar colores
            es_clara = (fila + columna) % 2 == 0
            fondo = "assets/squares/casilla_clara.png" if es_clara else "assets/squares/casilla_oscura.png"

            # Vamos a colocar tu famoso caballo negro indexado en algunas casillas
            # para demostrar que Kivy respeta la transparencia sin despeinarse
            pieza = ""
            if i in [10, 21, 36, 45]:
                pieza = "assets/pieces/negro_caballo.png"

            # Instanciamos la casilla y le pasamos los PNG
            casilla_widget = Casilla()
            casilla_widget.ruta_fondo = fondo
            casilla_widget.ruta_pieza = pieza

            cuadricula.add_widget(casilla_widget)


class ChessApp(App):
    def build(self):
        return VistaTablero()


if __name__ == '__main__':
    ChessApp().run()