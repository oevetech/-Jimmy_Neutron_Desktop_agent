# Resumo do projeto — Jimmy Neutron Desktop Pet

> Documento de passagem de contexto para outra IA (atualizado em 2026-10-24).
> Escrito para quem vai continuar o trabalho entender o que existe, como funciona e onde paramos.

## 1. O que é

Pet de desktop para Windows: o **Jimmy Neutron** e o **Goddard** andam em cima da barra de tarefas,
voam de foguete, recebem visitas dos amigos, lembram de beber água etc. Feito em **Python 3.14 + PyQt6**,
empacotado em `.exe` com **PyInstaller**. Interface e falas em **português** (com tradução para inglês).

- Pasta: `C:\Users\everaldolima\jimmy-neutron-pet`
- Repositório: https://github.com/oevetech/-Jimmy_Neutron_Desktop_agent (branch `main`)
- Última versão publicada: **v1.1** (`APP_VERSAO = "1.1"` em `jimmy_pet.py`, linha ~214)
- Lista completa de recursos para o usuário: `README.md`

## 2. Estrutura dos arquivos

| Arquivo / pasta | Função |
|---|---|
| `jimmy_pet.py` | **Todo o programa** (~6.700 linhas, um arquivo só). |
| `instalador_jimmy.py` | Instalador (tkinter) que copia o `.exe` para o PC do usuário. |
| `build.ps1` | Gera `dist\JimmyNeutronPet.exe` e `dist\Instalar Jimmy Neutron Pet.exe`. |
| `JimmyNeutronPet.spec` | Spec do PyInstaller (inclui `assets/`). |
| `assets/extracted/` | Folhas de sprites originais (PNG/JPG geradas pelo usuário). |
| `assets/anim/<nome>/00.png, 01.png…` | Quadros recortados de cada animação + `meta.json` (`{"box": tamanho}`). |
| `assets/anim_config.json` | Diz qual figura de cada folha vira qual animação. |
| `assets/extract_frames.py` | Recortador: lê `anim_config.json` e gera `assets/anim/`. |
| `assets/sons/`, `assets/gerar_sons.py` | Efeitos sonoros. |

### Classes principais em `jimmy_pet.py`

- `Pet` (base): janela transparente sem borda; `show_anim(anim, i, flip)`, `frame()`, `has_anim()`, `ground_y`.
- `Jimmy`, `Goddard`, `Rocket`: personagens fixos. O `Jimmy` tem uma máquina de estados (`state`, `sequence_state`).
- `Friend`: amigo que chega andando, conversa (roteiros em `CONVERSAS`) e vai embora. Chaves: `carl`, `sheen`, `libby`, `cindy`.
  Animações com o nome `amigo_<nome>_<tipo>` (`anda`, `parado`, `fala`, `acena`, `aponta`, `ri`, `pula`, `corre`).
- `Runner`: atravessa a tela correndo (lhama fugindo, Carl atrás).
- `CarlResgate`, `Planeta`, `LhamaCarona`: evento de resgate da lhama no planeta.
- `ModoGame`: jogo de nave (setas, espaço, Enter, P, Esc), com aliens e o chefe Rei Goobot.
- `Meteoro`: chuva de meteoros clicável.
- `TrayManager`: o "cérebro": ícone da bandeja, timers, sorteia eventos (`check_friend`, `solta_lhamas`,
  `start_resgate`, `spawn_friend`, `start_meteoros`…). Global `MANAGER`.
- `Configuracoes`: janela de configurações. Configuração salva em `%APPDATA%\JimmyNeutronPet` (dicionário `CFG`).

## 3. Como adicionar/alterar animações

1. O usuário gera uma folha de sprites (de preferência **PNG com fundo transparente**, figuras separadas por espaço vazio)
   e coloca em `assets/extracted/`.
2. Conferir a numeração das figuras: `python assets/extract_frames.py assets/extracted/folha.png`
   (gera `folha_conferencia.png` com os números).
3. Criar a entrada em `assets/anim_config.json`, por exemplo:
   ```json
   "extracted/folha.png": {
     "box": 150,
     "animations": { "amigo_sheen_ultralord": { "frames": [0, 1, 2, 3] } }
   }
   ```
   Opções úteis da folha: `sem_baloes` (apaga balões de fala), `buracos` (apaga branco preso numa faixa de altura),
   `limpar_pontos` (apaga a mancha branca que contém cada ponto `[x, y]`, por quadro, veja abaixo), `fill`, `lado_usados`, `grade`.
