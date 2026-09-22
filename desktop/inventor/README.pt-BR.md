# Exportação automática do Inventor para o CAD-link

O engenheiro salva o IPT/IAM no Inventor. A regra gera um GLB na mesma pasta, e o
Odoo lê esse GLB para exibir o 3D. O original continua sendo o arquivo editável.

```text
Itens\DEMO-001\DEMO-001.ipt
Itens\DEMO-001\DEMO-001.glb
```

Este componente é reutilizável: não contém nomes de computadores, usuários ou
servidores. A configuração fica por usuário Windows e as regras podem ficar em
uma pasta compartilhada. Ele é separado do componente que abre arquivos da rede.

## Configuração inicial

1. Use uma instalação completa do Inventor com o exportador nativo glTF/GLB
   (introduzido no Inventor 2023). O visualizador sozinho não executa esta regra.
2. Copie as duas regras `.iLogicVb` para a pasta de regras externas e adicione a
   pasta em **Ferramentas → Opções → Configuração do iLogic → Diretórios de regras
   externas**. Preserve os diretórios existentes e sua ordem.
3. Execute **CadLink-InspectGLB** manualmente. Ela identifica o exportador real
   instalado, sem exportar arquivos. Não vincule essa regra de inspeção ao evento
   de salvar.
4. Copie `export.example.xml` para
   `%LOCALAPPDATA%\CAD-link\Inventor\export.xml`. Configure `ItemsRoot` com o caminho
   da pasta que contém os códigos dos itens, por exemplo `R:\Itens`. Deixe
   `TranslatorClassId` vazio para identificação automática de um único exportador.
   Se houver mais de um, informe o identificador encontrado na inspeção.
5. Ajuste `MaxFileBytes` ao limite configurado no Odoo, mantendo 50 MiB por padrão.
   Coloque `Enabled` como `true`. Abra, atualize e salve uma peça de teste. Execute
   **CadLink-ExportGLB** manualmente e confira o GLB no Odoo: aparência, escala,
   orientação e texturas. Repita com uma montagem, com os componentes resolvidos
   e salvos, e teste também substituir um GLB já existente.
6. Após validar o piloto, em **Gerenciar → iLogic → Gatilhos de eventos**, vincule
   **CadLink-ExportGLB** a **Após salvar documento** nas abas **Peças** e
   **Montagens**. Preserve os demais eventos; coloque a exportação depois das
   regras que alteram o documento. Salve novamente para comprovar a atualização.

As abas globais Peças/Montagens permitem configurar uma vez por estação, sem
inserir a regra em cada desenho. Os vínculos ficam em `RulesOnEvents.xml`, no
primeiro diretório de regras externas. Esse arquivo pode ser compartilhado entre
estações, com manutenção restrita. A aba **Este documento** grava o vínculo dentro
do arquivo CAD; não é necessária para esse fluxo. Também não é preciso alterar
o IPJ. [Configuração de eventos Autodesk](https://help.autodesk.com/cloudhelp/2022/ENU/Inventor-iLogic/files/GUID-B14A47F4-81D2-4627-A973-2BC7F790DF89.htm).

## Comportamento e limites

A regra só exporta `pasta-do-item\codigo.ipt` ou `.iam` cujo nome coincide com a
pasta, abaixo do `ItemsRoot` configurado. Ela não salva nem altera propriedades
dos originais. Gera o arquivo em uma subpasta temporária e publica o GLB completo
por renomeação/substituição atômica. Se ocorrer erro, o GLB anterior permanece.
Erros ficam na barra de status e em
`%LOCALAPPDATA%\CAD-link\Inventor\export.log`.

Salvar uma peça atualiza o GLB da peça. Para atualizar a visualização de uma
montagem que usa essa peça, é necessário abrir, atualizar e salvar a montagem.
Esta versão não percorre automaticamente todas as montagens superiores. A regra
usa a representação atual e os padrões do exportador; o piloto precisa validar
qual posição, estado do modelo e aparência devem ser publicados.

A exportação ocupa o Inventor durante a execução e pode aumentar o tempo de
salvar montagens grandes. Não há serviço de conversão no Linux nem processo de
aprovação. Para pausar, altere `Enabled` para `false`; para retirar o automatismo,
remova apenas os dois vínculos do CAD-link nos gatilhos de eventos.

**Validação disponível:** 17 verificações do código de arquivos passaram no Windows
com dados sintéticos; a regra completa compila com a API do Inventor 2024. A
execução real no Inventor, o evento após salvar e a aparência dos modelos ainda
dependem do piloto na estação. A distribuição não instala nem ativa os eventos
automaticamente. Veja os [detalhes técnicos e testes](README.md).
