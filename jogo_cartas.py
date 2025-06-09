import threading
import random
import time
import queue
import os

ORDEM = ['K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2', 'A']
NAIPES = ['♠', '♥', '♦', '♣']
NAIPE_INPUT = {'E': '♠', 'C': '♥', 'O': '♦', 'P': '♣'}
NAIPE_OUTPUT = {v: k for k, v in NAIPE_INPUT.items()}  # Reverse mapping for output

lock = threading.Lock()
turno = 0
tempo_turno = 50
jogo_ativo = True
vencedor = None

def limpar_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def criar_baralho():
    return [f"{valor}{naipe}" for valor in ORDEM for naipe in NAIPES]

def cartas_validas(mao, mesa):
    jogaveis = []
    for carta in mao:
        valor, naipe = carta[:-1], carta[-1]
        if not mesa[naipe]:
            if valor == 'K':
                jogaveis.append(carta)
        else:
            ultima = mesa[naipe][-1][:-1]
            if ORDEM.index(valor) == ORDEM.index(ultima) + 1:
                jogaveis.append(carta)
    return jogaveis

def desenhar_carta(carta, jogavel=False):
    """Desenha uma carta em 7x11 com margens fixas e destaque se jogável."""
    borda_sup = "┏━━━━━━━━━━━┓" if jogavel else "┌───────────┐"
    borda_inf = "┗━━━━━━━━━━━┛" if jogavel else "└───────────┘"
    borda_sup_pilha = "┌───────────┐"  # Para bordas de cartas empilhadas

    if not carta:
        return [
            borda_sup,
            "│           │",
            "│           │",
            "│   Vazio   │",
            "│           │",
            "│           │",
            borda_inf
        ], borda_sup_pilha
    valor, naipe = carta[:-1], carta[-1]
    valor_display = valor
    return [
        borda_sup,
        f"│ {valor_display:<2}      {naipe} │",
        "│           │",
        f"│     {naipe}     │",
        "│           │",
        f"│ {naipe}      {valor_display:>2} │",
        borda_inf
    ], borda_sup_pilha  # Retorna carta completa e borda para pilha

def imprimir_mesa(mesa):
    """Imprime a mesa com pilhas alinhadas, mostrando a carta do topo e bordas de cartas abaixo."""
    print("\n╔══════════════════════════════════ MESA ══════════════════════════════════╗")
    print("║    ♠                  ♥                  ♦                  ♣            ║")
    linhas_pilhas = []
    max_altura = 7  # Altura de uma carta

    for naipe in NAIPES:
        pilha = mesa[naipe]
        linhas = []
        if not pilha:
            linhas.extend(desenhar_carta(None)[0])
        else:
            num_abaixo = min(len(pilha) - 1, 3)
            carta_lines, borda_pilha = desenhar_carta(pilha[-1])
            for _ in range(num_abaixo):
                linhas.append(borda_pilha)
            linhas.extend(carta_lines)
        linhas_pilhas.append(linhas[:max_altura])

    for linhas in linhas_pilhas:
        while len(linhas) < max_altura:
            linhas.append(" " * 13)

    for i in range(max_altura):
        linha = "  ".join(pilha[i] for pilha in linhas_pilhas)
        print(f"║ {linha:^68} ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝\n")

def imprimir_mao(mao, validas):
    """Imprime a mão do jogador com cartas alinhadas, sem códigos de entrada."""
    if not mao:
        print("🃏 Sua mão: [Vazia]")
        return
    print("🃏 Sua mão (cartas com bordas grossas são jogáveis):")
    linhas_cartas = [desenhar_carta(carta, carta in validas)[0] for carta in mao]
    for i in range(7):
        linha = "  ".join(carta[i] for carta in linhas_cartas)
        print(f"  {linha}")

def imprimir_cartas_restantes(jogadores_maos):
    print("📊 Cartas restantes:")
    for idx, mao in enumerate(jogadores_maos):
        nome = f"Jogador {idx+1}" if idx == 0 else f"Bot {idx+1}"
        print(f"  {nome}: {len(mao)} carta(s)")
    print()

