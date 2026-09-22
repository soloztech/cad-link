---
name: cad-link-export-glb
description: Inspecionar e exportar IPT/IAM para GLB na sessão local do Autodesk Inventor para visualização no CAD-link, incluindo configuração do automatismo após salvar. Use para geração e diagnóstico de GLB; não para editar geometria ou instalar o viewer Odoo.
---

# Exportar GLB com o Inventor

Use o Inventor já aberto no Windows, na mesma sessão, usuário e nível de elevação
do Codex. Execute o helper com **Windows PowerShell 5.1, 64 bits, `-STA`**. Não
inicie outra instância, serviço, sessão remota ou processo de exportação paralelo.

O helper fica em [scripts/Invoke-CadLinkGlb.ps1](scripts/Invoke-CadLinkGlb.ps1).
Ele localiza a regra mantida pelo CAD-link em `tools/cad-link/inventor`, subindo
pelos ancestrais da skill no projeto. Também aceita `-CompanionDirectory` ou a
variável `CAD_LINK_INVENTOR_HOME`. No checkout do CAD-link, localiza o próprio
`desktop/inventor`. A skill não mantém outra cópia da regra: instale junto o
companion da mesma versão. A inspeção informa o caminho encontrado.

## Inspecionar e executar

Primeiro inspecione; sem `-Export` não abre documentos nem executa regras:

```powershell
powershell.exe -NoProfile -STA -File .\.agents\skills\cad-link-export-glb\scripts\Invoke-CadLinkGlb.ps1
```

Identifique o **caminho exato** do item na lista de documentos abertos. Não use o
documento ativo por conveniência: outra montagem pode conter trabalho não salvo.
Compare código, nome de arquivo e pasta; preserve zeros à esquerda. Não troque
silenciosamente um caminho `R:` por UNC ou escolha um estado de modelo ambíguo.

Quando a exportação estiver solicitada e o documento correto estiver salvo:

```powershell
powershell.exe -NoProfile -STA -File .\.agents\skills\cad-link-export-glb\scripts\Invoke-CadLinkGlb.ps1 -DocumentPath 'R:\Itens\DEMO-001\DEMO-001.ipt' -Export
```

O caminho acima é ilustrativo; use o caminho descoberto na estação. Para abrir
um arquivo que ainda não está carregado, acrescente `-OpenIfNeeded` somente quando
a abertura desse item estiver no escopo autorizado. O helper abre invisivelmente
e fecha apenas o documento que ele abriu, se continuar limpo e inalterado. Não
fecha documentos do engenheiro. Abrir um arquivo pode executar eventos iLogic
já configurados na instalação; prefira um documento já aberto no piloto.

Leia o JSON retornado. Considere sucesso somente com GLB novo validado e
`source_unchanged: true`. Um retorno zero do iLogic, sozinho, não comprova exportação:
a regra preserva o GLB anterior quando falha. Se falhar, leia
`%LOCALAPPDATA%\CAD-link\Inventor\export.log` e o erro do helper. Se houver documento
sujo, referência ausente, atualização pendente ou Inventor ocupado, relate o
impedimento; não salve, descarte, atualize ou tente repetidamente por conta própria.

## Configuração e automatismo

A configuração é `%LOCALAPPDATA%\CAD-link\Inventor\export.xml`. O helper exige
`Enabled=true`, `ItemsRoot` correto e limite de bytes válido; não altera esses
valores automaticamente. A regra exporta apenas `ItemsRoot\codigo\codigo.ipt` ou
`.iam`, para o GLB de mesmo nome. A descoberta do exportador exige uma única opção
compatível ou `TranslatorClassId` explícito. Use os arquivos `export.example.xml`
e `README.pt-BR.md` do companion encontrado para configurar uma nova estação.

Para automatizar, valide primeiro peça e montagem manualmente e depois use as
abas globais **Peças** e **Montagens** dos gatilhos iLogic, no evento **Após salvar
documento**. Preserve os vínculos existentes em `RulesOnEvents.xml`. Não grave
eventos diretamente no XML, altere templates/IPJ ou enfraqueça a segurança do
iLogic para contornar uma falha. Não vincule a regra de inspeção ao evento.

Salvar uma peça não regenera automaticamente todas as montagens que a utilizam.
As montagens precisam ser atualizadas e salvas no Inventor. O GLB representa a
posição, estado e aparência exportados; validar no Odoo faz parte do piloto.

Fontes: [API de execução de regra externa](https://help.autodesk.com/cloudhelp/2021/ENU/Inventor-iLogic-API/files/html/20a9a482-0e9c-6b88-a6f2-e200b332ee62.htm),
[acesso à automação iLogic](https://blog.autodesk.io/automate-creation-of-named-geometry/),
[eventos compartilhados](https://help.autodesk.com/cloudhelp/2022/ENU/Inventor-iLogic/files/GUID-B14A47F4-81D2-4627-A973-2BC7F790DF89.htm).
