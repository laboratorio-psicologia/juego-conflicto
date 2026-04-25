import random
from otree.api import Bot, Submission
from . import (
    C,
    Instrucciones, Instrucciones2, PruebaPractica, PaginaSTAXI,
    ChatPage, DecisionPage, ResultadosPage, CastigoPage, EmocionPage, PaginaFinal,
)

# ── Banco de mensajes grupales: apertura de conversación ─────────────────────

FRASES_GRUPO_APERTURA = [
    "Buenas a todos. Antes de que empiece el tiempo, quería proponer que nos coordinemos bien esta ronda. En la ronda anterior creo que cada uno hizo lo suyo sin avisarse y eso nos costó caro. Si coordinamos un frente fuerte tenemos muchas más chances de ganar. ¿Qué dicen?",

    "Hola equipo. He estado pensando en la estrategia y creo que lo más inteligente es concentrar las fichas en un solo frente en vez de distribuirlas entre los tres. Si los tres ponemos la mayoría en el mismo frente, es casi imposible que el rival nos gane ahí. El problema es que si ellos adivinan cuál es, nos bloquean. Necesito saber qué piensan para decidir.",

    "¡Hola! Empecemos a hablar de estrategia antes de que se nos acabe el tiempo. Lo que me funcionó en otras rondas es apostar fuerte en un frente y guardar algo de ahorro por si perdemos. ¿Tienen preferencia por el frente A, B o C esta vez? Yo me adapto a lo que decida el grupo.",

    "Equipo, hay que organizarse bien esta vez. Me parece que el equipo contrario también va a intentar coordinar, así que tenemos que ser más listos que ellos. Propongo que nos pongamos de acuerdo en UN frente y que los tres metamos la mayoría de las fichas ahí. Alguien ¿tiene una idea de cuál?",

    "Buenos días o tardes según donde estén jaja. Veamos, tenemos quince fichas cada uno. Si los tres concentramos en el frente A, ponemos 45 fichas ahí y el rival tiene que meter más de 45 para ganarnos — eso es difícil para ellos. ¿Les parece bien ir todos al A esta ronda?",

    "Hola. Quiero ser honesto con el equipo: no sé exactamente qué va a hacer el rival, pero si repetimos la estrategia de la ronda pasada creo que volvemos a perder. Necesitamos cambiar algo. ¿Alguien tiene un plan distinto? Estoy abierto a escuchar antes de decidir.",

    "¿Alguien más está cansado de perder? jaja. En serio, creo que la clave está en la coordinación. Si cada uno se va por su cuenta, el rival nos supera en todos los frentes. Pero si los tres vamos juntos a uno solo, lo ganamos seguro. La pregunta es cuál elegimos y si podemos confiar en que todos cumplan.",

    "Oigan, tengo una propuesta. Que alguien de nosotros actúe de 'coordinador' esta ronda: él elige el frente y los demás seguimos. Así no hay confusión. ¿Quién quiere tomar esa responsabilidad? Yo puedo hacerlo si quieren, pero también acepto seguir si alguien tiene mejor información.",
]

# ── Mensajes de estrategia ────────────────────────────────────────────────────

FRASES_GRUPO_ESTRATEGIA = [
    "Yo voy a meter la mayoría al frente B. Creo que el rival no espera que nos concentremos ahí y podríamos sorprenderlos. Guardaré 2 o 3 fichas de ahorro por si acaso. ¿Alguien más va al B?",

    "Mi plan es distribuir así: 10 al A, 3 al B, 2 al C. El A me parece el más importante porque si lo ganamos y uno de los otros también, ganamos la ronda. Claro que esto depende de que ustedes también pongan algo ahí.",

    "Pensándolo bien, creo que vale más la pena apostar todo en un frente que distribuir parejo. Con 15 fichas cada uno y tres jugadores, si los tres vamos al mismo tenemos 45 fichas concentradas — es mucho. Yo voy al frente que digan la mayoría.",

    "Esta ronda voy a intentar algo distinto: pongo todo al frente C y nada de ahorro. Sé que es arriesgado, pero si ganamos el C y alguno de ustedes gana el A o el B, tenemos la ronda. La última vez jugué demasiado conservador y no ayudé al equipo.",

    "Propuesta concreta: el que tiene más experiencia en este tipo de juegos elija el frente. Yo confío en el criterio del equipo. Si me dicen voy al A, voy al A. Si me dicen voy al C, voy al C. Solo necesito saber antes de que termine el tiempo del chat.",

    "Lo que veo es que el frente A es donde más se concentra la gente normalmente, así que el rival también va a ir ahí. Por eso mi propuesta es atacar el B o el C donde quizás tienen menos fichas. ¿Qué piensan? Me parece que pensar lo contrario a lo obvio nos da ventaja.",

    "Para ser transparente: yo voy a guardar 3 fichas de ahorro y el resto lo meto en el frente A. Es mi estrategia personal, pero si el grupo prefiere otro frente puedo cambiar. Lo importante es que coordinemos y no que todos hagan lo mismo que yo.",

    "Seamos honestos: si no coordinamos, el otro equipo nos va a ganar aunque tengamos buenas intenciones individuales. Mi voto es por concentrar todos en el frente B. Digan si están de acuerdo antes de que se acabe el tiempo.",
]

