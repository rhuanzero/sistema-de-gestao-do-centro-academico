Instruções para iniciar o frontend Angular (projeto: `sgca`)

Este README descreve os passos iniciais para criar o projeto Angular `sgca` usando PowerShell (Windows).

1) Pré-requisitos
- Node.js (recomendo LTS, v18+). Verifique com:

```powershell
node --version
npm --version
```

Se não tiver Node.js, instale a partir de https://nodejs.org/ ou use um gerenciador (nvm-windows).

2) Instalar Angular CLI (globalmente)

```powershell
npm install -g @angular/cli
```

3) Criar o projeto Angular `sgca`

Abra o PowerShell e execute:

```powershell
cd C:\\Users\\thaua\\Projetos\\SGCA\\sistema-de-gestao-do-centro-academico\\frontend
ng new sgca --routing --style=css
```

Observações:
- `--routing`: adiciona suporte a rotas.
- `--style=css`: usa CSS puro.
- Não passamos `--strict` (configurações estritas OFF).

O `ng new` normalmente já instala dependências. Se preferir pular instalação automática e rodar depois, use `--skip-install`.

4) Iniciar o servidor de desenvolvimento

```powershell
cd sgca
npm install
ng serve --open
```

O `ng serve --open` abre o app no navegador.

5) Proxy para o backend (evitar CORS)

Há um `proxy.conf.json` de exemplo neste diretório. O conteúdo aponta para `http://localhost:8000` e encaminha chamadas para `/api`.

Para usar o proxy durante desenvolvimento:

```powershell
ng serve --proxy-config ..\\proxy.conf.json
```

(o caminho `..\\proxy.conf.json` assume que você está em `frontend/sgca`)

6) Controle de versão

```powershell
git add frontend/sgca
git commit -m "feat(frontend): scaffold Angular app (sgca)"
```

Próximos passos que eu posso fazer por você:
- Rodar os comandos de scaffold (`ng new sgca`) aqui (se você quiser que eu execute localmente).
- Gerar componentes iniciais, serviços para comunicação com o backend ou o `proxy.conf.json` (já adicionado).
- Adicionar instruções CI ou scripts npm.

Diga se quer que eu execute os comandos agora ou apenas te passe os comandos para rodar no seu terminal.