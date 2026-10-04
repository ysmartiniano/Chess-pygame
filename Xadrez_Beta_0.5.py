import pygame
import math
import random
from typing import List, Tuple, Optional

# --- CONSTANTES DE JOGO ---
VAZIO = 0
PEAO_B, CAVALO_B, BISPO_B, TORRE_B, RAINHA_B, REI_B = 1, 2, 3, 4, 5, 6
PEAO_P, CAVALO_P, BISPO_P, TORRE_P, RAINHA_P, REI_P = -1, -2, -3, -4, -5, -6

# Pontuação customizada
VALORES_PONTUACAO = {
    1: 10,   # Peão
    4: 20,   # Torre
    3: 30,   # Bispo
    2: 40,   # Cavalo
    5: 100,  # Rainha
    6: 360   # Rei (Soma do restante)
}

PST_CENTRO = [
    0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,
    0,  0, 10, 15, 15, 10,  0,  0,
    0,  0, 15, 25, 25, 15,  0,  0,
    0,  0, 15, 25, 25, 15,  0,  0,
    0,  0, 10, 15, 15, 10,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0
]

TEMAS = {
    "CLASSICO": {"clara": (235, 236, 208), "escura": (119, 149, 86), "destaque": (186, 202, 68), "selecao": (246, 246, 105)},
    "MADEIRA": {"clara": (240, 217, 181), "escura": (181, 136, 99), "destaque": (205, 210, 106), "selecao": (200, 170, 80)},
    "METAL": {"clara": (210, 215, 220), "escura": (100, 110, 120), "destaque": (140, 170, 190), "selecao": (150, 190, 210)}
}

# --- MOTOR DE REGRAS ---
class RegrasMovimento:
    __slots__ = ()
    DIRECOES_TORRE = (-8, 8, -1, 1)
    DIRECOES_BISPO = (-9, -7, 7, 9)
    SALTO_CAVALO = (-17, -15, -10, -6, 6, 10, 15, 17)

    @staticmethod
    def _valida_limite_e_borda(origem: int, destino: int, max_delta_coluna: int) -> bool:
        if not (0 <= destino < 64): return False
        return abs((destino & 7) - (origem & 7)) <= max_delta_coluna

    @classmethod
    def obter_pseudo_movimentos(cls, origem: int, estado: List[int]) -> List[int]:
        peca = estado[origem]
        if peca == VAZIO: return []
        cor = 1 if peca > 0 else -1
        tipo = abs(peca)
        movimentos = []

        if tipo == 1:
            frente = -8 if cor == 1 else 8
            if 0 <= origem + frente < 64 and estado[origem + frente] == VAZIO:
                movimentos.append(origem + frente)
                if (origem >> 3) == (6 if cor == 1 else 1) and estado[origem + (frente * 2)] == VAZIO:
                    movimentos.append(origem + (frente * 2))
            for diag in (frente - 1, frente + 1):
                dest = origem + diag
                if cls._valida_limite_e_borda(origem, dest, 1) and estado[dest] != VAZIO and (estado[dest] * cor < 0):
                    movimentos.append(dest)
        elif tipo == 2:
            for salto in cls.SALTO_CAVALO:
                dest = origem + salto
                if cls._valida_limite_e_borda(origem, dest, 2) and (estado[dest] == VAZIO or estado[dest] * cor < 0):
                    movimentos.append(dest)
        elif tipo in (3, 4, 5):
            dirs = []
            if tipo in (3, 5): dirs.extend(cls.DIRECOES_BISPO)
            if tipo in (4, 5): dirs.extend(cls.DIRECOES_TORRE)
            for d in dirs:
                atual = origem
                delta = 1 if abs(d) in (1, 7, 9) else 0
                while True:
                    prox = atual + d
                    if not cls._valida_limite_e_borda(atual, prox, delta): break
                    if estado[prox] == VAZIO: movimentos.append(prox)
                    else:
                        if estado[prox] * cor < 0: movimentos.append(prox)
                        break
                    atual = prox
        elif tipo == 6:
            for d in cls.DIRECOES_BISPO + cls.DIRECOES_TORRE:
                dest = origem + d
                delta = 1 if abs(d) in (1, 7, 9) else 0
                if cls._valida_limite_e_borda(origem, dest, delta) and (estado[dest] == VAZIO or estado[dest] * cor < 0):
                    movimentos.append(dest)
        return movimentos

    @classmethod
    def casa_sob_ataque(cls, casa: int, estado: List[int], cor_atacante: int) -> bool:
        for origem in range(64):
            if estado[origem] * cor_atacante > 0:
                if casa in cls.obter_pseudo_movimentos(origem, estado): return True
        return False

