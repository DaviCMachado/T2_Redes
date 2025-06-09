from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Rectangle
from kivy.app import App
import os


class TelaMenuInicial(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()

        self.graficos = []  # Lista para armazenar os gráficos gerados
        self.indice_atual = 0  # Índice atual do gráfico exibido

        btn_gerar = Button(text="Métricas", size_hint=(0.4, 0.2), pos_hint={"center_x": 0.5, "center_y": 0.75})
        btn_gerar.bind(on_press=self.ir_para_analise)
        layout.add_widget(btn_gerar)

        btn_stats = Button(text="Gráficos Opcionais", size_hint=(0.4, 0.2), pos_hint={"center_x": 0.5, "center_y": 0.5})
        btn_stats.bind(on_press=self.ir_para_opcionais)
        layout.add_widget(btn_stats)

        btn_sobre = Button(text="Sobre", size_hint=(0.4, 0.2), pos_hint={"center_x": 0.5, "center_y": 0.25})
        btn_sobre.bind(on_press=self.abrir_popup_sobre)
        layout.add_widget(btn_sobre)

        self.add_widget(layout)


    def ir_para_analise(self, *args):
        self.manager.current = "Métricas"

    def ir_para_opcionais(self, *args):
        self.manager.current = "Gráficos Opcionais"

    def abrir_popup_sobre(self, *args):
        texto1 = (
            "Trabalho 2 Redes de Computadores.\n\n"
            "Este programa tem como objetivo analisar e gerar gráficos a partir de arquivos de captura de pacotes IP, com ênfase no uso do protocolo TCP.\n\n"
        )

        texto2 = (
            "Feito por:\n\nDavi de Castro Machado\nGiovana Borelli\nJoão Pedro Righi\nLaura Boemo"
        )

        # Layout principal com padding
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Botão X de fechar (alinhado à direita)
        fechar_layout = AnchorLayout(anchor_x='right', anchor_y='top', size_hint=(1, None), height=40)
        btn_fechar = Button(text='X', size_hint=(None, None), size=(40, 40))
        fechar_layout.add_widget(btn_fechar)
        content.add_widget(fechar_layout)

        # Scroll com o texto principal (texto1)
        scroll = ScrollView(size_hint=(1, 1))
        label = Label(
            text=texto1,
            size_hint_y=None,
            halign='left',
            valign='top',
            font_size='16sp',
            text_size=(660, None),
            padding=(20, 10)  # Padding nas laterais e topo/baixo
        )
        label.bind(texture_size=lambda instance, value: setattr(label, 'height', value[1]))
        scroll.add_widget(label)
        content.add_widget(scroll)

        # Adicionando o texto2 (centralizado horizontalmente)
        label2 = Label(
            text=texto2,
            size_hint_y=0.8,
            halign='center',  # Centraliza horizontalmente
            valign='middle',  # Centraliza verticalmente dentro do espaço
            font_size='16sp',
            text_size=(660, None),
            padding=(20, 10)
        )
        content.add_widget(label2)

        # Popup
        popup = Popup(title="Sobre o trabalho",
                    content=content,
                    size_hint=(0.9, 0.7),
                    auto_dismiss=False)

        # Botão fecha o popup
        btn_fechar.bind(on_release=popup.dismiss)
        popup.open()

class TelaAnalise(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pasta_graficos = "graficos_metricas"
        self.graficos_atual = []
        self.indice_atual = 0

        layout_principal = BoxLayout(orientation='horizontal')

        # Barra lateral com botão Voltar
        barra_lateral = BoxLayout(orientation='vertical', size_hint=(0.25, 1), spacing=10, padding=10)

        label = Label(text="Navegação", size_hint=(1, 0.1))
        barra_lateral.add_widget(label)

        btn_voltar = Button(text="Voltar", size_hint=(1, 0.1))
        btn_voltar.bind(on_press=self.voltar_menu)
        barra_lateral.add_widget(btn_voltar)

        layout_principal.add_widget(barra_lateral)

        # Área central para o gráfico
        self.area_grafico = BoxLayout(orientation='vertical', size_hint=(0.75, 1), padding=20, spacing=10)

        self.fundo_branco = FloatLayout(size_hint=(1.0, 0.8))
        with self.fundo_branco.canvas.before:
            Color(1, 1, 1, 1)
            self.fundo_rect = Rectangle(pos=self.fundo_branco.pos, size=self.fundo_branco.size)
            self.fundo_branco.bind(pos=self._update_fundo, size=self._update_fundo)

        self.imagem = Image(
            size_hint=(0.8, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self.fundo_branco.add_widget(self.imagem)

        self.area_grafico.add_widget(self.fundo_branco)

        self.label_explicativo = Label(
            text="Legenda aparecerá aqui",
            size_hint=(1, 0.1),
            halign='center'
        )
        self.area_grafico.add_widget(self.label_explicativo)

        box_nav = BoxLayout(size_hint=(1, 0.1), spacing=20, padding=(40, 0))
        btn_anterior = Button(text="Anterior")
        btn_proximo = Button(text="Próximo")
        btn_anterior.bind(on_press=self.anterior_grafico)
        btn_proximo.bind(on_press=self.proximo_grafico)
        box_nav.add_widget(btn_anterior)
        box_nav.add_widget(btn_proximo)
        self.area_grafico.add_widget(box_nav)

        layout_principal.add_widget(self.area_grafico)
        self.add_widget(layout_principal)

        self.carregar_graficos()

    def carregar_graficos(self):
        """Carrega todos os arquivos de imagem da pasta especificada."""
        if os.path.isdir(self.pasta_graficos):
            arquivos = sorted([
                f for f in os.listdir(self.pasta_graficos)
                if f.lower().endswith('.png')
            ])
            self.graficos_atual = [(os.path.join(self.pasta_graficos, f), f.replace('_', ' ').replace('.png', '').title())
                                   for f in arquivos]
            self.indice_atual = 0
            self.atualizar_imagem()
        else:
            self.label_explicativo.text = "Pasta de gráficos não encontrada."

    def atualizar_imagem(self):
        if self.graficos_atual:
            caminho_imagem, legenda = self.graficos_atual[self.indice_atual]
            if os.path.exists(caminho_imagem):
                self.imagem.source = caminho_imagem
                self.imagem.reload()
                self.label_explicativo.text = legenda
            else:
                self.label_explicativo.text = "Imagem não encontrada."
        else:
            self.label_explicativo.text = "Nenhum gráfico disponível."

    def anterior_grafico(self, *args):
        if self.indice_atual > 0:
            self.indice_atual -= 1
            self.atualizar_imagem()

    def proximo_grafico(self, *args):
        if self.indice_atual < len(self.graficos_atual) - 1:
            self.indice_atual += 1
            self.atualizar_imagem()

    def voltar_menu(self, *args):
        self.manager.current = "Menu Inicial"

    def _update_fundo(self, instance, value):
        self.fundo_rect.pos = instance.pos
        self.fundo_rect.size = instance.size

class TelaGraficosBasicos(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pasta_graficos = "graficos_opcionais"
        self.graficos_atual = []
        self.indice_atual = 0

        layout_principal = BoxLayout(orientation='horizontal')

        # Barra lateral com botão Voltar
        barra_lateral = BoxLayout(orientation='vertical', size_hint=(0.25, 1), spacing=10, padding=10)
        label = Label(text="Navegação", size_hint=(1, 0.1))
        barra_lateral.add_widget(label)

        btn_voltar = Button(text="Voltar", size_hint=(1, 0.1))
        btn_voltar.bind(on_press=self.voltar_menu)
        barra_lateral.add_widget(btn_voltar)

        layout_principal.add_widget(barra_lateral)

        # Área central de exibição
        self.area_grafico = BoxLayout(orientation='vertical', size_hint=(0.75, 1), padding=20, spacing=10)

        self.fundo_branco = FloatLayout(size_hint=(1.0, 0.8))
        with self.fundo_branco.canvas.before:
            Color(1, 1, 1, 1)
            self.fundo_rect = Rectangle(pos=self.fundo_branco.pos, size=self.fundo_branco.size)
            self.fundo_branco.bind(pos=self._update_fundo, size=self._update_fundo)

        self.imagem = Image(
            size_hint=(0.8, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self.fundo_branco.add_widget(self.imagem)

        self.area_grafico.add_widget(self.fundo_branco)

        self.label_explicativo = Label(
            text="Legenda aparecerá aqui",
            size_hint=(1, 0.1),
            halign='center'
        )
        self.area_grafico.add_widget(self.label_explicativo)

        box_nav = BoxLayout(size_hint=(1, 0.1), spacing=20, padding=(40, 0))
        btn_anterior = Button(text="Anterior")
        btn_proximo = Button(text="Próximo")
        btn_anterior.bind(on_press=self.anterior_grafico)
        btn_proximo.bind(on_press=self.proximo_grafico)
        box_nav.add_widget(btn_anterior)
        box_nav.add_widget(btn_proximo)
        self.area_grafico.add_widget(box_nav)

        layout_principal.add_widget(self.area_grafico)
        self.add_widget(layout_principal)

        self.carregar_graficos()

    def carregar_graficos(self):
        """Carrega todos os arquivos de imagem da pasta especificada."""
        if os.path.isdir(self.pasta_graficos):
            arquivos = sorted([
                f for f in os.listdir(self.pasta_graficos)
                if f.lower().endswith('.png')
            ])
            self.graficos_atual = [
                (os.path.join(self.pasta_graficos, f), f.replace('_', ' ').replace('.png', '').title())
                for f in arquivos
            ]
            self.indice_atual = 0
            self.atualizar_imagem()
        else:
            self.label_explicativo.text = "Pasta de gráficos não encontrada."

    def atualizar_imagem(self):
        if self.graficos_atual:
            caminho_imagem, legenda = self.graficos_atual[self.indice_atual]
            if os.path.exists(caminho_imagem):
                self.imagem.source = caminho_imagem
                self.imagem.reload()
                self.label_explicativo.text = legenda
            else:
                self.label_explicativo.text = "Imagem não encontrada."
        else:
            self.label_explicativo.text = "Nenhum gráfico disponível."

    def anterior_grafico(self, *args):
        if self.indice_atual > 0:
            self.indice_atual -= 1
            self.atualizar_imagem()

    def proximo_grafico(self, *args):
        if self.indice_atual < len(self.graficos_atual) - 1:
            self.indice_atual += 1
            self.atualizar_imagem()

    def voltar_menu(self, *args):
        self.manager.current = "Menu Inicial"

    def _update_fundo(self, instance, value):
        self.fundo_rect.pos = instance.pos
        self.fundo_rect.size = instance.size



class GerenciadorTelas(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(TelaMenuInicial(name="Menu Inicial"))
        self.add_widget(TelaAnalise(name="Métricas"))
        self.add_widget(TelaGraficosBasicos(name="Gráficos Opcionais"))


class NetGraphicsApp(App):
    def build(self):
        return GerenciadorTelas()


if __name__ == "__main__":
    NetGraphicsApp().run()
