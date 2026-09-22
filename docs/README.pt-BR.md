# CAD-link

Arquivos de engenharia do repositório compartilhado, acessíveis pelos produtos do Odoo.

**Versão alfa · Odoo 16 · 16.0.1.2.0 · LGPL-3.0 ou posterior**

O módulo `cad_link` usa o código interno de cada variante para localizar sua
pasta. Os arquivos continuam no repositório compartilhado, utilizados pelo CAD
e pelo Explorer. O Odoo consulta esse mesmo conteúdo, sob demanda.

## O que já está implementado

- Configuração por empresa do backend OCA `fs_storage`, pasta dos itens e UNC opcional.
- Aba CAD no produto e na variante, com seleção quando há múltiplas variantes.
- Listagem dos arquivos dentro da própria aba CAD, visualização de PDF pelo
  navegador e download dos formatos permitidos.
- Visualização de GLB dentro da aba CAD, com giro, zoom, retorno à vista inicial
  e tela cheia. O visualizador local exibe as texturas PNG/JPEG incluídas no GLB.
- Componente opcional para Windows: abrir o original na rede, mostrar o arquivo
  no Explorer e abrir a pasta do item. O botão **Baixar** continua disponível.
- Grupos separados para PDFs e para PDFs mais arquivos CAD originais.
- Caminho copiável para abrir no Explorer, preservando zeros do código.
- Verificações de código duplicado, empresa, acesso ao produto, nome e tamanho do arquivo.
- [Regras externas de exportação para Inventor](../desktop/inventor/README.pt-BR.md),
  que podem gerar o GLB após salvar peças e montagens. A exportação real e o evento
  precisam ser validados em um piloto na estação de engenharia.

O Odoo consulta os arquivos; a edição do original aberto na rede é feita pelo
aplicativo CAD instalado no Windows. O navegador lê o GLB já exportado, sem abrir
diretamente IPT/IAM. A conversão acontece no Inventor, pelo componente opcional;
o Odoo não gera PDFs, converte modelos nem sincroniza listas de materiais.

## Como configurar

1. Instale `fs_storage` da OCA e suas dependências na mesma instalação Python do Odoo.
2. Adicione a raiz deste repositório ao `addons_path` e instale `cad_link` em teste.
3. Configure um backend de armazenamento com credenciais somente de leitura.
4. Em **Configurações → Usuários e Empresas → Empresas → CAD-link**, escolha o
   backend, informe a pasta relativa dos itens e, opcionalmente, o caminho UNC
   equivalente à raiz do armazenamento.
5. Conceda ao usuário interno o grupo CAD-link adequado. Ele também precisa ter
   acesso ao produto pelas permissões normais do Odoo.
6. Abra o produto, escolha a variante se necessário e use a aba CAD.
7. Para consultar o 3D, coloque um GLB 2.0 na pasta do item, clique em **Refresh**
   e depois em **View 3D**. O botão **Download** e as ações de rede continuam na
   listagem. O grupo **PDF and CAD sources** é necessário para acessar o GLB.
8. Para abrir pela rede, instale o [componente Windows](../desktop/windows/README.md)
   em cada estação, configurando a raiz UNC permitida. Ative **CAD-link Desktop**
   na empresa. O aplicativo associado ao formato abrirá o original compartilhado.

Exemplo fictício: referência `P-2200` → `Items/P-2200/P-2200.pdf`.
A instalação não cria pastas, contas, mapeamentos ou permissões automaticamente.
O componente opcional registra o protocolo `cad-link` somente no usuário Windows
em que for instalado. Não é necessário instalá-lo nem ter Inventor para consultar
PDFs/GLBs no navegador ou baixar arquivos. Abertura direta usa o caminho UNC,
sem depender de uma letra de unidade.

O limite padrão é **50 MiB por arquivo**, configurável na empresa. O GLB deve
conter a geometria e as imagens PNG/JPEG no próprio arquivo, sem URIs externas,
texturas separadas ou compressão que dependa de decodificadores. A visualização
depende dos materiais que o exportador realmente incluiu; ela não cria texturas
ausentes. O grupo restrito a PDFs continua sem acesso aos modelos 3D.

Para automatizar, configure as regras externas do Inventor, valide uma peça e
uma montagem manualmente e depois vincule a regra a **Após salvar documento**
nas abas globais **Peças** e **Montagens**. Não é necessário inserir uma regra
em cada item nem alterar o IPJ. Salvar uma peça atualiza seu GLB; montagens que
a utilizam precisam ser abertas, atualizadas e salvas para atualizar seus GLBs.
Veja o [passo a passo do exportador](../desktop/inventor/README.pt-BR.md).

As permissões SMB/NTFS e os grupos do Odoo têm funções diferentes: os grupos
controlam o acesso feito pelo Odoo; o acesso direto pelo Explorer depende das
permissões do servidor de arquivos. Visualizar um PDF permite obter seu conteúdo.

Leia o [guia de configuração](configuration.md) e as
[instruções para contribuir](../CONTRIBUTING.md).
