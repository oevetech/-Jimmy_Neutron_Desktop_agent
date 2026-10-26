# 🎭 Poses e Animações 3D — Mixamo para o Jimmy Neutron Pet

> Documento atualizado em 26/10/2026 registrando o processo de extração, otimização das animações 3D e a **Arquitetura Modular de Pacote 3D sob demanda**.

---

## 1. O que foi feito

1. Conectamos um navegador automatizado (via Playwright) diretamente à sessão autenticada do Google Chrome no **Adobe Mixamo**, pesquisamos as animações correspondentes a todas as ações dos personagens do pet, ativamos opções essenciais para sprites/jogos (como **"In Place"** para caminhada e corrida contínuas) e realizamos o download dos pacotes binários `.FBX` completos (incluindo malha, esqueleto de rigging e animação com keyframes a 30 FPS).
2. Otimizamos a malha 3D (reduzindo em ~90% o tamanho dos arquivos FBX via modificador Decimate no Blender) e renderizamos os quadros do Jimmy 3D com shader cartoon e contorno com normais invertidas.
3. Quantizamos todas as imagens geradas para paleta transparente de 256 cores de alta fidelidade (redução média de 82% no peso dos sprites).
4. **Arquitetura Modular (DLC / Pacote 3D Sob Demanda)**:
   - O executável principal mantém as imagens clássicas em 2D, ficando extremamente leve e rápido para abrir.
   - Um botão dedicado nas **Configurações** (`Geral` > `Visual 3D`) permite:
     - Baixar e instalar o pacote 3D (`dist/pacote_3d.zip` - 1.3 MB).
     - Ativar e desativar o modo 3D com um único clique (alternância dinâmica instantânea sem precisar fechar o pet).
     - Desinstalar o pacote 3D para liberar espaço e retornar ao modo 2D a qualquer momento.

---

## 2. Tabela Completa de Poses Baixadas e Mapeamento com o Pet

| Arquivo FBX | Animação no Mixamo | Opção In Place | Animação Correspondente no Pet | Status no Pacote 3D |
|---|---|:---:|---|:---:|
| **`01_walking.fbx`** | `Walking` | ✅ Sim | `jimmy_walk` | ✅ Renderizado e empacotado (16 quadros) |
| **`02_running.fbx`** | `Running` | ✅ Sim | `amigo_*_corre` / `carl_desespero` | Pronto para futuros amigos |
| **`03_idle.fbx`** | `Happy Idle` | ❌ Não | `jimmy_idle` | ✅ Renderizado e empacotado (16 quadros) |
| **`04_falling.fbx`** | `Falling` | ❌ Não | `jimmy_fall` | ✅ Renderizado e empacotado (12 quadros) |
| **`05_jumping.fbx`** | `Jump` | ✅ Sim | `ideia_feliz` | ✅ Renderizado e empacotado (16 quadros) |
| **`06_waving.fbx`** | `Waving` | ❌ Não | `amigo_*_acena` | Pronto para amigos |
| **`07_talking.fbx`** | `Talking` | ❌ Não | `amigo_*_fala` | Pronto para amigos |
| **`08_dancing.fbx`** | `Hip Hop Dancing` | ✅ Sim | `jimmy_danca` | ✅ Renderizado e empacotado (16 quadros) |
| **`09_pointing.fbx`** | `Pointing` | ❌ Não | `ideia_ideia` | ✅ Renderizado e empacotado (12 quadros) |
| **`10_laughing.fbx`** | `Laughing` | ❌ Não | `amigo_*_ri` | Pronto para amigos |
| **`11_yawn.fbx`** | `Big Yawn While Standing` | ❌ Não | `jimmy_yawn` | ✅ Renderizado e empacotado (16 quadros) |
| **`12_doze_stand.fbx`** | `Standing Around Bored Idle` | ❌ Não | `jimmy_doze_stand` | ✅ Renderizado e empacotado (16 quadros) |
| **`13_doze_sit.fbx`** | `Sitting On The Floor` | ❌ Não | `jimmy_doze_sit` | ✅ Renderizado e empacotado (16 quadros) |
| **`14_sleep.fbx`** | `Sleeping Deeply` | ❌ Não | `jimmy_sleep` | ✅ Renderizado e empacotado (16 quadros) |
| **`15_hang.fbx`** | `Hanging Idle` | ❌ Não | `jimmy_hang` | ✅ Renderizado e empacotado (12 quadros) |
| **`16_thinking.fbx`** | `Thinking` | ❌ Não | `ideia_pensa` | ✅ Renderizado e empacotado (16 quadros) |
| **`17_surprised.fbx`** | `Being Surprised And Looking Right` | ❌ Não | `ideia_susto` | ✅ Renderizado e empacotado (12 quadros) |

---

## 3. Estrutura do Pacote Modular 3D

- **Arquivo do Pacote**: `dist/pacote_3d.zip` e `assets/pacote_3d.zip` (Tamanho: **1.31 MB**)
- **Animações inclusas no Pacote 3D**: **13 animações completas** do Jimmy Neutron (192 arquivos / quadros PNG quantizados + `meta.json` em cada pasta).
- **Diretório de Instalação no Cliente**: `%APPDATA%\JimmyNeutronPet\anim_3d\`
- **Integração no Código (`jimmy_pet.py`)**:
  - `Pet.get_anim_folder(anim)`: Detecta dinamicamente se `CFG["modo_3d"]` está ativo e se a pasta `%APPDATA%\JimmyNeutronPet\anim_3d\` contém a animação. Se sim, carrega os quadros 3D; caso contrário, carrega instantaneamente os quadros 2D originais.
  - `TrayManager.apply_modo_3d()`: Limpa o cache de texturas e reinicia os pets em tempo de execução sem reiniciar o processo.
  - **Thread de Download (`BaixadorPacote3D`)**: Se o pacote não existir localmente, baixa em segundo plano da release com barra de progresso.
