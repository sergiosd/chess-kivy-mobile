"""Widgets de texto adaptativo comunes para toda la interfaz."""

from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


class BotonTextoAdaptativo(Button):
    """Reduce la fuente solo cuando el texto no cabe dentro del botón."""

    font_size_min = NumericProperty(sp(7))
    font_size_max = NumericProperty(0)
    proporcion_altura_fuente = NumericProperty(0.38)
    margen_horizontal = NumericProperty(dp(6))
    margen_vertical = NumericProperty(dp(4))

    def __init__(self, **kwargs) -> None:
        """Configura el reajuste automático conservando el tamaño máximo diseñado."""
        self._evento_ajuste = None
        self._font_size_referencia = None
        super().__init__(**kwargs)
        self.bind(
            size=self._programar_ajuste,
            text=self._programar_ajuste,
            font_name=self._programar_ajuste,
            bold=self._programar_ajuste,
            italic=self._programar_ajuste,
            font_size_min=self._programar_ajuste,
            font_size_max=self._programar_ajuste,
            proporcion_altura_fuente=self._programar_ajuste,
            margen_horizontal=self._programar_ajuste,
            margen_vertical=self._programar_ajuste,
        )
        self._programar_ajuste()

    def on_kv_post(self, base_widget) -> None:
        """Captura como máximo el tamaño definido por KV y reajusta el widget."""
        super().on_kv_post(base_widget)
        if self.font_size_max <= 0:
            self._font_size_referencia = float(self.font_size)
        self._programar_ajuste()

    def _programar_ajuste(self, *_args) -> None:
        """Agrupa cambios de layout para recalcular una sola vez por frame."""
        if self._evento_ajuste is not None:
            self._evento_ajuste.cancel()
        self._evento_ajuste = Clock.schedule_once(self._ajustar_fuente, 0)

    def _obtener_maximo(self) -> float:
        """Devuelve el tamaño máximo respetando el diseño original."""
        if self.font_size_max > 0:
            return float(self.font_size_max)
        if self._font_size_referencia is None:
            self._font_size_referencia = float(self.font_size)
        return self._font_size_referencia

    def _medir_texto(self, tamano_fuente: float) -> tuple[float, float]:
        """Devuelve el tamaño natural del texto para una fuente concreta."""
        etiqueta = CoreLabel(
            text=self.text,
            font_name=self.font_name,
            font_size=tamano_fuente,
            bold=self.bold,
            italic=self.italic,
        )
        etiqueta.refresh()
        return etiqueta.texture.size

    def _ajustar_fuente(self, _dt: float) -> None:
        """Busca el mayor tamaño que cabe dentro del botón."""
        self._evento_ajuste = None
        if not self.text or self.width <= 0 or self.height <= 0:
            return

        ancho_disponible = max(1.0, self.width - 2 * self.margen_horizontal)
        alto_disponible = max(1.0, self.height - 2 * self.margen_vertical)
        maximo = min(
            self._obtener_maximo(),
            max(1.0, self.height * self.proporcion_altura_fuente),
        )
        minimo = min(float(self.font_size_min), maximo)

        ancho, alto = self._medir_texto(maximo)
        if ancho <= ancho_disponible and alto <= alto_disponible:
            self.font_size = maximo
            return

        bajo = minimo
        ancho_minimo, alto_minimo = self._medir_texto(minimo)
        if ancho_minimo > ancho_disponible or alto_minimo > alto_disponible:
            bajo = 1.0

        mejor = bajo
        alto_busqueda = maximo
        for _ in range(10):
            candidato = (bajo + alto_busqueda) / 2.0
            ancho, alto = self._medir_texto(candidato)
            if ancho <= ancho_disponible and alto <= alto_disponible:
                mejor = candidato
                bajo = candidato
            else:
                alto_busqueda = candidato

        self.font_size = mejor