4. Rodar `python assets/extract_frames.py` (sem argumentos reprocessa **todas** as folhas; para uma só, importar o módulo
   e chamar `export(nome, spec)`).

## 4. Histórico (commits)

| Commit | O que foi feito |
|---|---|
| `37541e7` | v1.0 do pet. |
| `850eee9` | Goddard bichinho virtual, chuva de meteoros, contagens regressivas, menu de clique, manutenção do foguete. |
| `bcf9866` | **v1.1 (publicada)**: Modo Game, aliens, resgate da lhama. |
| `7c8212d` | Correção: Carl não aparecia no resgate da lhama. |
| `557aa60` | **Hoje** — só um Carl na tela + andar da Cindy mais calmo. |
| `231cf20` | **Hoje** — branco entre o Jimmy e o guarda-chuva removido. |
| `091d659` | Sheen vestido de Ultra Lord atravessa a tela correndo ou "voando". |

### Detalhes do que foi feito hoje (ainda não publicado)

**1. Dois Carls na tela ao mesmo tempo (`jimmy_pet.py`)**
- Problema: durante o resgate da lhama (Carl esperando o Jimmy), o evento aleatório "lhamas fugindo" mandava
  um segundo Carl correndo atrás da lhama.
- Solução: novo método `TrayManager.carl_na_tela()`, que é verdadeiro se houver Carl no resgate, Carl correndo
  (`Runner` com `anim == "carl_desespero"`) ou Carl de visita (`friend.key == "carl"`). É usado em:
  - `solta_lhamas()`: a lhama aleatória ainda pode fugir, mas **sem** o Carl atrás se ele já estiver na tela;
  - `start_resgate()`: o resgate não começa se já houver Carl;
  - `spawn_friend()`: o Carl não é sorteado para visita se já estiver na tela.
- Regra combinada com o usuário: **uma lhama no planeta e outra correndo ao mesmo tempo pode**; **dois Carls nunca**.

**2. Cindy andando estranho (mexendo a mão sem parar)**
- Causa: a animação `amigo_cindy_anda` tem só **2 poses** com os braços bem diferentes, trocando a cada ~0,1 s.
- Solução em `Friend.logic()`: se a animação de andar tiver 2 quadros ou menos, troca a cada 26 px em vez de 9 px
  (~4 trocas por segundo). Os outros amigos (5–6 quadros) não mudaram.
- Melhoria futura: o usuário pode gerar uma folha nova do andar da Cindy com 4–6 quadros, de perfil.

**3. Branco entre braço, cabeça e guarda-chuva (animações `chuva_*`)**
- Folha: `assets/extracted/jimmyChovendo.png`.
- Novo recurso `limpar_pontos` em `extract_frames.py` (função `limpar_pontos`), configurado em
  `anim_config.json` → `"extracted/jimmyChovendo.png"` → `"limpar_pontos": {"2": [[100,131]], …}`
  (chave = índice da figura na folha, valor = pontos dentro das manchas a apagar, em coordenadas do recorte).
- Removidas 9 manchas nos quadros 2 a 9. Ficaram intactos de propósito: os brancos dos olhos, os dentes (quadro 5)
  e a ponta branca do guarda-chuva (quadro 0).

**4. Sheen de Ultra Lord (`091d659`)**
- Folha `assets/extracted/shinultralord.jpg` (15 figuras): animações `sheen_ultralord_corre` (figuras 5–9) e
  `sheen_ultralord_voa` (10–14). A 1ª linha da folha (andando, socando, apontando: figuras 0–4) ainda não é usada.
- `TrayManager.solta_sheen()`: o Sheen atravessa a tela gritando ("ULTRA LORD! 🦸"…) e o Jimmy comenta.
  Sai sozinho de tempos em tempos (`next_sheen`, a cada 20–45 min, se as visitas de amigos estiverem ligadas)
  ou pelo menu do botão direito → "🦸 Ultra Lord!". Não aparece junto com lhamas, nem se o Sheen estiver de visita.
- `Runner` ganhou o parâmetro `comentario` (lista de falas do Jimmy quando o corredor passa por ele).

## 5. Onde estamos agora