class Tabuleiro:
    __slots__ = ["estado", "pontos_brancas", "pontos_pretas"]
    def __init__(self) -> None:
        self.estado: List[int] = [VAZIO] * 64
        self.estado[0:8] = [TORRE_P, CAVALO_P, BISPO_P, RAINHA_P, REI_P, BISPO_P, CAVALO_P, TORRE_P]
        self.estado[8:16] = [PEAO_P] * 8
        self.estado[48:56] = [PEAO_B] * 8
        self.estado[56:64] = [TORRE_B, CAVALO_B, BISPO_B, RAINHA_B, REI_B, BISPO_B, CAVALO_B, TORRE_B]
        self.pontos_brancas = 0
        self.pontos_pretas = 0

    def encontrar_rei(self, cor: int) -> int:
        alvo = REI_B if cor == 1 else REI_P
        for i, peca in enumerate(self.estado):
            if peca == alvo: return i
        return -1

    def movimentos_estritamente_legais(self, cor: int) -> List[Tuple[int, int]]:
        movimentos_validos = []
        for origem in range(64):
            if self.estado[origem] * cor > 0:
                pseudos = RegrasMovimento.obter_pseudo_movimentos(origem, self.estado)
                for destino in pseudos:
                    p_m, p_c = self.estado[origem], self.estado[destino]
                    self.estado[destino], self.estado[origem] = p_m, VAZIO
                    pos_rei = self.encontrar_rei(cor)
                    if not RegrasMovimento.casa_sob_ataque(pos_rei, self.estado, -cor):
                        movimentos_validos.append((origem, destino))
                    self.estado[origem], self.estado[destino] = p_m, p_c
        return movimentos_validos

    def aplicar_movimento(self, origem: int, destino: int) -> int:
        peca_capturada = self.estado[destino]
        self.estado[destino] = self.estado[origem]
        self.estado[origem] = VAZIO
        
        # Sistema de Pontos
        if peca_capturada != VAZIO:
            valor = VALORES_PONTUACAO[abs(peca_capturada)]
            if self.estado[destino] > 0: self.pontos_brancas += valor
            else: self.pontos_pretas += valor
            
        return peca_capturada

    def checar_estado_partida(self, cor: int) -> str:
        movimentos = self.movimentos_estritamente_legais(cor)
        em_xeque = RegrasMovimento.casa_sob_ataque(self.encontrar_rei(cor), self.estado, -cor)

        if not movimentos:
            if em_xeque:
                # Bônus de Checkmate (360 pontos) para o vencedor
                if cor == 1: self.pontos_pretas += VALORES_PONTUACAO[6]
                else: self.pontos_brancas += VALORES_PONTUACAO[6]
                return "CHECKMATE"
            return "STALEMATE"
        return "CHECK" if em_xeque else "NORMAL"

