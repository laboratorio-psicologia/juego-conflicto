import json
import random
from types import SimpleNamespace as NS
from otree.api import *

doc = """
Juego de Conflicto Intergrupal – Campos de Batalla
Inspirado en Colonel Blotto (Roberson, 2006).
Dos equipos de 3 jugadores (Azul vs Rojo), 8 rondas.
"""

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

class C(BaseConstants):
    NAME_IN_URL = 'juego'
    PLAYERS_PER_GROUP = 6
    NUM_ROUNDS = 8

    TOKENS_PER_ROUND = 15
    PRIZE_POOL = 45
    PUNISHMENT_COST = 1
    PUNISHMENT_PENALTY = 5

    CHAT_DURATION = 180    # 3 minutos
    DECISION_DURATION = 60
    RESULTS_DURATION = 60
    PUNISHMENT_DURATION = 60
    EMOTION_DURATION = 90

    # id_in_group 1-3 = Azul, 4-6 = Rojo
    AZUL_IDS = [1, 2, 3]
    ROJO_IDS = [4, 5, 6]


# ─────────────────────────────────────────────────────────────────────────────
# SUBSESSION
# ─────────────────────────────────────────────────────────────────────────────

class Subsession(BaseSubsession):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# GROUP
# ─────────────────────────────────────────────────────────────────────────────

class Group(BaseGroup):
    # Totales por equipo y frente
    total_a_azul = models.IntegerField(initial=0)
    total_b_azul = models.IntegerField(initial=0)
    total_c_azul = models.IntegerField(initial=0)
    total_a_rojo = models.IntegerField(initial=0)
    total_b_rojo = models.IntegerField(initial=0)
    total_c_rojo = models.IntegerField(initial=0)

    # Ganador por frente: 'azul', 'rojo', 'empate'
    ganador_a = models.StringField(initial='')
    ganador_b = models.StringField(initial='')
    ganador_c = models.StringField(initial='')
    ganador_ronda = models.StringField(initial='')  # 'azul', 'rojo', 'empate'

    # Mensajes de chat (JSON: lista de {sender_id, sender_name, text, ts})
    chat_grupal_azul = models.LongStringField(initial='[]')
    chat_grupal_rojo = models.LongStringField(initial='[]')
    # Chats privados dentro del equipo (por par canónico: menor_mayor)
    chat_priv_12 = models.LongStringField(initial='[]')
    chat_priv_13 = models.LongStringField(initial='[]')
    chat_priv_23 = models.LongStringField(initial='[]')
    chat_priv_45 = models.LongStringField(initial='[]')
    chat_priv_46 = models.LongStringField(initial='[]')
    chat_priv_56 = models.LongStringField(initial='[]')

    # Resultado del castigo: JSON {str(id_in_group): votos_recibidos}
    resultado_castigo = models.LongStringField(initial='{}')

    # ── Helpers ───────────────────────────────────────────────────────────────

    def es_azul(self, player):
        return player.id_in_group in C.AZUL_IDS

    def equipo(self, player):
        return [p for p in self.get_players()
                if self.es_azul(p) == self.es_azul(player)]

    def companeros(self, player):
        return [p for p in self.equipo(player) if p.id_in_group != player.id_in_group]

    def rivales(self, player):
        return [p for p in self.get_players()
                if self.es_azul(p) != self.es_azul(player)]

    def _ganador_frente(self, azul, rojo):
        if azul > rojo:
            return 'azul'
        if rojo > azul:
            return 'rojo'
        return 'empate'

    def _campo_chat_privado(self, id1, id2):
        a, b = sorted([id1, id2])
        return f'chat_priv_{a}{b}'

    # ── Lógica de resultados ──────────────────────────────────────────────────

    def calcular_resultados(self):
        players = self.get_players()
        azules = [p for p in players if p.id_in_group in C.AZUL_IDS]
        rojos  = [p for p in players if p.id_in_group in C.ROJO_IDS]

        self.total_a_azul = sum(p.frente_a for p in azules)
        self.total_b_azul = sum(p.frente_b for p in azules)
        self.total_c_azul = sum(p.frente_c for p in azules)
        self.total_a_rojo = sum(p.frente_a for p in rojos)
        self.total_b_rojo = sum(p.frente_b for p in rojos)
        self.total_c_rojo = sum(p.frente_c for p in rojos)

        self.ganador_a = self._ganador_frente(self.total_a_azul, self.total_a_rojo)
        self.ganador_b = self._ganador_frente(self.total_b_azul, self.total_b_rojo)
        self.ganador_c = self._ganador_frente(self.total_c_azul, self.total_c_rojo)

        ganados = [self.ganador_a, self.ganador_b, self.ganador_c]
        azul_wins = ganados.count('azul')
        rojo_wins = ganados.count('rojo')
        if azul_wins >= 2:
            self.ganador_ronda = 'azul'
        elif rojo_wins >= 2:
            self.ganador_ronda = 'rojo'
        else:
            self.ganador_ronda = 'empate'

        frentes_azul = [f for f, g in [('a', self.ganador_a), ('b', self.ganador_b), ('c', self.ganador_c)] if g == 'azul']
        frentes_rojo = [f for f, g in [('a', self.ganador_a), ('b', self.ganador_b), ('c', self.ganador_c)] if g == 'rojo']

        self._calcular_premios(azules, frentes_azul, self.ganador_ronda == 'azul')
        self._calcular_premios(rojos,  frentes_rojo,  self.ganador_ronda == 'rojo')

    def _calcular_premios(self, jugadores, frentes_ganados, equipo_gano):
        contribuciones = {}
        for p in jugadores:
            contrib = sum(getattr(p, f'frente_{f}') for f in frentes_ganados)
            contribuciones[p.id_in_group] = contrib

        total_contrib = sum(contribuciones.values())

        for p in jugadores:
            if equipo_gano and total_contrib > 0:
                p.premio_ronda = round(
                    (contribuciones[p.id_in_group] / total_contrib) * C.PRIZE_POOL, 2)
            else:
                p.premio_ronda = 0.0

            factor = 1.0 if equipo_gano else 0.5
            p.ahorro_efectivo = round(p.ahorro * factor, 2)
            p.ganancia_ronda  = round(p.premio_ronda + p.ahorro_efectivo, 2)

            prev = p.participant.vars.get('acumulado', 0.0)
            p.participant.vars['acumulado'] = round(prev + p.ganancia_ronda, 2)

    def calcular_castigo(self):
        players = self.get_players()
        azules = [p for p in players if p.id_in_group in C.AZUL_IDS]
        rojos  = [p for p in players if p.id_in_group in C.ROJO_IDS]

        resultado = {}
        for equipo in [azules, rojos]:
            votos_contra = {p.id_in_group: 0 for p in equipo}
            for p in equipo:
                if p.voto_castigo and p.voto_castigo != 0:
                    if p.voto_castigo in votos_contra:
                        votos_contra[p.voto_castigo] += 1
                        # El votante paga 1 ficha
                        p.participant.vars['acumulado'] = round(
                            p.participant.vars.get('acumulado', 0) - C.PUNISHMENT_COST, 2)

            for p in equipo:
                votos = votos_contra[p.id_in_group]
                resultado[str(p.id_in_group)] = votos
                if votos >= 2:
                    p.fue_castigado = True
                    p.participant.vars['acumulado'] = round(
                        p.participant.vars.get('acumulado', 0) - C.PUNISHMENT_PENALTY, 2)
                else:
                    p.fue_castigado = False

        self.resultado_castigo = json.dumps(resultado)


