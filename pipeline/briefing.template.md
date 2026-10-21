# BRIEFING: atualização do cérebro de {DONO} (vault Markdown no formato Obsidian)

{PERFIL}

## Tarefa
O vault já existe e cobre de {INICIO_VAULT} até {INICIO}. Chegaram {N_MSGS} mensagens novas, de {INICIO} a {FIM}. Você ATUALIZA as notas da sua área com o que mudou. Não reescreve o que já existe.
Vault: {VAULT}
Extrato da sua área (já redigido): {EXTRATO}. Formato das linhas: `MM-DD HH:MM QUEM: texto`. {EU} = {DONO}. Em conversa sigilosa, o outro lado é {ELE} e a conversa tem alias.
Leia o extrato inteiro, em blocos. Use busca no vault para confirmar contagens e datas.

## Como atualizar
1. Liste a pasta da sua área e leia as notas ligadas ao que o extrato traz. Busque no vault o nome canônico antes de criar nota.
2. Em nota existente: acrescente no fim da seção "## Fatos" linhas datadas (`- AAAA-MM-DD: fato`). Crie a seção "## Atualização {INICIO} a {FIM}" só se houver padrão novo, pendência nova ou pendência resolvida. Não apague nada. Fato superado recebe "(superado em AAAA-MM-DD, ver Atualização)". Atualize o campo `periodo:` das notas que tocar.
3. Crie nota nova só para assunto, papel ou decisão novos que o extrato sustenta. Use o formato abaixo.
4. Na nota "Eventos ..." da sua área, acrescente linhas no formato `- AAAA-MM-DD | Domínio | evento em 1 frase | [[Nota relacionada]]`. Só o que o extrato comprova.
5. Pendência resolvida no extrato: diga. Pendência nova: acrescente na nota de pendências da área.
6. Cada nota nova liga a pelo menos 3 outras com `[[Título]]` e meia frase de motivo. O alvo do link precisa existir.

## Formato de nota nova
```
---
tipo: pessoa | projeto | organizacao | tema | decisao | fluxo | resposta | voz | rotina | financeiro | viagem | lazer | periodo
dominio: Profissional | Pessoal | Lazer | Viagens | Financeiro
tags: [palavras, curtas]
relacionados: ["[[Título 1]]", "[[Título 2]]"]
periodo: {INICIO} a {FIM}
confianca: alta | media | baixa
fonte: "origem das mensagens"
---
# Título

(Resumo de 1 a 2 frases.)

## Fatos
## Padrão
## Em aberto
## Ligações
```

## Estilo
- Frase curta. Voz ativa. Uma ideia por frase.
- Sem travessão. Sem enchimento ("é importante ressaltar", "vale destacar", "no contexto de", "em suma").
- Não invente fato nem número. Inferência leva "INFERÊNCIA:" e confiança baixa. Sem prova no extrato: "NÃO VERIFICADO".
- Datas em AAAA-MM-DD. Frequência só com contagem real.
- Sem elogio, sem diagnóstico, sem traço de personalidade.

## Sigilo (obrigatório)
- Conversa sigilosa: NUNCA grave nome, documento, número de processo, telefone, e-mail, endereço, conta ou valor que identifique pessoa. Use o alias ou o papel. Padrões sim; pessoas não.
- Saúde, religião, política, sexualidade e intimidade de terceiros: sem detalhe. Registre só o que afeta a rotina de {DONO}.
- Conversa de família sobre desentendimento ou sentimento: registre só a decisão prática, sem citar falas.
- Sobre {DONO}: atividade e decisão, não diagnóstico nem estado emocional.
- Senha, token, chave e código: nunca, mesmo que apareçam.
- Terceiros em grupo: resuma o tema. Citação literal só de falas de {DONO}, até 25 palavras, sem dado pessoal.
{REGRAS_EXTRAS}

## Entrega (resposta final, no máximo 12 linhas)
Quantas notas atualizou e quantas criou (títulos das criadas), os 3 achados mais fortes do período e o que ficou NÃO VERIFICADO. Não cole conteúdo das notas.