# ── Mensajes de reacción (rondas 2+) ─────────────────────────────────────────

FRASES_GRUPO_REACCION = [
    "Uf, esa ronda estuvo difícil. Creo que nos faltó coordinación en el frente donde más apostamos. ¿Alguien puede contarme qué pasó? Para la próxima ronda necesito entender mejor cómo están distribuyendo el otro equipo.",

    "¡Bien jugado equipo! Eso es lo que pasa cuando coordinamos bien — los superamos claramente en el frente fuerte. Sigamos con esta estrategia, aunque quizás cambiemos el frente para que no nos adivinen.",

    "Nos ganaron esa ronda, hay que admitirlo. Pero creo que podemos remontar si ajustamos la estrategia. ¿Qué frente creen que el equipo contrario va a atacar esta vez? Si podemos anticiparlo, les ganamos dos frentes con menos esfuerzo.",

    "La ronda pasada perdimos por poco — creo que si uno o dos de nosotros hubiera puesto unas fichas más en el frente A, lo ganábamos. Hay que ser más agresivos esta vez y no quedarse con demasiado ahorro cuando el equipo lo necesita.",

    "Interesante esa ronda. Vi que el equipo rival distribuyó bastante parejo entre los tres frentes. Si eso se repite, con que concentremos bien en uno o dos frentes los ganamos fácil. ¿Qué estrategia usamos?",

    "Empate en la ronda pasada. No es lo que queríamos pero tampoco es un desastre. Esta ronda hay que definir bien la estrategia antes de que empiece la cuenta regresiva y no improvisar.",

    "Creo que el rival va a cambiar de táctica esta ronda después de lo que pasó. Hay que anticiparse. Yo propongo que nos concentremos en el frente donde ellos pusieron menos fichas en la ronda pasada. ¿Recuerdan cuál fue?",

    "Hay que mantenerse positivos aunque la ronda anterior no salió bien. Todavía tenemos varias rondas para recuperar puntos. Esta vez propongo ser más arriesgados — menos ahorro, más fichas en los frentes. ¿Están de acuerdo?",
]

# ── Mensajes privados ─────────────────────────────────────────────────────────

FRASES_PRIVADAS = [
    "Oye, te escribo en privado porque no quiero que el otro lo sepa todavía. Mi plan es meter casi todo al frente B, pero en el chat grupal dije que iba al A para despistar. ¿Tú qué vas a hacer? Si los dos vamos al B lo ganamos seguro.",

    "Tengo una propuesta que solo quiero decirte a ti. ¿Qué tal si nos coordinamos los dos en el frente C y dejamos que el tercero haga lo que quiera? Si tú y yo metemos 12 o 13 cada uno al C, el rival no puede con nosotros ahí. Y el A o el B también los podemos ganar con lo que ponga el tercer compañero.",

    "Aquí en confianza: creo que J3 no está cooperando bien con el equipo. En las rondas anteriores parecía que iba por su cuenta. ¿Tú lo notas también? Creo que si no cambia, deberíamos considerar votarle el castigo si sigue así.",

    "¿Cuánto vas a guardar de ahorro esta ronda? Yo estoy pensando en 3 o 4 fichas. No me gusta quedarme sin nada si perdemos la ronda — perder el 50% del ahorro duele. Pero tampoco quiero poner tan poco en los frentes que no aporte nada al equipo.",

    "Te cuento mi estrategia real, sin filtros: voy al frente A con 11 fichas, 1 al B, 1 al C y 2 de ahorro. Sé que es arriesgado concentrar tanto, pero si tú también vas fuerte al A lo ganamos con mucho margen. ¿Puedes ir al menos con 8 o 9 al A también?",

    "Oye, ¿cómo ves el ambiente del equipo esta ronda? A mí me parece que podemos coordinarnos bien si nos ponemos de acuerdo tú y yo primero, y luego el tercero se suma. En el chat grupal a veces la gente se dispersa con propuestas distintas y al final nadie se coordina con nadie.",

    "Aquí entre nosotros: si perdemos esta ronda voy a votar para castigar a alguien que no cooperó. No sé si tú harías lo mismo, pero creo que hay que mandar un mensaje cuando alguien no cumple lo que dice en el chat. ¿Qué piensas tú?",

    "Tengo curiosidad: ¿cuánto llevas acumulado hasta ahora? Yo no llevo tanto como quisiera. Esta ronda me importa mucho ganar para recuperar un poco. Por eso quiero coordinar bien contigo antes de tomar la decisión. ¿Tienes alguna preferencia de frente?",
]