class InteligenciaArtificial:
    __slots__ = ["nivel", "profundidade"]
    def __init__(self, nivel: int) -> None:
        self.nivel = nivel
        self.profundidade = nivel if nivel <= 3 else 4 

    def avaliar_posicao(self, estado: List[int]) -> float:
        pontuacao = 0.0
        for i, peca in enumerate(estado):
            if peca != VAZIO:
                valor_base = VALORES_PONTUACAO[abs(peca)]
                cor = 1 if peca > 0 else -1
                if self.nivel >= 3 and abs(peca) != 6:
                    valor_base += (PST_CENTRO[i if cor == 1 else 63 - i] * 0.1)
                pontuacao += valor_base if cor == 1 else -valor_base
        if self.nivel == 1: pontuacao += random.uniform(-5, 5)
        return pontuacao

    def minimax(self, tabuleiro: Tabuleiro, profundidade: int, alfa: float, beta: float, maximizando: bool) -> Tuple[float, Optional[Tuple[int, int]]]:
        if self.nivel == 1 and profundidade == 1:
            movs = tabuleiro.movimentos_estritamente_legais(1 if maximizando else -1)
            return (0, random.choice(movs)) if movs else (0, None)

        if profundidade == 0: return self.avaliar_posicao(tabuleiro.estado), None
            
        movimentos = tabuleiro.movimentos_estritamente_legais(1 if maximizando else -1)
        if not movimentos: return self.avaliar_posicao(tabuleiro.estado), None

        melhor_jogada = None
        if maximizando:
            max_eval = -math.inf
            for o, d in movimentos:
                p_m, p_c = tabuleiro.estado[o], tabuleiro.estado[d]
                tabuleiro.estado[d], tabuleiro.estado[o] = p_m, VAZIO
                aval, _ = self.minimax(tabuleiro, profundidade - 1, alfa, beta, False)
                tabuleiro.estado[o], tabuleiro.estado[d] = p_m, p_c
                if aval > max_eval: max_eval, melhor_jogada = aval, (o, d)
                alfa = max(alfa, aval)
                if beta <= alfa: break
            return max_eval, melhor_jogada
        else:
            min_eval = math.inf
            for o, d in movimentos:
                p_m, p_c = tabuleiro.estado[o], tabuleiro.estado[d]
                tabuleiro.estado[d], tabuleiro.estado[o] = p_m, VAZIO
                aval, _ = self.minimax(tabuleiro, profundidade - 1, alfa, beta, True)
                tabuleiro.estado[o], tabuleiro.estado[d] = p_m, p_c
                if aval < min_eval: min_eval, melhor_jogada = aval, (o, d)
                beta = min(beta, aval)
                if beta <= alfa: break
            return min_eval, melhor_jogada

# --- INTERFACE E CONTROLE (PYGAME) ---
pygame.init()

# Configurações Globais Iniciais
CONFIG = {
    "RESOLUCOES": [(1280, 720), (1920, 1080)],
    "RES_INDEX": 0,
    "TELA_CHEIA": False
}

def aplicar_resolucao() -> pygame.Surface:
    res = CONFIG["RESOLUCOES"][CONFIG["RES_INDEX"]]
    flags = pygame.FULLSCREEN if CONFIG["TELA_CHEIA"] else 0
    return pygame.display.set_mode(res, flags)

TELA = aplicar_resolucao()
pygame.display.set_caption("Xadrez - Master Edition")

UNICODE_PECAS = {1: "♙", 2: "♘", 3: "♗", 4: "♖", 5: "♕", 6: "♔", -1: "♟", -2: "♞", -3: "♝", -4: "♜", -5: "♛", -6: "♚"}

def get_fontes(tamanho_base: int):
    fator = TELA.get_height() / 720.0
    return {
        "titulo": pygame.font.SysFont("arial", int(48 * fator), bold=True),
        "padrao": pygame.font.SysFont("arial", int(tamanho_base * fator), bold=True),
        "tutorial": pygame.font.SysFont("arial", int(18 * fator), bold=False),
        "pecas": pygame.font.SysFont("segoeuisymbol", int((TELA.get_height() * 0.8 / 8) * 0.75))
    }