def jogador_humano(id_jogador, mao, mesa, jogadores, jogadores_maos):
    global turno, jogo_ativo, vencedor
    while jogo_ativo:
        if turno != id_jogador:
            time.sleep(1)
            continue

        with lock:
            limpar_terminal()
            print(f"🎮 Turno do Jogador {id_jogador + 1}")
            imprimir_mesa(mesa)
            imprimir_cartas_restantes(jogadores_maos)

            print(f"🎯 Sua vez! (Tempo: {tempo_turno}s)")
            validas = cartas_validas(mao, mesa)
            imprimir_mao(mao, validas)

            def jogada_bot_substituto():
                nonlocal mao
                validas_sub = cartas_validas(mao, mesa)
                if validas_sub:
                    carta = random.choice(validas_sub)
                    print(f"\n🤖 [Bot substituto] Jogou: {carta}")
                    mao.remove(carta)
                    mesa[carta[-1]].append(carta)
                else:
                    print(f"\n🤖 [Bot substituto] Passou a vez.")

            print("\n📥 Digite a carta (ex: KE para K♠, JO para J♦) ou 'passar')")

            input_queue = queue.Queue()

            def get_input():
                entrada = input("\nJogada: ").strip().upper()
                input_queue.put(entrada)

            thread_input = threading.Thread(target=get_input)
            thread_input.daemon = True
            thread_input.start()

            jogou = False
            start = time.time()

            while time.time() - start < tempo_turno:
                if not input_queue.empty():
                    entrada = input_queue.get()

                    if entrada == 'PASSAR':
                        if validas:
                            print("❌ Você tem cartas jogáveis! Tente novamente.")
                            thread_input = threading.Thread(target=get_input)
                            thread_input.daemon = True
                            thread_input.start()
                            continue
                        else:
                            print("✅ Passou a vez.")
                            break

                    if len(entrada) >= 2 and entrada[-1] in NAIPE_INPUT:
                        carta = entrada[:-1] + NAIPE_INPUT[entrada[-1]]
                    else:
                        carta = entrada

                    if carta in validas:
                        mao.remove(carta)
                        mesa[carta[-1]].append(carta)
                        jogou = True
                        print(f"✅ Jogou: {carta}")
                        break
                    else:
                        print("❌ Carta inválida. Tente novamente.")
                        thread_input = threading.Thread(target=get_input)
                        thread_input.daemon = True
                        thread_input.start()
                else:
                    time.sleep(0.1)

            if not jogou and validas:
                print("\n⏰ Tempo esgotado! Bot substituto joga.")
                jogada_bot_substituto()

            if not mao:
                print(f"\n🎉 Jogador {id_jogador + 1} venceu! 🏆")
                vencedor = f"Jogador {id_jogador + 1}"
                jogo_ativo = False
                return

            turno = (turno + 1) % len(jogadores)
        time.sleep(1)

def bot(id_jogador, mao, mesa, jogadores, jogadores_maos):
    global turno, jogo_ativo, vencedor
    while jogo_ativo:
        if turno != id_jogador:
            time.sleep(1)
            continue

        with lock:
            limpar_terminal()
            print(f"🎮 Turno do Bot {id_jogador + 1}")
            imprimir_mesa(mesa)
            imprimir_cartas_restantes(jogadores_maos)

            validas = cartas_validas(mao, mesa)
            time.sleep(1.5)

            if validas:
                carta = random.choice(validas)
                print(f"🤖 Bot {id_jogador + 1} jogou: {carta}")
                mao.remove(carta)
                mesa[carta[-1]].append(carta)
            else:
                print(f"🤖 Bot {id_jogador + 1} passou a vez.")

            if not mao:
                print(f"\n🏆 Bot {id_jogador + 1} venceu!")
                vencedor = f"Bot {id_jogador + 1}"
                jogo_ativo = False
                return

            turno = (turno + 1) % len(jogadores)
        time.sleep(1)

def exibir_regras():
    limpar_terminal()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                🃏 DOMINÓ DE CARTAS - REGRAS 🃏            ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║ - 4 jogadores (você + bots)                              ║")
    print("║ - Cada um recebe 13 cartas                               ║")
    print("║ - Mesa com 4 pilhas (♠ ♥ ♦ ♣)                           ║")
    print("║ - Regras para jogar:                                    ║")
    print("║   • Rei (K) inicia uma pilha vazia                      ║")
    print("║   • Carta deve ser do mesmo naipe e valor imediatamente ║")
    print("║     inferior ao topo (ex: Q sobre K)                    ║")
    print("║ - Tempo: 50 segundos por jogada                         ║")
    print("║ - Sem jogada no tempo? Bot joga por você                ║")
    print("║ - Vence quem descartar todas as cartas primeiro         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    input("\n🎮 Pressione Enter para começar...")

def jogar():
    global jogo_ativo, turno, vencedor

    while True:
        jogo_ativo = True
        turno = 0
        vencedor = None
        mesa = {naipe: [] for naipe in NAIPES}
        exibir_regras()

        while True:
            try:
                num_reais = int(input("Quantos jogadores reais? (1 a 4): "))
                if 1 <= num_reais <= 4:
                    break
                else:
                    print("⚠️ Digite um número entre 1 e 4.")
            except ValueError:
                print("⚠️ Entrada inválida. Tente novamente.")

        num_bots = 4 - num_reais

        baralho = criar_baralho()
        random.shuffle(baralho)
        maos = [baralho[i*13:(i+1)*13] for i in range(4)]
        jogadores = []

        for i in range(num_reais):
            t = threading.Thread(target=jogador_humano, args=(i, maos[i], mesa, list(range(4)), maos))
            jogadores.append(t)

        for i in range(num_bots):
            idx = i + num_reais
            t = threading.Thread(target=bot, args=(idx, maos[idx], mesa, list(range(4)), maos))
            jogadores.append(t)

        print(f"\n🃏 Jogo iniciado: {num_reais} jogador(es), {num_bots} bot(s).")

        for t in jogadores:
            t.start()
        for t in jogadores:
            t.join()

        print(f"\n🏁 Fim de jogo! {vencedor} venceu! 🏆")

        while True:
            resposta = input("\n🔄 Jogar novamente? (s/n): ").strip().lower()
            if resposta == 's':
                break
            elif resposta == 'n':
                print("\n👋 Até a próxima!")
                return
            else:
                print("⚠️ Digite 's' para sim ou 'n' para não.")

if __name__ == "__main__":
    jogar()