def _companeros_ids(mi_id):
    equipo = [1, 2, 3] if mi_id in [1, 2, 3] else [4, 5, 6]
    return [p for p in equipo if p != mi_id]


class PlayerBot(Bot):
    """Bot con conversaciones largas y realistas. El chat se inyecta en
    ChatPage.before_next_page (browser bots no soportan liveSend)."""

    def play_round(self):
        mi_id = self.player.id_in_group

        # ── Ronda 1: instrucciones (2 páginas) + práctica + STAXI ─────────────
        if self.round_number == 1:
            yield Instrucciones
            yield Instrucciones2
            yield PruebaPractica

            staxi = {}
            for i in range(1, 11):
                staxi[f'staxi_r{i:02d}'] = random.randint(1, 4)
            for i in range(1, 9):
                staxi[f'staxi_ai{i}'] = random.randint(1, 4)
                staxi[f'staxi_ao{i}'] = random.randint(1, 4)
                staxi[f'staxi_ac{i}'] = random.randint(1, 4)
            yield PaginaSTAXI, staxi

        # ── Chat (los mensajes largos los inyecta before_next_page) ───────────
        yield Submission(ChatPage, check_html=False)

        # ── Decisión: estrategia con sesgo hacia concentración ────────────────
        if random.random() < 0.40:
            fuerte = random.randint(9, 13)
            resto = C.TOKENS_PER_ROUND - fuerte
            segundo = random.randint(0, resto)
            tercero = resto - segundo
            dists = [fuerte, segundo, tercero]
            random.shuffle(dists)
            a, b, c = dists
            ahorro = 0
        else:
            ahorro = random.randint(0, 4)
            resto = C.TOKENS_PER_ROUND - ahorro
            a = random.randint(0, resto)
            b = random.randint(0, resto - a)
            c = resto - a - b

        yield DecisionPage, dict(frente_a=a, frente_b=b, frente_c=c, ahorro=ahorro)

        # ── Resultados ────────────────────────────────────────────────────────
        yield Submission(ResultadosPage, check_html=False)

        # ── Castigo: ~20 % vota contra un compañero ───────────────────────────
        if random.random() < 0.20:
            voto = random.choice(_companeros_ids(mi_id))
        else:
            voto = 0
        yield CastigoPage, dict(voto_castigo=voto)

        # ── Emoción: correlacionada con castigo y resultado ───────────────────
        fue_castigado = getattr(self.player, 'fue_castigado', False)
        ganador_ronda = getattr(self.player.group, 'ganador_ronda', '')
        equipo_color  = 'azul' if mi_id in C.AZUL_IDS else 'rojo'
        equipo_gano   = (ganador_ronda == equipo_color)

        base_ira = 3
        if fue_castigado:
            base_ira += 2
        if not equipo_gano and ganador_ronda != 'empate':
            base_ira += 1

        def ira(extra=0):
            return min(7, max(1, base_ira + extra + random.randint(-1, 1)))

        yield EmocionPage, dict(
            ira_general=ira(),
            ira_comp1=ira(1 if fue_castigado else 0),
            ira_comp2=ira(1 if fue_castigado else 0),
            ira_rival=ira(1 if not equipo_gano else -1),
        )

        # ── Página final ──────────────────────────────────────────────────────
        if self.round_number == C.NUM_ROUNDS:
            yield Submission(PaginaFinal, check_html=False)