def desenhar_texto_centralizado(tela, texto, fonte, cor, y, x_offset=0):
    txt_surface = fonte.render(texto, True, cor)
    rect = txt_surface.get_rect(center=(tela.get_width()//2 + x_offset, y))
    tela.blit(txt_surface, rect)

def renderizar_tutorial(tela, fontes):
    s = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
    s.fill((20, 20, 30, 230))
    tela.blit(s, (0,0))
    
    desenhar_texto_centralizado(tela, "TUTORIAL DE MOVIMENTAÇÃO", fontes["padrao"], (255, 200, 100), 100)
    
    instrucoes = [
        "PEÃO (10 pts): Move 1 casa para frente. Captura peças na diagonal. No 1º movimento pode andar 2 casas.",
        "TORRE (20 pts): Move quantas casas quiser em linhas retas (Horizontal e Vertical).",
        "BISPO (30 pts): Move quantas casas quiser nas diagonais.",
        "CAVALO (40 pts): Move em 'L' (Duas casas numa direção, uma na outra). É a única peça que pula obstáculos.",
        "RAINHA (100 pts): A peça mais forte. Move em todas as direções (Combinação de Torre e Bispo).",
        "REI (360 pts): Move apenas 1 casa em qualquer direção. Perder o Rei significa perder o jogo."
    ]
    
    inicio_y = 200
    espaco = 60 * (tela.get_height() / 720.0)
    for i, linha in enumerate(instrucoes):
        txt = fontes["tutorial"].render(linha, True, (255, 255, 255))
        tela.blit(txt, (tela.get_width() * 0.1, inicio_y + (i * espaco)))
        
    desenhar_texto_centralizado(tela, "Pressione 'T' novamente para voltar", fontes["padrao"], (150, 150, 150), tela.get_height() - 100)

def menu_configuracoes():
    global TELA  # Correção aplicada aqui para evitar erro de escopo global
    fontes = get_fontes(24)
    rodando = True
    while rodando:
        TELA.fill((30, 30, 35))
        LARGURA, ALTURA = TELA.get_size()
        desenhar_texto_centralizado(TELA, "CONFIGURAÇÕES DE VÍDEO", fontes["titulo"], (255, 255, 255), ALTURA * 0.15)

        opcoes = [
            (f"Resolução: {CONFIG['RESOLUCOES'][CONFIG['RES_INDEX']][0]}x{CONFIG['RESOLUCOES'][CONFIG['RES_INDEX']][1]}", "RES"),
            (f"Modo: {'TELA CHEIA' if CONFIG['TELA_CHEIA'] else 'JANELA'}", "MODO"),
            ("Voltar ao Menu Principal", "VOLTAR")
        ]

        botoes = []
        for i, (texto, acao) in enumerate(opcoes):
            rect = pygame.Rect(LARGURA//2 - 250, ALTURA * 0.4 + (i * 80), 500, 60)
            botoes.append((rect, acao))
            cor_btn = (100, 150, 200) if rect.collidepoint(pygame.mouse.get_pos()) else (70, 110, 150)
            pygame.draw.rect(TELA, cor_btn, rect, border_radius=8)
            txt = fontes["padrao"].render(texto, True, (255, 255, 255))
            TELA.blit(txt, txt.get_rect(center=rect.center))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, acao in botoes:
                    if rect.collidepoint(event.pos):
                        if acao == "RES":
                            CONFIG["RES_INDEX"] = (CONFIG["RES_INDEX"] + 1) % len(CONFIG["RESOLUCOES"])
                            TELA = aplicar_resolucao()
                            fontes = get_fontes(24) 
                        elif acao == "MODO":
                            CONFIG["TELA_CHEIA"] = not CONFIG["TELA_CHEIA"]
                            TELA = aplicar_resolucao()
                        elif acao == "VOLTAR":
                            return

def menu_principal() -> Tuple[int, str]:
    fontes = get_fontes(24)
    nivel = 0
    tema = ""
    
    while True:
        TELA.fill((40, 40, 45))
        LARGURA, ALTURA = TELA.get_size()
        desenhar_texto_centralizado(TELA, "XADREZ", fontes["titulo"], (255, 255, 255), ALTURA * 0.15)
        
        opcoes = [("Jogar", "JOGAR"), ("Configurações", "CONFIG"), ("Sair", "SAIR")]
        botoes = []
        for i, (texto, acao) in enumerate(opcoes):
            rect = pygame.Rect(LARGURA//2 - 200, ALTURA * 0.4 + (i * 80), 400, 60)
            botoes.append((rect, acao))
            cor_btn = (100, 150, 200) if rect.collidepoint(pygame.mouse.get_pos()) else (70, 110, 150)
            pygame.draw.rect(TELA, cor_btn, rect, border_radius=8)
            txt = fontes["padrao"].render(texto, True, (255, 255, 255))
            TELA.blit(txt, txt.get_rect(center=rect.center))
            
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, acao in botoes:
                    if rect.collidepoint(event.pos):
                        if acao == "SAIR": pygame.quit(); exit()
                        elif acao == "CONFIG": menu_configuracoes(); fontes = get_fontes(24)
                        elif acao == "JOGAR":
                            niveis = [("Iniciante", 1), ("Amador", 2), ("Avançado", 3), ("Mestre", 4)]
                            nivel = menu_selecao("DIFICULDADE", niveis, fontes)
                            temas = [("Clássico", "CLASSICO"), ("Madeira", "MADEIRA"), ("Metal", "METAL")]
                            tema = menu_selecao("TEMA DO TABULEIRO", temas, fontes)
                            return nivel, tema

def menu_selecao(titulo: str, opcoes: list, fontes) -> any:
    while True:
        TELA.fill((40, 40, 45))
        LARGURA, ALTURA = TELA.get_size()
        desenhar_texto_centralizado(TELA, titulo, fontes["titulo"], (255, 255, 255), ALTURA * 0.15)
        
        botoes = []
        for i, (texto, valor) in enumerate(opcoes):
            rect = pygame.Rect(LARGURA//2 - 200, ALTURA * 0.35 + (i * 70), 400, 50)
            botoes.append((rect, valor))
            cor_btn = (100, 150, 200) if rect.collidepoint(pygame.mouse.get_pos()) else (70, 110, 150)
            pygame.draw.rect(TELA, cor_btn, rect, border_radius=8)
            txt = fontes["padrao"].render(texto, True, (255, 255, 255))
            TELA.blit(txt, txt.get_rect(center=rect.center))
            
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, valor in botoes:
                    if rect.collidepoint(event.pos): return valor

def iniciar_jogo():
    nivel_ia, tema_escolhido = menu_principal()
    fontes = get_fontes(24)
    jogo = Tabuleiro()
    ia = InteligenciaArtificial(nivel_ia)
    
    rodando = True
    turno_jogador = True
    pausado = False
    mostrar_tutorial = False
    estado_atual = "NORMAL"
    casa_selecionada = None
    mov_legais = []
    contador_rei_branco = 0
    contador_rei_preto = 0
    relogio = pygame.time.Clock()

    while rodando:
        LARGURA, ALTURA = TELA.get_size()
        BOARD_SIZE = int(ALTURA * 0.8)
        TAM_CASA = BOARD_SIZE // 8
        OFFSET_X = (LARGURA - BOARD_SIZE) // 2
        OFFSET_Y = (ALTURA - BOARD_SIZE) // 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT: rodando = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and estado_atual in ("NORMAL", "CHECK") and not mostrar_tutorial:
                    pausado = not pausado
                elif event.key == pygame.K_t and pausado:
                    mostrar_tutorial = not mostrar_tutorial
                elif event.key == pygame.K_ESCAPE:
                    if estado_atual not in ("NORMAL", "CHECK"): rodando = False
                    elif mostrar_tutorial: mostrar_tutorial = False
                    elif pausado: pausado = False

            elif event.type == pygame.MOUSEBUTTONDOWN and turno_jogador and not pausado:
                if event.button == 1:
                    mx, my = event.pos
                    if OFFSET_X <= mx < OFFSET_X + BOARD_SIZE and OFFSET_Y <= my < OFFSET_Y + BOARD_SIZE:
                        col = (mx - OFFSET_X) // TAM_CASA
                        lin = (my - OFFSET_Y) // TAM_CASA
                        idx = lin * 8 + col
                        
                        if casa_selecionada is not None and idx in mov_legais:
                            peca_capt = jogo.aplicar_movimento(casa_selecionada, idx)
                            if sum(1 for p in jogo.estado if p > 0) == 1:
                                contador_rei_branco = 0 if peca_capt != VAZIO else contador_rei_branco + 1
                            
                            turno_jogador = False
                            casa_selecionada = None
                            mov_legais = []
                            
                            if contador_rei_branco >= 10: estado_atual = "DERROTA_BRANCAS_EXAUSTAO"
                            else: estado_atual = jogo.checar_estado_partida(-1)
                        
                        elif jogo.estado[idx] > 0:
                            casa_selecionada = idx
                            validos = jogo.movimentos_estritamente_legais(1)
                            mov_legais = [d for o, d in validos if o == idx]
                        else:
                            casa_selecionada = None
                            mov_legais = []
                    else:
                        casa_selecionada = None
                        mov_legais = []

        # --- RENDERIZAÇÃO ---
        TELA.fill((30, 30, 35))
        
        hud_cor = (200, 200, 200)
        txt_p_brancas = fontes["padrao"].render(f"PONTOS (Você): {jogo.pontos_brancas}", True, hud_cor)
        txt_p_pretas = fontes["padrao"].render(f"PONTOS (I.A): {jogo.pontos_pretas}", True, hud_cor)
        
        TELA.blit(txt_p_brancas, (50, OFFSET_Y + BOARD_SIZE - 50))
        TELA.blit(txt_p_pretas, (50, OFFSET_Y))

        cores = TEMAS[tema_escolhido]
        for linha in range(8):
            for col in range(8):
                idx = linha * 8 + col
                px = OFFSET_X + col * TAM_CASA
                py = OFFSET_Y + linha * TAM_CASA
                
                cor_casa = cores["clara"] if (linha + col) % 2 == 0 else cores["escura"]
                if idx == casa_selecionada: cor_casa = cores["selecao"]
                elif idx in mov_legais: cor_casa = cores["destaque"]
                    
                pygame.draw.rect(TELA, cor_casa, (px, py, TAM_CASA, TAM_CASA))
                
                if estado_atual == "CHECK" and jogo.estado[idx] == REI_B:
                    pygame.draw.rect(TELA, (255, 60, 60), (px, py, TAM_CASA, TAM_CASA), max(2, int(TAM_CASA * 0.05)))
                
                peca = jogo.estado[idx]
                if peca != VAZIO:
                    simbolo = UNICODE_PECAS[peca]
                    cor_p = (255, 255, 255) if peca > 0 else (20, 20, 20)
                    cor_s = (40, 40, 40) if peca > 0 else (220, 220, 220)
                    
                    txt_sombra = fontes["pecas"].render(simbolo, True, cor_s)
                    TELA.blit(txt_sombra, txt_sombra.get_rect(center=(px + TAM_CASA//2 + 2, py + TAM_CASA//2 + 3)))
                    txt = fontes["pecas"].render(simbolo, True, cor_p)
                    TELA.blit(txt, txt.get_rect(center=(px + TAM_CASA//2, py + TAM_CASA//2)))

        if pausado:
            if mostrar_tutorial:
                renderizar_tutorial(TELA, fontes)
            else:
                s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                s.fill((0, 0, 0, 180))
                TELA.blit(s, (0,0))
                desenhar_texto_centralizado(TELA, "JOGO PAUSADO", fontes["titulo"], (255, 255, 255), ALTURA//2 - 40)
                desenhar_texto_centralizado(TELA, "Pressione 'P' para Voltar | 'T' para Tutorial", fontes["padrao"], (200, 200, 200), ALTURA//2 + 30)
                
        elif estado_atual not in ("NORMAL", "CHECK"):
            msg = ""
            if estado_atual == "CHECKMATE": msg = "XEQUE-MATE!"
            elif estado_atual == "STALEMATE": msg = "AFOGAMENTO (EMPATE)!"
            elif estado_atual == "DERROTA_BRANCAS_EXAUSTAO": msg = "DERROTA: REI EXAUSTO!"
            elif estado_atual == "DERROTA_PRETAS_EXAUSTAO": msg = "VITÓRIA: I.A. EXAUSTA!"

            s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            TELA.blit(s, (0,0))
            desenhar_texto_centralizado(TELA, msg, fontes["titulo"], (255, 80, 80), ALTURA//2 - 40)
            desenhar_texto_centralizado(TELA, "Pressione ESC para sair", fontes["padrao"], (200, 200, 200), ALTURA//2 + 40)

        pygame.display.flip()

        if not turno_jogador and not pausado and estado_atual in ("NORMAL", "CHECK"):
            _, jogada = ia.minimax(jogo, ia.profundidade, -math.inf, math.inf, False)
            if jogada:
                o, d = jogada
                peca_capt = jogo.aplicar_movimento(o, d)
                
                if sum(1 for p in jogo.estado if p < 0) == 1:
                    contador_rei_preto = 0 if peca_capt != VAZIO else contador_rei_preto + 1
                
                if contador_rei_preto >= 10: estado_atual = "DERROTA_PRETAS_EXAUSTAO"
                else: estado_atual = jogo.checar_estado_partida(1)
            else:
                estado_atual = jogo.checar_estado_partida(-1)
            
            turno_jogador = True

        relogio.tick(60)

if __name__ == "__main__":
    while True:
        iniciar_jogo()
