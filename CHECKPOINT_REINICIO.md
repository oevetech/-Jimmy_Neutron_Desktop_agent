# 📌 Checkpoint do Projeto Jimmy Neutron Pet

**Data/Hora**: 26/10/2026 09:50 (Horário Local)  
**Status**: 100% Concluído e Atualizado

---

## 🎯 O Que Foi Feito e Está Concluído:

1. **Modo 2D Clássico Restaurado e Protegido**:
   - `assets/anim/` 100% limpo e sem misturas de quadros 3D.
   - O andar original (`jimmy_walk` de 14 quadros do v1.0) está restaurado e ativo por padrão.

2. **Pipeline do Sheen 3D Completo (10 Animações)**:
   - Baixados 10 FBX do Mixamo com Playwright usando o modelo riggado do Sheen.
   - Otimizados via Blender Decimate (66% de redução).
   - Renderizados 156 quadros com Blender:
     - `amigo_sheen_anda`, `amigo_sheen_parado`, `amigo_sheen_fala`, `amigo_sheen_acena`, `amigo_sheen_ri`, `amigo_sheen_pula`, `amigo_sheen_corre`, `amigo_sheen_aponta`
     - `sheen_ultralord_corre`, `sheen_ultralord_voa`
   - Quantizados com FastOctree 256 cores (86% de redução).
   - Inclusos no pacote modular `dist/pacote_3d.zip` e `assets/pacote_3d.zip` (2.59 MB) e instalados em `%APPDATA%\JimmyNeutronPet\anim_3d\`.

3. **Correção do Bug do Goddard ("Goddard, pega o ponteiro!")**:
   - **Causa**: Na transição de fase de `"indo"` para `"levando"`, o bloco sequencial subsequente avaliava a distância com o `perto` calculado para o cursor, disparando `fim_busca(True)` no exato milissegundo em que mordia o ponteiro. Além disso, a tolerância de movimento do mouse era muito rígida (25px).
   - **Correção**: Estruturado como `if/elif` estrito, inicializando `b["solto"]` na mordida e conduzindo o cursor `QCursor.setPos` a cada quadro até as mãos do Jimmy, completando a entrega somente ao chegar próximo do Jimmy. Tolerância ajustada para 50px contra tremores do mouse.

4. **Correção do Bug do Jimmy Arrastado pelo Mouse (Tamanho Gigante / Deitado / Cortado)**:
   - **Causa 1**: Quando arrastado pelo mouse, o código usava `jimmy_fall` (Jimmy deitado no ar caindo) em vez de `jimmy_hang` (Jimmy pendurado em pé pelo mouse).
   - **Causa 2**: No script do Blender (`render_anim.py`), a altura `H` era medida apenas pelos vértices da malha avaliada; como em animações deitadas a altura Z é pequena, o Blender aplicava um zoom ortográfico de mais de 2.5x, cortando a cabeça e as pernas.
   - **Correção**:
     - `render_anim.py` corrigido para respeitar a altura real do modelo (`rest_h`) com matriz de mundo, centralizando o enquadramento sem zoom excessivo.
     - `jimmy_fall` re-renderizado com proporções perfeitas e centralizadas.
     - `Jimmy.mousePressEvent` e `logic()` atualizados para usar `jimmy_hang` (em pé, pendurado) ao ser clicado e arrastado.
     - Adicionado `grabMouse()` / `releaseMouse()` e `e.accept()` garantindo arraste suave sem perder foco.

5. **Correção do Bug do Sheen Voando (`sheen_ultralord_voa` Cortando Cabeça e Pés / Gigante)**:
   - **Causa**: Como o Sheen voa na horizontal, o enquadramento anterior calculava apenas a altura Z pequena do corpo (~0,005) em vez do comprimento do personagem, aplicando zoom excessivo de 2,3x e estourando a largura da imagem (0 a 277px).
   - **Correção**: Re-renderizado no Blender com enquadramento proporcional e margem de 15%. A caixa de exibição foi reduzida de forma segura para X: 28..251 e Y: 82..194 (totalmente centralizado, corpo inteiro, cabeça e pés com folga). Sprites quantizados e `pacote_3d.zip` atualizado.

6. **Binários Atualizados**:
   - `build.ps1` executado gerando:
     - `dist\JimmyNeutronPet.exe`
     - `dist\Instalar Jimmy Neutron Pet.exe`
     - `dist\pacote_3d.zip` (2.85 MB)

7. **Git**:
   - Todas as alterações são estritamente locais (`sem git push`).
