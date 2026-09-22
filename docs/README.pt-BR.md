# CAD-link

Arquivos de engenharia do repositório compartilhado, acessíveis pelos produtos do Odoo.

**Versão alfa · Odoo 16 · LGPL-3.0 ou posterior**

O módulo `cad_link` usa o código interno de cada variante para localizar sua
pasta. Os arquivos continuam no repositório compartilhado, utilizados pelo CAD
e pelo Explorer. O Odoo consulta esse mesmo conteúdo, sob demanda.

## O que já está implementado

- Configuração por empresa do backend OCA `fs_storage`, pasta dos itens e UNC opcional.
- Aba CAD no produto e na variante, com seleção quando há múltiplas variantes.
- Listagem dos arquivos dentro da própria aba CAD, visualização de PDF pelo
  navegador e download dos formatos permitidos.
- Componente opcional para Windows: abrir o original na rede, mostrar o arquivo
  no Explorer e abrir a pasta do item. O botão **Baixar** continua disponível.
- Grupos separados para PDFs e para PDFs mais arquivos CAD originais.
- Caminho copiável para abrir no Explorer, preservando zeros do código.
- Verificações de código duplicado, empresa, acesso ao produto, nome e tamanho do arquivo.

O Odoo consulta os arquivos; a edição do original aberto na rede é feita pelo
aplicativo CAD instalado no Windows. Esta versão não gera PDFs, converte modelos
ou sincroniza listas de materiais. O visualizador 3D e os conectores de exportação
estão no [roteiro de evolução](roadmap.md).

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
7. Para abrir pela rede, instale o [componente Windows](../desktop/windows/README.md)
   em cada estação, configurando a raiz UNC permitida. Ative **CAD-link Desktop**
   na empresa. O aplicativo associado ao formato abrirá o original compartilhado.

Exemplo fictício: referência `P-2200` → `Items/P-2200/P-2200.pdf`.
A instalação não cria pastas, contas, mapeamentos ou permissões automaticamente.
O componente opcional registra o protocolo `cad-link` somente no usuário Windows
em que for instalado. Não é necessário instalá-lo para visualizar PDFs ou baixar
arquivos. Abertura direta usa o caminho UNC, sem depender de uma letra de unidade.

As permissões SMB/NTFS e os grupos do Odoo têm funções diferentes: os grupos
controlam o acesso feito pelo Odoo; o acesso direto pelo Explorer depende das
permissões do servidor de arquivos. Visualizar um PDF permite obter seu conteúdo.

Leia o [guia de configuração](configuration.md) e as
[instruções para contribuir](../CONTRIBUTING.md).
