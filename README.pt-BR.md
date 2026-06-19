<sub>[English](README.md) · **Português 🇧🇷**</sub>

# 🎬 Instagram Reels Gallery

> Todo Reel que seus amigos jogaram no grupo do chat, transformado em uma parede linda e
> navegável. Extraia os Reels compartilhados em um **grupo de DM** do Instagram e construa
> um site de galeria estático, filtre por quem compartilhou, ordene por data, clique para abrir.

Sem usuário/senha: ele usa **o seu próprio cookie de sessão**. A saída são arquivos
estáticos simples, então você pode abri-los localmente ou hospedá-los em qualquer lugar.

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![instagrapi](https://img.shields.io/badge/api-instagrapi-purple)

![Gallery preview](preview.png)

> *Galeria de exemplo com dados de espaço reservado, chips de filtro por pessoa, alternância
> mais novo/mais antigo, cards 9:16, clique para abrir no Instagram.*

---

## 🚀 Recursos

- **Lê um grupo de DM**: puxa todo Reel/post compartilhado na conversa.
- **Sabe quem compartilhou o quê**: cada card mostra o amigo que o postou; filtre por pessoa.
- **Site autossuficiente**: as miniaturas são baixadas localmente (os links do CDN do Instagram expiram),
  então a galeria continua funcionando para sempre, mesmo offline via `file://`.
- **Autenticação por cookie**: sem senha; usa o seu `sessionid`.
- **Deploy com um comando**: upload opcional para o Netlify, ou coloque em qualquer host estático.

---

## 📦 Requisitos

```bash
pip install instagrapi requests
```

Além de um **`sessionid`** do Instagram logado (veja abaixo).

---

## 🔑 Obtenha o seu sessionid

1. Faça login no Instagram no seu navegador.
2. `F12` → **Application** → **Cookies** → `https://www.instagram.com` → copie o valor do
   cookie **`sessionid`**.
3. Cole-o (apenas o valor, uma linha) em um arquivo chamado `.sessionid` nesta pasta, ou
   defina a variável de ambiente `IG_SESSIONID`.

> ⚠️ O `sessionid` concede acesso total à sua conta. Trate-o como uma senha. Ele é
> ignorado pelo git e nunca sai da sua máquina. Para revogá-lo, basta deslogar essa sessão no
> Instagram.

---

## ▶️ Uso

```bash
# 1) find your group's THREAD_ID
python extract.py list
#    (or search by name)
python find_thread.py "the squad"

# 2) pull the reels  ->  reels.json
python extract.py pull <THREAD_ID>            # add --limit N to cap it

# 3) build the gallery  ->  site/index.html
python build_site.py reels.json site "The Squad's Reels" 🔥

# 4) (optional) deploy to Netlify
NETLIFY_AUTH_TOKEN=xxxxx python deploy_netlify.py site the-squad-reels
```

Abra `site/index.html` no seu navegador. Para atualizar com novos reels, repita os passos 2–3.

> O `thread_id` da API **não** é o id na URL da web (`/direct/t/<id>/`). Use
> `extract.py list` ou `find_thread.py` para obter o id real.

---

## ⚙️ Como funciona

| Script | O que faz |
|--------|------|
| `extract.py list` | lista suas threads de DM + os respectivos `THREAD_ID` (grupos primeiro) |
| `extract.py pull <id>` | percorre a conversa → `reels.json` (código, dono, quem compartilhou, data, miniatura) |
| `find_thread.py "name"` | encontra o id de uma thread por nome/@username |
| `build_site.py` | baixa as miniaturas + escreve o `site/` estático |
| `deploy_netlify.py` | compacta e faz deploy do `site/` via API REST do Netlify |

Ele lida com o formato de compartilhamento atual do Instagram (`xma_clip` = reel, `xma_media_share` = post)
bem como com compartilhamentos estruturados mais antigos, removendo duplicatas pelo código do reel.

---

## 🤖 Use como uma skill do Claude Code

```bash
git clone https://github.com/pedroccm/instagram-reels-gallery.git \
  ~/.claude/skills/instagram-reels-gallery
```

Então diga *"build a gallery from the reels in my group 'the squad'"*.

---

## 📝 Notas e limites

- Usa a **API privada** do Instagram (instagrapi), tecnicamente contra os ToS. Existe risco de
  bloqueio, mas é menor com um cookie do que com usuário/senha. Mantenha os delays no lugar.
- `reels.json` e `site/` guardam conteúdo privado do grupo e são **ignorados pelo git** por padrão.
- Compartilhamentos de Stories são ignorados (eles são efêmeros).

---

## 📄 Licença

MIT, veja [LICENSE](LICENSE).