class TextoAdaptativo(Label):
    """Mantiene el tamaño diseñado y lo reduce cuando el texto desborda su caja."""

    font_size_min = NumericProperty(sp(6))
    font_size_max = NumericProperty(0)
    margen_horizontal = NumericProperty(dp(2))
    margen_vertical = NumericProperty(dp(2))

    def __init__(self, **kwargs) -> None:
        """Configura el reajuste automático para cambios de texto y geometría."""
        self._evento_ajuste = None
        self._font_size_referencia = None
        self._ajustando_fuente = False
        super().__init__(**kwargs)
        self.bind(
            size=self._programar_ajuste,
            text=self._programar_ajuste,
            font_name=self._programar_ajuste,
            bold=self._programar_ajuste,
            italic=self._programar_ajuste,
            markup=self._programar_ajuste,
            font_size_min=self._programar_ajuste,
            font_size_max=self._programar_ajuste,
            margen_horizontal=self._programar_ajuste,
            margen_vertical=self._programar_ajuste,
        )
        self._programar_ajuste()

    def on_kv_post(self, base_widget) -> None:
        """Captura como máximo el tamaño definido por KV y reajusta el texto."""
        super().on_kv_post(base_widget)
        if self.font_size_max <= 0:
            self._font_size_referencia = float(self.font_size)
        self._programar_ajuste()

    def _programar_ajuste(self, *_args) -> None:
        """Agrupa cambios para evitar trabajo redundante."""
        if self._ajustando_fuente:
            return
        if self._evento_ajuste is not None:
            self._evento_ajuste.cancel()
        self._evento_ajuste = Clock.schedule_once(self._ajustar_fuente, 0)

    def _obtener_maximo(self) -> float:
        """Devuelve el tamaño máximo original del widget."""
        if self.font_size_max > 0:
            return float(self.font_size_max)
        if self._font_size_referencia is None:
            self._font_size_referencia = float(self.font_size)
        return self._font_size_referencia

    def _medir_texto(
        self,
        tamano_fuente: float,
        ancho_disponible: float,
    ) -> tuple[float, float]:
        """Mide el texto real, incluido markup y el salto de línea configurado."""
        fuente_original = self.font_size
        text_size_original = self.text_size
        envolver = bool(
            text_size_original
            and len(text_size_original) >= 1
            and text_size_original[0] is not None
        )

        self._ajustando_fuente = True
        try:
            self.font_size = tamano_fuente
            self.text_size = (
                (ancho_disponible, None)
                if envolver
                else (None, None)
            )
            self.texture_update()
            return tuple(self.texture_size)
        finally:
            self.font_size = fuente_original
            self.text_size = text_size_original
            self.texture_update()
            self._ajustando_fuente = False

    def _ajustar_fuente(self, _dt: float) -> None:
        """Busca el mayor tamaño que cabe dentro del área real del texto."""
        self._evento_ajuste = None
        if not self.text or self.width <= 0 or self.height <= 0:
            return

        ancho_disponible = max(1.0, self.width - 2 * self.margen_horizontal)
        alto_disponible = max(1.0, self.height - 2 * self.margen_vertical)
        maximo = self._obtener_maximo()
        minimo = min(float(self.font_size_min), maximo)

        ancho, alto = self._medir_texto(maximo, ancho_disponible)
        if ancho <= ancho_disponible and alto <= alto_disponible:
            self.font_size = maximo
            return

        bajo = minimo
        ancho_minimo, alto_minimo = self._medir_texto(
            minimo,
            ancho_disponible,
        )
        if ancho_minimo > ancho_disponible or alto_minimo > alto_disponible:
            bajo = 1.0

        mejor = bajo
        alto_busqueda = maximo
        for _ in range(10):
            candidato = (bajo + alto_busqueda) / 2.0
            ancho, alto = self._medir_texto(candidato, ancho_disponible)
            if ancho <= ancho_disponible and alto <= alto_disponible:
                mejor = candidato
                bajo = candidato
            else:
                alto_busqueda = candidato

        self.font_size = mejor