# ─────────────────────────────────────────────────────────────────────────────
# PLAYER
# ─────────────────────────────────────────────────────────────────────────────

class Player(BasePlayer):
    # ── Decisión por ronda ────────────────────────────────────────────────────
    frente_a = models.IntegerField(initial=0, min=0, max=C.TOKENS_PER_ROUND, label="Frente A")
    frente_b = models.IntegerField(initial=0, min=0, max=C.TOKENS_PER_ROUND, label="Frente B")
    frente_c = models.IntegerField(initial=0, min=0, max=C.TOKENS_PER_ROUND, label="Frente C")
    ahorro   = models.IntegerField(initial=0, min=0, max=C.TOKENS_PER_ROUND, label="Ahorro personal")

    # ── Ganancias ─────────────────────────────────────────────────────────────
    premio_ronda   = models.FloatField(initial=0)
    ahorro_efectivo = models.FloatField(initial=0)
    ganancia_ronda  = models.FloatField(initial=0)

    # ── Castigo ───────────────────────────────────────────────────────────────
    voto_castigo  = models.IntegerField(initial=0, label="¿A quién castigas?")
    fue_castigado = models.BooleanField(initial=False)

    # ── Emociones post-ronda (ira estado, escala 1-7) ─────────────────────────
    ira_general = models.IntegerField(min=1, max=7, blank=True,
                    label="¿Qué tan enojado/a te sientes en este momento?")
    ira_comp1   = models.IntegerField(min=1, max=7, blank=True,
                    label="¿Qué tan enojado/a estás con tu compañero/a 1?")
    ira_comp2   = models.IntegerField(min=1, max=7, blank=True,
                    label="¿Qué tan enojado/a estás con tu compañero/a 2?")
    ira_rival   = models.IntegerField(min=1, max=7, blank=True,
                    label="¿Qué tan enojado/a estás con el equipo rival?")

    # ── STAXI-2 (medido solo en ronda 1) ─────────────────────────────────────
    # NOTA: Usar la versión validada al español de Miguel Á. Pérez-Nieto et al.
    # Los ítems a continuación son representativos; reemplazar por los ítems
    # oficiales de la versión española del STAXI-2.

    # Rasgo de Ira – 10 ítems (1=Casi nunca … 4=Casi siempre)
    staxi_r01 = models.IntegerField(min=1, max=4, blank=True, label="Me enojo")
    staxi_r02 = models.IntegerField(min=1, max=4, blank=True, label="Tengo un carácter fuerte")
    staxi_r03 = models.IntegerField(min=1, max=4, blank=True, label="Soy una persona impulsiva")
    staxi_r04 = models.IntegerField(min=1, max=4, blank=True, label="Me irrita cuando no me reconocen un trabajo bien hecho")
    staxi_r05 = models.IntegerField(min=1, max=4, blank=True, label="Me enfurezco cuando cometo errores estúpidos")
    staxi_r06 = models.IntegerField(min=1, max=4, blank=True, label="Me siento furioso/a cuando me critican delante de los demás")
    staxi_r07 = models.IntegerField(min=1, max=4, blank=True, label="Me enfado mucho")
    staxi_r08 = models.IntegerField(min=1, max=4, blank=True, label="Me irrita que mi trabajo sea poco valorado")
    staxi_r09 = models.IntegerField(min=1, max=4, blank=True, label="Pierdo los estribos")
    staxi_r10 = models.IntegerField(min=1, max=4, blank=True, label="Me enojo cuando me equivoco")

    # Anger-In – 8 ítems (1=Casi nunca … 4=Casi siempre)
    staxi_ai1 = models.IntegerField(min=1, max=4, blank=True, label="Contengo mi ira")
    staxi_ai2 = models.IntegerField(min=1, max=4, blank=True, label="Guardo rencores que no le cuento a nadie")
    staxi_ai3 = models.IntegerField(min=1, max=4, blank=True, label="Me irrito más de lo que la gente nota")
    staxi_ai4 = models.IntegerField(min=1, max=4, blank=True, label="Me hierve la sangre aunque no lo demuestro")
    staxi_ai5 = models.IntegerField(min=1, max=4, blank=True, label="Me enfado pero lo siento por dentro")
    staxi_ai6 = models.IntegerField(min=1, max=4, blank=True, label="Controlo mi comportamiento para no expresar mi ira")
    staxi_ai7 = models.IntegerField(min=1, max=4, blank=True, label="Rumio mi enfado sin expresarlo")
    staxi_ai8 = models.IntegerField(min=1, max=4, blank=True, label="Reprimo mi ira")

    # Anger-Out – 8 ítems (1=Casi nunca … 4=Casi siempre)
    staxi_ao1 = models.IntegerField(min=1, max=4, blank=True, label="Pierdo los nervios")
    staxi_ao2 = models.IntegerField(min=1, max=4, blank=True, label="Expreso mi ira")
    staxi_ao3 = models.IntegerField(min=1, max=4, blank=True, label="Digo cosas desagradables")
    staxi_ao4 = models.IntegerField(min=1, max=4, blank=True, label="Hago comentarios sarcásticos")
    staxi_ao5 = models.IntegerField(min=1, max=4, blank=True, label="Tiro o rompo objetos")
    staxi_ao6 = models.IntegerField(min=1, max=4, blank=True, label="Me comporto de forma agresiva")
    staxi_ao7 = models.IntegerField(min=1, max=4, blank=True, label="Muestro abiertamente mi ira")
    staxi_ao8 = models.IntegerField(min=1, max=4, blank=True, label="Golpeo cosas")

    # Anger-Control – 8 ítems (1=Casi nunca … 4=Casi siempre)
    staxi_ac1 = models.IntegerField(min=1, max=4, blank=True, label="Controlo mi temperamento")
    staxi_ac2 = models.IntegerField(min=1, max=4, blank=True, label="Me calmo antes de actuar")
    staxi_ac3 = models.IntegerField(min=1, max=4, blank=True, label="Controlo el impulso de actuar agresivamente")
    staxi_ac4 = models.IntegerField(min=1, max=4, blank=True, label="Reduzco mi ira tan pronto como puedo")
    staxi_ac5 = models.IntegerField(min=1, max=4, blank=True, label="Me domino a mí mismo/a")
    staxi_ac6 = models.IntegerField(min=1, max=4, blank=True, label="Controlo mis sentimientos de ira")
    staxi_ac7 = models.IntegerField(min=1, max=4, blank=True, label="Me tranquilizo más rápido de lo que me enfado")
    staxi_ac8 = models.IntegerField(min=1, max=4, blank=True, label="Tolero las cosas que me hacen enojar")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def color_equipo(self):
        return 'Azul' if self.id_in_group in C.AZUL_IDS else 'Rojo'

    def posicion_en_equipo(self):
        return self.id_in_group if self.id_in_group in C.AZUL_IDS else self.id_in_group - 3

    def nombre(self):
        return f"J{self.posicion_en_equipo()}"

    def acumulado(self):
        return self.participant.vars.get('acumulado', 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINAS
# ─────────────────────────────────────────────────────────────────────────────

# ── Helpers de modo solo ──────────────────────────────────────────────────────
def _es_solo(player):
    """True si la sesión corre en modo solo (1 jugador real, resto en fondo)."""
    return bool(player.session.config.get('is_solo', False))

def _ronda_max(player):
    """Última ronda efectiva: respeta solo_rounds en modo solo, NUM_ROUNDS si no."""
    if _es_solo(player):
        return int(player.session.config.get('solo_rounds', C.NUM_ROUNDS))
    return C.NUM_ROUNDS

def _visible(player):
    """En modo solo, solo el jugador 1 (id_in_group==1) ve páginas de contenido."""
    if _es_solo(player):
        return player.id_in_group == 1
    return True


def _vars_instrucciones(player):
    return dict(
        tokens=C.TOKENS_PER_ROUND,
        rondas=C.NUM_ROUNDS,
        premio=C.PRIZE_POOL,
        costo_castigo=C.PUNISHMENT_COST,
        penalizacion=C.PUNISHMENT_PENALTY,
    )


class Instrucciones(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and _visible(player)

    @staticmethod
    def vars_for_template(player):
        return _vars_instrucciones(player)


class Instrucciones2(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and _visible(player)

    @staticmethod
    def vars_for_template(player):
        return _vars_instrucciones(player)


class PruebaPractica(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and _visible(player)

    @staticmethod
    def vars_for_template(player):
        return dict(
            tokens=C.TOKENS_PER_ROUND,
            color_equipo=player.color_equipo(),
            nombre_jugador=player.nombre(),
        )


class PaginaSTAXI(Page):
    form_model = 'player'
    form_fields = [
        'staxi_r01', 'staxi_r02', 'staxi_r03', 'staxi_r04', 'staxi_r05',
        'staxi_r06', 'staxi_r07', 'staxi_r08', 'staxi_r09', 'staxi_r10',
        'staxi_ai1', 'staxi_ai2', 'staxi_ai3', 'staxi_ai4',
        'staxi_ai5', 'staxi_ai6', 'staxi_ai7', 'staxi_ai8',
        'staxi_ao1', 'staxi_ao2', 'staxi_ao3', 'staxi_ao4',
        'staxi_ao5', 'staxi_ao6', 'staxi_ao7', 'staxi_ao8',
        'staxi_ac1', 'staxi_ac2', 'staxi_ac3', 'staxi_ac4',
        'staxi_ac5', 'staxi_ac6', 'staxi_ac7', 'staxi_ac8',
    ]

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and _visible(player)

    @staticmethod
    def vars_for_template(player):
        # Construimos los grupos del STAXI para renderizar en el template
        # sin usar filtros de Django (que oTree no soporta).
        def mk_lista(*pares):
            return [NS(nombre=n, etiqueta=e) for n, e in pares]

        escala = '1 = Casi nunca · 2 = A veces · 3 = Con frecuencia · 4 = Casi siempre'
        grupos = [
            NS(
                titulo='Rasgo de Ira',
                escala=escala,
                lista=mk_lista(
                    ('staxi_r01', 'Me enojo'),
                    ('staxi_r02', 'Tengo un carácter fuerte'),
                    ('staxi_r03', 'Soy una persona impulsiva'),
                    ('staxi_r04', 'Me irrita cuando no me reconocen un trabajo bien hecho'),
                    ('staxi_r05', 'Me enfurezco cuando cometo errores estúpidos'),
                    ('staxi_r06', 'Me siento furioso/a cuando me critican delante de los demás'),
                    ('staxi_r07', 'Me enfado mucho'),
                    ('staxi_r08', 'Me irrita que mi trabajo sea poco valorado'),
                    ('staxi_r09', 'Pierdo los estribos'),
                    ('staxi_r10', 'Me enojo cuando me equivoco'),
                ),
            ),
            NS(
                titulo='Supresión de la ira (Anger-In)',
                escala=escala,
                lista=mk_lista(
                    ('staxi_ai1', 'Contengo mi ira'),
                    ('staxi_ai2', 'Guardo rencores que no le cuento a nadie'),
                    ('staxi_ai3', 'Me irrito más de lo que la gente nota'),
                    ('staxi_ai4', 'Me hierve la sangre aunque no lo demuestro'),
                    ('staxi_ai5', 'Me enfado pero lo siento por dentro'),
                    ('staxi_ai6', 'Controlo mi comportamiento para no expresar mi ira'),
                    ('staxi_ai7', 'Rumio mi enfado sin expresarlo'),
                    ('staxi_ai8', 'Reprimo mi ira'),
                ),
            ),
            NS(
                titulo='Expresión de la ira (Anger-Out)',
                escala=escala,
                lista=mk_lista(
                    ('staxi_ao1', 'Pierdo los nervios'),
                    ('staxi_ao2', 'Expreso mi ira'),
                    ('staxi_ao3', 'Digo cosas desagradables'),
                    ('staxi_ao4', 'Hago comentarios sarcásticos'),
                    ('staxi_ao5', 'Tiro o rompo objetos'),
                    ('staxi_ao6', 'Me comporto de forma agresiva'),
                    ('staxi_ao7', 'Muestro abiertamente mi ira'),
                    ('staxi_ao8', 'Golpeo cosas'),
                ),
            ),
            NS(
                titulo='Control de la ira (Anger-Control)',
                escala=escala,
                lista=mk_lista(
                    ('staxi_ac1', 'Controlo mi temperamento'),
                    ('staxi_ac2', 'Me calmo antes de actuar'),
                    ('staxi_ac3', 'Controlo el impulso de actuar agresivamente'),
                    ('staxi_ac4', 'Reduzco mi ira tan pronto como puedo'),
                    ('staxi_ac5', 'Me domino a mí mismo/a'),
                    ('staxi_ac6', 'Controlo mis sentimientos de ira'),
                    ('staxi_ac7', 'Me tranquilizo más rápido de lo que me enfado'),
                    ('staxi_ac8', 'Tolero las cosas que me hacen enojar'),
                ),
            ),
        ]
        return dict(grupos=grupos)


class EsperaInicio(WaitPage):
    title_text = 'Espera a que todos estén listos'
    body_text = 'El juego comenzará cuando todos los jugadores hayan completado el cuestionario inicial.'

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and _visible(player)


class ChatPage(Page):
    """Fase de comunicación – live page con chat grupal y privados."""
    timeout_seconds = C.CHAT_DURATION

    @staticmethod
    def is_displayed(player):
        return _visible(player) and player.round_number <= _ronda_max(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        """En sesiones de bot, poblar el chat con mensajes largos y realistas."""
        import random as _rnd
        if not player.participant._is_bot:
            return
        group = player.group
        comp  = group.companeros(player)
        ronda = player.round_number

        apertura = [
            "Buenas a todos. Antes de que empiece el tiempo, quería proponer que nos coordinemos bien esta ronda. En la ronda anterior creo que cada uno hizo lo suyo sin avisarse y eso nos costó caro. Si coordinamos un frente fuerte tenemos muchas más chances de ganar. ¿Qué dicen?",
            "Hola equipo. He estado pensando en la estrategia y creo que lo más inteligente es concentrar las fichas en un solo frente en vez de distribuirlas entre los tres. Si los tres ponemos la mayoría en el mismo frente, es casi imposible que el rival nos gane ahí. Necesito saber qué piensan para decidir.",
            "¡Hola! Empecemos a hablar de estrategia antes de que se nos acabe el tiempo. Lo que me funcionó en otras rondas es apostar fuerte en un frente y guardar algo de ahorro por si perdemos. ¿Tienen preferencia por el frente A, B o C esta vez? Yo me adapto a lo que decida el grupo.",
            "Equipo, hay que organizarse bien esta vez. Me parece que el equipo contrario también va a intentar coordinar, así que tenemos que ser más listos que ellos. Propongo que nos pongamos de acuerdo en UN frente y que los tres metamos la mayoría de las fichas ahí. ¿Alguien tiene idea de cuál?",
            "Buenos días o tardes según donde estén jaja. Si los tres concentramos en el frente A, ponemos 45 fichas ahí y el rival tiene que meter más de 45 para ganarnos — eso es difícil para ellos. ¿Les parece bien ir todos al A esta ronda?",
            "¿Alguien más está cansado de perder? jaja. En serio, creo que la clave está en la coordinación. Si cada uno se va por su cuenta, el rival nos supera. Pero si los tres vamos juntos a uno solo, lo ganamos seguro. La pregunta es cuál elegimos.",
        ]
        estrategia = [
            "Yo voy a meter la mayoría al frente B. Creo que el rival no espera que nos concentremos ahí y podríamos sorprenderlos. Guardaré 2 o 3 fichas de ahorro por si acaso. ¿Alguien más va al B?",
            "Mi plan es distribuir así: 10 al A, 3 al B, 2 al C. El A me parece el más importante porque si lo ganamos y uno de los otros también, ganamos la ronda. Claro que esto depende de que ustedes también pongan algo ahí.",
            "Pensándolo bien, creo que vale más la pena apostar todo en un frente que distribuir parejo. Con 15 fichas cada uno y tres jugadores, si los tres vamos al mismo tenemos 45 fichas concentradas — es mucho. Yo voy al frente que digan la mayoría.",
            "Lo que veo es que el frente A es donde más se concentra la gente normalmente, así que el rival también va a ir ahí. Por eso propongo atacar el B o el C. Pensar lo contrario a lo obvio nos da ventaja.",
            "Para ser transparente: yo voy a guardar 3 fichas de ahorro y el resto lo meto en el frente A. Es mi estrategia, pero si el grupo prefiere otro frente puedo cambiar. Lo importante es que coordinemos.",
            "Seamos honestos: si no coordinamos, el otro equipo nos va a ganar aunque tengamos buenas intenciones. Mi voto es por concentrar todos en el frente B. Digan si están de acuerdo antes de que se acabe el tiempo.",
        ]
        reaccion = [
            "Uf, esa ronda estuvo difícil. Creo que nos faltó coordinación en el frente donde más apostamos. ¿Alguien puede contarme qué pasó? Para la próxima ronda necesito entender mejor cómo distribuye el otro equipo.",
            "¡Bien jugado equipo! Eso es lo que pasa cuando coordinamos bien — los superamos claramente en el frente fuerte. Sigamos con esta estrategia, aunque quizás cambiemos el frente para que no nos adivinen.",
            "Nos ganaron esa ronda, hay que admitirlo. Pero creo que podemos remontar si ajustamos la estrategia. ¿Qué frente creen que el equipo contrario va a atacar esta vez? Si podemos anticiparlo, les ganamos dos frentes con menos esfuerzo.",
            "La ronda pasada perdimos por poco. Creo que si uno o dos de nosotros hubiera puesto unas fichas más en el frente A, lo ganábamos. Hay que ser más agresivos y no quedarse con demasiado ahorro cuando el equipo lo necesita.",
            "Empate en la ronda pasada. No es lo que queríamos pero tampoco es un desastre. Esta ronda hay que definir bien la estrategia antes de que empiece la cuenta regresiva y no improvisar.",
        ]
        privadas = [
            "Oye, te escribo en privado porque no quiero que el otro lo sepa todavía. Mi plan es meter casi todo al frente B, pero en el chat grupal dije que iba al A para despistar. ¿Tú qué vas a hacer? Si los dos vamos al B lo ganamos seguro.",
            "Tengo una propuesta que solo quiero decirte a ti. ¿Qué tal si nos coordinamos los dos en el frente C y dejamos que el tercero haga lo que quiera? Si tú y yo metemos 12 o 13 cada uno al C, el rival no puede con nosotros ahí.",
            "Aquí en confianza: creo que el tercer compañero no está cooperando bien. En las rondas anteriores parecía que iba por su cuenta. ¿Tú lo notas también? Si no cambia, deberíamos considerar votarle el castigo.",
            "¿Cuánto vas a guardar de ahorro esta ronda? Yo estoy pensando en 3 o 4 fichas. No me gusta quedarme sin nada si perdemos. Pero tampoco quiero poner tan poco que no aporte nada al equipo.",
            "Te cuento mi estrategia real: voy al frente A con 11 fichas, 1 al B, 1 al C y 2 de ahorro. Si tú también vas fuerte al A lo ganamos con mucho margen. ¿Puedes ir al menos con 8 o 9 al A también?",
            "Aquí entre nosotros: si perdemos esta ronda voy a votar para castigar a alguien que no cooperó. Creo que hay que mandar un mensaje cuando alguien no cumple lo que dice en el chat.",
        ]

        # Mensajes grupales
        canal = 'chat_grupal_azul' if group.es_azul(player) else 'chat_grupal_rojo'
        msgs  = json.loads(getattr(group, canal))

        msgs.append({'sender_id': player.id_in_group, 'sender_name': player.nombre(),
                     'texto': _rnd.choice(apertura)})
        msgs.append({'sender_id': player.id_in_group, 'sender_name': player.nombre(),
                     'texto': _rnd.choice(estrategia)})
        if ronda > 1 and _rnd.random() < 0.70:
            msgs.append({'sender_id': player.id_in_group, 'sender_name': player.nombre(),
                         'texto': _rnd.choice(reaccion)})

        setattr(group, canal, json.dumps(msgs))

        # Mensaje privado (60 % de probabilidad)
        if comp and _rnd.random() < 0.60:
            partner = _rnd.choice(comp)
            campo   = group._campo_chat_privado(player.id_in_group, partner.id_in_group)
            priv    = json.loads(getattr(group, campo))
            priv.append({'sender_id': player.id_in_group, 'sender_name': player.nombre(),
                         'texto': _rnd.choice(privadas)})
            setattr(group, campo, json.dumps(priv))

    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        comp = group.companeros(player)
        equipo = group.equipo(player)

        # Cargar historial del chat actual (como NS para acceso con punto en template)
        canal_grupo = 'chat_grupal_azul' if group.es_azul(player) else 'chat_grupal_rojo'
        msgs_grupo  = [NS(sender_id=m['sender_id'], sender_name=m['sender_name'], texto=m['texto'])
                       for m in json.loads(getattr(group, canal_grupo))]

        # Chats privados: lista de NS con id, nombre y mensajes para cada compañero
        companeros_data = []
        for c in comp:
            campo = group._campo_chat_privado(player.id_in_group, c.id_in_group)
            msgs = json.loads(getattr(group, campo))
            # Convertir cada mensaje a NS para que el template pueda acceder con punto
            msgs_ns = [NS(sender_id=m['sender_id'], sender_name=m['sender_name'], texto=m['texto'])
                       for m in msgs]
            companeros_data.append(NS(
                id=c.id_in_group,
                nombre=c.nombre(),
                mensajes=msgs_ns,
            ))

        return dict(
            ronda=player.round_number,
            total_rondas=C.NUM_ROUNDS,
            color_equipo=player.color_equipo(),
            nombre_jugador=player.nombre(),
            mi_id=player.id_in_group,
            companeros_data=companeros_data,
            msgs_grupo=msgs_grupo,
            timer_segundos=C.CHAT_DURATION,
        )

    @staticmethod
    def live_method(player: Player, data):
        group = player.group
        tipo = data.get('tipo')
        texto = str(data.get('texto', '')).strip()[:500]  # limitar longitud

        if not texto:
            return {}

        msg = {
            'sender_id':   player.id_in_group,
            'sender_name': player.nombre(),
            'texto':       texto,
        }

        if tipo == 'grupo':
            # Solo a compañeros de equipo (incluido el remitente)
            canal = 'chat_grupal_azul' if group.es_azul(player) else 'chat_grupal_rojo'
            msgs  = json.loads(getattr(group, canal))
            msgs.append(msg)
            setattr(group, canal, json.dumps(msgs))
            destinatarios = [p.id_in_group for p in group.equipo(player)]
            return {pid: {**msg, 'canal': 'grupo'} for pid in destinatarios}

        elif tipo == 'privado':
            partner_id = int(data.get('partner_id', 0))
            # Validar que partner pertenece al mismo equipo
            equipo_ids = [p.id_in_group for p in group.equipo(player)]
            if partner_id not in equipo_ids or partner_id == player.id_in_group:
                return {}
            campo = group._campo_chat_privado(player.id_in_group, partner_id)
            msgs  = json.loads(getattr(group, campo))
            msgs.append(msg)
            setattr(group, campo, json.dumps(msgs))
            return {
                player.id_in_group: {**msg, 'canal': 'privado', 'partner_id': partner_id},
                partner_id:         {**msg, 'canal': 'privado', 'partner_id': partner_id},
            }

        return {}


class DecisionPage(Page):
    form_model = 'player'
    form_fields = ['frente_a', 'frente_b', 'frente_c', 'ahorro']
    timeout_seconds = C.DECISION_DURATION

    @staticmethod
    def is_displayed(player):
        return _visible(player) and player.round_number <= _ronda_max(player)

    @staticmethod
    def error_message(player, values):
        total = values['frente_a'] + values['frente_b'] + values['frente_c'] + values['ahorro']
        if total != C.TOKENS_PER_ROUND:
            return f'La suma debe ser exactamente {C.TOKENS_PER_ROUND} fichas (ahora sumas {total}).'

    @staticmethod
    def before_next_page(player, timeout_happened):
        # Si se agotó el tiempo, distribuir uniformemente
        if timeout_happened:
            player.frente_a = 4
            player.frente_b = 4
            player.frente_c = 4
            player.ahorro   = 3

    @staticmethod
    def vars_for_template(player):
        return dict(
            ronda=player.round_number,
            total_rondas=C.NUM_ROUNDS,
            color_equipo=player.color_equipo(),
            nombre_jugador=player.nombre(),
            tokens=C.TOKENS_PER_ROUND,
            acumulado=player.acumulado(),
        )


class EsperaDecision(WaitPage):
    title_text = 'Calculando resultados...'
    body_text  = 'Esperando que todos los jugadores tomen su decisión.'

    @staticmethod
    def after_all_players_arrive(group: Group):
        # En modo solo, auto-rellenar decisiones de jugadores de fondo (2-6)
        if group.get_players()[0].session.config.get('is_solo', False):
            for p in group.get_players():
                if p.id_in_group != 1:
                    ahorro = random.randint(0, 3)
                    resto  = C.TOKENS_PER_ROUND - ahorro
                    a = random.randint(0, resto)
                    b = random.randint(0, resto - a)
                    c = resto - a - b
                    p.frente_a, p.frente_b, p.frente_c, p.ahorro = a, b, c, ahorro
        group.calcular_resultados()


class ResultadosPage(Page):
    timeout_seconds = C.RESULTS_DURATION

    @staticmethod
    def is_displayed(player):
        return _visible(player) and player.round_number <= _ronda_max(player)

    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        equipo = group.equipo(player)
        rivales = group.rivales(player)
        equipo_gano = group.ganador_ronda == ('azul' if group.es_azul(player) else 'rojo')

        def fila(p):
            return NS(
                nombre=p.nombre(),
                es_yo=(p.id_in_group == player.id_in_group),
                frente_a=p.frente_a,
                frente_b=p.frente_b,
                frente_c=p.frente_c,
                ahorro=p.ahorro,
                premio=p.premio_ronda,
                ahorro_ef=p.ahorro_efectivo,
                ganancia=p.ganancia_ronda,
            )

        return dict(
            ronda=player.round_number,
            total_rondas=C.NUM_ROUNDS,
            color_equipo=player.color_equipo(),
            nombre_jugador=player.nombre(),
            equipo_gano=equipo_gano,
            ganador_ronda=group.ganador_ronda,
            frentes_list=[
                NS(frente='A', total_a=group.total_a_azul, total_r=group.total_a_rojo, ganador=group.ganador_a),
                NS(frente='B', total_a=group.total_b_azul, total_r=group.total_b_rojo, ganador=group.ganador_b),
                NS(frente='C', total_a=group.total_c_azul, total_r=group.total_c_rojo, ganador=group.ganador_c),
            ],
            # Tablas
            filas_propio=[fila(p) for p in sorted(equipo,  key=lambda x: x.id_in_group)],
            filas_rival =[fila(p) for p in sorted(rivales, key=lambda x: x.id_in_group)],
            acumulado=player.acumulado(),
        )


class CastigoPage(Page):
    form_model  = 'player'
    form_fields = ['voto_castigo']
    timeout_seconds = C.PUNISHMENT_DURATION

    @staticmethod
    def is_displayed(player):
        return _visible(player) and player.round_number <= _ronda_max(player)

    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        comp  = group.companeros(player)
        return dict(
            ronda=player.round_number,
            total_rondas=C.NUM_ROUNDS,
            color_equipo=player.color_equipo(),
            nombre_jugador=player.nombre(),
            companeros=[NS(id=c.id_in_group, nombre=c.nombre()) for c in comp],
            costo_castigo=C.PUNISHMENT_COST,
            penalizacion=C.PUNISHMENT_PENALTY,
            acumulado=player.acumulado(),
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.voto_castigo = 0


class EsperaCastigo(WaitPage):
    title_text = 'Procesando votos...'
    body_text  = 'Esperando que todos voten.'

    @staticmethod
    def after_all_players_arrive(group: Group):
        # En modo solo, auto-rellenar voto_castigo para jugadores de fondo
        if group.get_players()[0].session.config.get('is_solo', False):
            for p in group.get_players():
                if p.id_in_group != 1:
                    p.voto_castigo = 0
        group.calcular_castigo()


class EmocionPage(Page):
    form_model  = 'player'
    form_fields = ['ira_general', 'ira_comp1', 'ira_comp2', 'ira_rival']
    timeout_seconds = C.EMOTION_DURATION

    @staticmethod
    def is_displayed(player):
        return _visible(player) and player.round_number <= _ronda_max(player)

    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        comp  = group.companeros(player)
        castigo_json = json.loads(group.resultado_castigo)

        def info_castigo(p):
            votos = castigo_json.get(str(p.id_in_group), 0)
            return NS(nombre=p.nombre(), fue_castigado=p.fue_castigado, votos=votos)

        comp1_nombre = comp[0].nombre() if len(comp) > 0 else 'Compañero/a 1'
        comp2_nombre = comp[1].nombre() if len(comp) > 1 else 'Compañero/a 2'
        return dict(
            ronda=player.round_number,
            total_rondas=C.NUM_ROUNDS,
            color_equipo=player.color_equipo(),
            nombre_jugador=player.nombre(),
            yo_fui_castigado=player.fue_castigado,
            castigos=[info_castigo(p) for p in group.equipo(player)],
            acumulado=player.acumulado(),
            ganador_ronda=group.ganador_ronda,
            escala=list(range(1, 8)),
            preguntas=[
                NS(campo='ira_general', etiqueta='¿Qué tan enojado/a te sientes en este momento?'),
                NS(campo='ira_comp1',   etiqueta=f'¿Qué tan enojado/a estás con {comp1_nombre}?'),
                NS(campo='ira_comp2',   etiqueta=f'¿Qué tan enojado/a estás con {comp2_nombre}?'),
                NS(campo='ira_rival',   etiqueta='¿Qué tan enojado/a estás con el equipo rival?'),
            ],
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        # Si se agotó el tiempo, asignar valores medios
        if timeout_happened:
            if player.ira_general is None: player.ira_general = 4
            if player.ira_comp1   is None: player.ira_comp1   = 4
            if player.ira_comp2   is None: player.ira_comp2   = 4
            if player.ira_rival   is None: player.ira_rival   = 4


class EsperaRonda(WaitPage):
    title_text = 'Preparando siguiente ronda...'
    body_text  = 'Esperando que todos completen la encuesta emocional.'

    @staticmethod
    def is_displayed(player):
        return player.round_number < _ronda_max(player)


class PaginaFinal(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == _ronda_max(player) and _visible(player)

    @staticmethod
    def vars_for_template(player: Player):
        group = player.group

        # ── Historial y conteo de victorias por equipo ────────────────────────
        num_rondas = _ronda_max(player)
        historial = []
        azul_wins = 0
        rojo_wins = 0
        for r in range(1, num_rondas + 1):
            p_r = player.in_round(r)
            g_r = p_r.group
            ganador = g_r.ganador_ronda
            if ganador == 'azul':
                azul_wins += 1
            elif ganador == 'rojo':
                rojo_wins += 1
            historial.append(NS(
                ronda=r,
                ganador=ganador,
                ganancia=p_r.ganancia_ronda,
                fue_castigado=p_r.fue_castigado,
            ))

        # ── Ganador de la sesión ──────────────────────────────────────────────
        mi_equipo = player.color_equipo().lower()   # 'azul' o 'rojo'
        if azul_wins > rojo_wins:
            ganador_sesion = 'azul'
        elif rojo_wins > azul_wins:
            ganador_sesion = 'rojo'
        else:
            ganador_sesion = 'empate'

        mi_equipo_gana = (ganador_sesion == mi_equipo or ganador_sesion == 'empate')

        # ── Puntaje total del equipo (determina ranking entre ganadores) ───────
        mis_ids = C.AZUL_IDS if player.id_in_group in C.AZUL_IDS else C.ROJO_IDS
        equipo_players = [p for p in group.get_players() if p.id_in_group in mis_ids]
        total_equipo = round(sum(p.acumulado() for p in equipo_players), 1)

        # ── Ranking individual dentro del equipo (determina proporción de tickets)
        total_acum = sum(p.acumulado() for p in equipo_players)
        ranking_equipo = sorted(
            [NS(
                nombre=p.nombre(),
                acumulado=round(p.acumulado(), 1),
                porcentaje=round(p.acumulado() / total_acum * 100) if total_acum > 0 else 0,
                es_yo=(p.id_in_group == player.id_in_group),
            ) for p in equipo_players],
            key=lambda x: -x.acumulado,
        )

        return dict(
            color_equipo=player.color_equipo(),
            nombre_jugador=player.nombre(),
            acumulado_final=round(player.acumulado(), 1),
            historial=historial,
            azul_wins=azul_wins,
            rojo_wins=rojo_wins,
            ganador_sesion=ganador_sesion,
            mi_equipo_gana=mi_equipo_gana,
            total_equipo=total_equipo,
            ranking_equipo=ranking_equipo,
        )


# ─────────────────────────────────────────────────────────────────────────────
# SECUENCIA DE PÁGINAS
# ─────────────────────────────────────────────────────────────────────────────

page_sequence = [
    Instrucciones,
    Instrucciones2,
    PruebaPractica,
    PaginaSTAXI,
    EsperaInicio,
    ChatPage,
    DecisionPage,
    EsperaDecision,
    ResultadosPage,
    CastigoPage,
    EsperaCastigo,
    EmocionPage,
    EsperaRonda,
    PaginaFinal,
]
