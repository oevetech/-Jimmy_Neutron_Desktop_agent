# 🚀 Jimmy Neutron Desktop Pet

O Jimmy Neutron e o Goddard morando na sua barra de tarefas do Windows! Eles passeiam, voam de foguete,
recebem visitas dos amigos, te lembram de beber água e muito mais.

> Projeto de fã, sem fins lucrativos. *Jimmy Neutron* e seus personagens pertencem à Nickelodeon/Paramount.

Feito por **[@oevetech](https://www.youtube.com/@oevetech)** ▶️

## ⬇️ Instalar

1. Baixe o **`Instalar Jimmy Neutron Pet.exe`** na página de [Releases](../../releases/latest).
2. Abra e clique em **Instalar** (não precisa de administrador).
3. Na primeira vez o Windows pode mostrar "O Windows protegeu o computador": clique em
   **Mais informações → Executar assim mesmo** (o programa não tem assinatura digital).

Prefere sem instalar? Baixe só o **`JimmyNeutronPet.exe`** e abra: ele funciona sozinho, em qualquer pasta.

O pet se atualiza sozinho quando sai uma versão nova (dá para desligar em ⚙️ Configurações → Online).

## ✨ O que ele faz

- 🚀 **Foguete**: de tempos em tempos o Jimmy agarra o foguete e decola; lá em cima o foguete explode
  e ele desce de paraquedas, levado pelo vento (às vezes uma rajada joga ele de volta pra cima!).
  O Goddard voa atrás de jetpack. Clique no foguete para lançar, ou arraste para mudar de lugar.
- 🛸 **Passeio de foguete**: o Jimmy monta no foguete e dá um voo rasante pela tela, acenando e comemorando.
  🔧 De vez em quando ele também faz a manutenção do foguete (com solda e faíscas).
- 🐕 **Goddard**: segue o Jimmy, busca a 🎾 bolinha, late, dorme junto, dança e faz truques.
  É um **bichinho virtual**: passe o mouse para ver 🛢️ óleo, 🎾 diversão e 🛁 limpeza; clique com o botão
  direito nele para dar óleo, brincar ou dar banho. Quando você fica um tempo longe do PC,
  ele pode até 🖱️ buscar o ponteiro do mouse para o Jimmy!
- 🖱️ **Clique rápido no Jimmy**: menu com jogo de bolinha (cada arremesso mais longe), novo lembrete,
  timer, nota rápida, "decida por mim" e contador de copos d'água.
- ☄️ **Chuva de meteoros**: clique nos meteoros antes que caiam (com recorde).
- ⏳ **Contagem regressiva**: cadastre datas e o Jimmy avisa quantos dias faltam e comemora no dia.
- 🌬️ Clique no Jimmy enquanto ele desce de paraquedas e uma rajada de vento joga ele de volta pra cima.
- 👫 **Amigos**: Carl, Sheen, Libby e Cindy aparecem para conversar. E as 🦙 lhamas do Carl fogem pela tela.
- ⚡ **Brain Blast**, 🧪 invenções (até o raio encolhedor no Goddard!), 💃 dança quando toca música no PC.
- 😴 Dorme à noite, cochila quando você sai do PC e diz "Voltou! 👋" quando você volta.
- 🔔 **Lembretes**: água, pausa, comer, exercício, hora de dormir e lembretes personalizados.
- 🍅 **Pomodoro**, ⏱️ timer "me avise em...", 🔕 não perturbe.
- 🌦️ **Clima** da sua cidade (com chuva e guarda-chuva na tela), 🍂 estações do ano, 🎉 datas comemorativas.
- 🎮 Comenta quando você abre certos programas, 🔬 conta curiosidades de ciência, 🏆 conquistas.
- 📡 Com o pet em dois PCs da mesma rede, o Jimmy **visita o outro PC**.
- 🌎 Português e inglês, vários monitores, tom de noite, sombras, fumaça, faíscas...

Clique com o **botão direito** em qualquer personagem para o menu rápido. Tudo é configurável no ícone da bandeja → ⚙️ Configurações
(inclusive o tamanho dos dois e a proporção só do Goddard).

## 🤝 Contribuir

Ideias, correções e novas animações são bem-vindas! Abra uma *Issue* ou mande um *Pull Request*.
Para animações novas: folha em **PNG com fundo transparente**, figuras separadas por espaço vazio,
e uma entrada no `assets/anim_config.json` (veja a seção Animações abaixo).

## 🔒 Privacidade

- **Clima**: só o nome da cidade é enviado ao [Open-Meteo](https://open-meteo.com) (gratuito, sem conta).
- **Atualização**: consulta as Releases deste repositório no GitHub.
- **Dança**: o pet só lê o *nível* de volume da saída de som; não grava nem escuta nada.
- **Easter egg "neutron"** (desligado por padrão): guarda só as últimas 7 letras digitadas, na memória.
- **Visita a outros PCs** (desligada por padrão): mensagens pequenas na rede local, só entre pets.
- Configurações ficam em `%APPDATA%\JimmyNeutronPet`.

## 🛠️ Compilar

Precisa do Python 3 com `PyQt6` e `pyinstaller`:

```powershell
pip install PyQt6 pyinstaller
.\build.ps1
```

Gera `dist\JimmyNeutronPet.exe` e `dist\Instalar Jimmy Neutron Pet.exe`. Para rodar direto: `python jimmy_pet.py`.

### Animações

As folhas de sprites ficam em `assets/` e são recortadas automaticamente pelo `assets/extract_frames.py`
(acha cada figura pela transparência, tira fundo branco e balões de fala, alinha pelos pés e iguala a escala).
O que vira cada animação está em `assets/anim_config.json`. Depois de mudar uma folha:

```powershell
python assets\extract_frames.py
```

Os sons são gerados por `assets/gerar_sons.py` (troque qualquer `.wav` em `assets/sons/` por um seu).

### Publicar uma versão nova

1. Suba `APP_VERSAO` no topo do `jimmy_pet.py` (ex.: `"1.1"`) e rode `.\build.ps1`.
2. Crie uma Release com a tag `v1.1` e anexe **`JimmyNeutronPet.exe`** (com esse nome) e o instalador.
3. Os pets instalados verificam e se atualizam sozinhos.