- Branch `main` com **3 commits locais à frente da v1.1**, **não enviados** ao GitHub (sem `git push`) e **sem release**.
- `.exe` já compilado em `dist\` com essas correções, e o pet está rodando a versão nova.
- Para publicar como v1.2: subir `APP_VERSAO`, rodar `.\build.ps1`, `git push` e criar a release (ver seção 6).
  **Só publicar com OK explícito do usuário.**

## 6. Regras e cuidados importantes

- **Build**: fechar o pet antes (o `.exe` em `dist\` fica travado se estiver aberto) e rodar `.\build.ps1` no PowerShell.
  Não redirecionar stderr com `*>&1`, senão o aviso "DEPRECATION" do PyInstaller vira erro.
- **Release**: `gh release create vX.Y ...` com `C:\Program Files\GitHub CLI\gh.exe`. O arquivo anexado **precisa se chamar
  `JimmyNeutronPet.exe`**, porque o auto-atualizador do pet (`Atualizador`) procura esse nome. Anexar também o instalador.
- Testes sem abrir janela: `QT_QPA_PLATFORM=offscreen`. Uma exceção num slot do PyQt6 encerra com código
  `0xC0000409` sem traceback (normalmente é erro do próprio teste). Os erros do pet são registrados com `log_error()`.
- Estilo do código: comentários curtos em português, nomes em português (`fala`, `anda`, `lado`, `chao`), uma linha por ideia.
  Toda lógica de timer fica dentro de `try/except` com `log_error(e)`.
- Mensagens de commit em inglês.
- Projeto de fã, sem fins lucrativos (personagens da Nickelodeon/Paramount).

## 7. Próximos passos e ideias

**Combinado com o usuário:**
- Hugh e Judy Neutron (pai e mãe do Jimmy): o usuário vai mandar as folhas.

**Pendências de arte (o usuário gera as imagens):**
- Andar da Cindy com 4–6 quadros.
- Folha do Jimmy andando com a sobrancelha estável.
- Minifoguetes com espaço entre eles na folha.
- (Opcional) Jimmy + Carl juntos no foguete.

**Ideias sugeridas (nenhuma começada):**
- ✅ Sheen de Ultra Lord: **feito**. Variação possível: o Sheen **correndo atrás do boneco do Ultra Lord** que o Goddard pegou
  (precisa de folha do Goddard com o boneco na boca).
- Álbum de conquistas/figurinhas usando as estatísticas que já são contadas (`stat(...)`). Não precisa de arte.
- Mini-jogos no menu de clique: "acerte o alien" (com os aliens do Modo Game) e quiz de ciência. Não precisa de arte.
- 🖼️ Professor Calamitous ou Beautiful Gorgeous como vilão visitante, ou chefe novo do Modo Game.
- 🖼️ Reações à bateria fraca e à queda da internet (a leitura da bateria já existe: `SYSTEM_POWER_STATUS`).
- Relatório do dia na hora de dormir (água, pomodoros, lembretes).
- 🖼️ Fantasias de Natal e Halloween nas datas comemorativas.

## 8. Arquitetura Modular 3D (DLC Sob Demanda)

- **Princípio**: O repositório original e os arquivos clássicos em `assets/anim/` permanecem 100% 2D limpos e intocados.
- **DLC 3D Sob Demanda**:
  - `dist/pacote_3d.zip` e `assets/pacote_3d.zip` (2.59 MB).
  - Inclui Jimmy (13 animações completas) e Sheen (10 animações: 8 normais + 2 ultralord).
  - Instalado em `%APPDATA%\JimmyNeutronPet\anim_3d\`.
  - Ativado via Configurações com alternância dinâmica instantânea.

### Personagens no Mixamo:
1. **Jimmy** (`jimmy_para_mixamo`): 13 animações renderizadas, quantizadas e integradas.
2. **Sheen** (`sheen_para_mixamo`): malha reduzida de 1.5M para 45k polígonos, 10 animações Mixamo baixadas e renderizadas com shader cartoon.

### Correções Recentes:
- **Goddard Fetch Mouse Pointer**: Corrigido fluxo de estados na máquina de voo para que Goddard morda o cursor e efetivamente o transporte até a mão do Jimmy antes de disparar a conclusão.
- **Arraste do Jimmy no Mouse**:
  - `render_anim.py` corrigido com proteção de escala do modelo base (`rest_h`), eliminando o zoom 2.5x e corte de membros em animações horizontais/deitadas.
  - Ao ser pego e arrastado com o mouse, o Jimmy agora usa a animação `jimmy_hang` (em pé, pendurado pelo ponteiro), com captura de mouse `grabMouse()` para arraste suave.