class EntradaTextoAdaptativa(TextInput):
    """Adapta la fuente del texto o placeholder al ancho y alto disponibles."""

    font_size_min = NumericProperty(sp(7))
    font_size_max = NumericProperty(0)
    margen_horizontal = NumericProperty(dp(8))
    margen_vertical = NumericProperty(dp(4))

    def __init__(self, **kwargs) -> None:
        """Configura el reajuste automático de entradas de texto."""
        self._evento_ajuste = None
        self._font_size_referencia = None
        super().__init__(**kwargs)
        self.bind(
            size=self._programar_ajuste,
            text=self._programar_ajuste,
            hint_text=self._programar_ajuste,
            font_name=self._programar_ajuste,
            font_size_min=self._programar_ajuste,
            font_size_max=self._programar_ajuste,
        )
        self._programar_ajuste()

    def on_kv_post(self, base_widget) -> None:
        """Captura como máximo el tamaño configurado por KV."""
        super().on_kv_post(base_widget)
        if self.font_size_max <= 0:
            self._font_size_referencia = float(self.font_size)
        self._programar_ajuste()

    def _programar_ajuste(self, *_args) -> None:
        """Agrupa cambios para recalcular una vez por frame."""
        if self._evento_ajuste is not None:
            self._evento_ajuste.cancel()
        self._evento_ajuste = Clock.schedule_once(self._ajustar_fuente, 0)

    def _obtener_maximo(self) -> float:
        """Devuelve el tamaño máximo original del campo."""
        if self.font_size_max > 0:
            return float(self.font_size_max)
        if self._font_size_referencia is None:
            self._font_size_referencia = float(self.font_size)
        return self._font_size_referencia

    def _medir_texto(self, tamano_fuente: float) -> tuple[float, float]:
        """Mide el texto visible o, si está vacío, el placeholder."""
        contenido = self.text if self.text else self.hint_text
        etiqueta = CoreLabel(
            text=contenido,
            font_name=self.font_name,
            font_size=tamano_fuente,
        )
        etiqueta.refresh()
        return etiqueta.texture.size

    def _ajustar_fuente(self, _dt: float) -> None:
        """Reduce la fuente cuando el contenido no cabe en una línea."""
        self._evento_ajuste = None
        contenido = self.text if self.text else self.hint_text
        if not contenido or self.width <= 0 or self.height <= 0:
            return

        ancho_disponible = max(1.0, self.width - 2 * self.margen_horizontal)
        alto_disponible = max(1.0, self.height - 2 * self.margen_vertical)
        maximo = self._obtener_maximo()
        minimo = min(float(self.font_size_min), maximo)

        ancho, alto = self._medir_texto(maximo)
        if ancho <= ancho_disponible and alto <= alto_disponible:
            self.font_size = maximo
            return

        bajo = minimo
        ancho_minimo, alto_minimo = self._medir_texto(minimo)
        if ancho_minimo > ancho_disponible or alto_minimo > alto_disponible:
            bajo = 1.0

        mejor = bajo
        alto_busqueda = maximo
        for _ in range(10):
            candidato = (bajo + alto_busqueda) / 2.0
            ancho, alto = self._medir_texto(candidato)
            if ancho <= ancho_disponible and alto <= alto_disponible:
                mejor = candidato
                bajo = candidato
            else:
                alto_busqueda = candidato

        self.font_size = mejor


class PopupTextoAdaptativo(Popup):
    """Adapta el tamaño del título del popup al ancho disponible."""

    title_font_size_min = NumericProperty(sp(8))
    title_margen_horizontal = NumericProperty(dp(24))

    def __init__(self, **kwargs) -> None:
        """Configura el reajuste automático del título."""
        self._evento_ajuste_titulo = None
        self._title_font_size_referencia = None
        self._ajustando_titulo = False
        super().__init__(**kwargs)
        self.bind(
            size=self._programar_ajuste_titulo,
            title=self._programar_ajuste_titulo,
        )
        self._programar_ajuste_titulo()

    def on_kv_post(self, base_widget) -> None:
        """Captura el tamaño máximo de título definido por KV."""
        super().on_kv_post(base_widget)
        self._title_font_size_referencia = float(self.title_font_size)
        self._programar_ajuste_titulo()

    def _programar_ajuste_titulo(self, *_args) -> None:
        """Agrupa cambios para recalcular el título una vez por frame."""
        if self._ajustando_titulo:
            return
        if self._evento_ajuste_titulo is not None:
            self._evento_ajuste_titulo.cancel()
        self._evento_ajuste_titulo = Clock.schedule_once(
            self._ajustar_titulo,
            0,
        )

    def _medir_titulo(self, tamano_fuente: float) -> tuple[float, float]:
        """Mide el título usando la fuente real del Popup."""
        etiqueta = CoreLabel(
            text=self.title,
            font_name=self.title_font,
            font_size=tamano_fuente,
        )
        etiqueta.refresh()
        return etiqueta.texture.size

    def _ajustar_titulo(self, _dt: float) -> None:
        """Busca el mayor tamaño de título que cabe en el Popup."""
        self._evento_ajuste_titulo = None
        if not self.title or self.width <= 0:
            return

        maximo = (
            self._title_font_size_referencia
            if self._title_font_size_referencia is not None
            else float(self.title_font_size)
        )
        minimo = min(float(self.title_font_size_min), maximo)
        ancho_disponible = max(
            1.0,
            self.width - 2 * self.title_margen_horizontal,
        )

        ancho, _alto = self._medir_titulo(maximo)
        if ancho <= ancho_disponible:
            self._ajustando_titulo = True
            self.title_font_size = maximo
            self._ajustando_titulo = False
            return

        bajo = minimo
        ancho_minimo, _alto_minimo = self._medir_titulo(minimo)
        if ancho_minimo > ancho_disponible:
            bajo = 1.0

        mejor = bajo
        alto_busqueda = maximo
        for _ in range(10):
            candidato = (bajo + alto_busqueda) / 2.0
            ancho, _alto = self._medir_titulo(candidato)
            if ancho <= ancho_disponible:
                mejor = candidato
                bajo = candidato
            else:
                alto_busqueda = candidato

        self._ajustando_titulo = True
        self.title_font_size = mejor
        self._ajustando_titulo = False
