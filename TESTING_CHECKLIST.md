# 📋 Testing Checklist - Item Database Update

## 🚀 Quick Start

```bash
# 1. Testes rápidos (sem Core Keeper dump)
cd scripts
python3 quick_test.py

# 2. Depois de exportar assets com AssetRipper
python3 items.py

# 3. Validar dados extraídos
python3 test_items.py

# 4. Deploy dos arquivos
./deploy.py
```

## ✅ Pré-Execução

### Ambiente
- [ ] Python 3.8+ instalado
- [ ] Virtual environment criado e ativado
- [ ] `pip install -r scripts/requirements.txt` executado
- [ ] Scripts têm permissão de execução (`chmod +x scripts/*.py`)

### Verificações Iniciais
- [ ] Clonar/atualizar repositório
- [ ] Estar na branch `update/complete-items-database`
- [ ] Pasta `scripts/` existe e contém todos os arquivos
- [ ] Arquivo `scripts/blacklist.py` existe
- [ ] Arquivo `scripts/util.py` existe

## 🧪 Teste 1: Quick Test (Sem Assets)

**Comando:**
```bash
cd scripts
python3 quick_test.py
```

**Resultado Esperado:**
```
✓ JSON Structure                         ✓ PASS
✓ JSON Serialization                     ✓ PASS
✓ Validation Script                      ✓ PASS
✓ Items Extraction Script                ✓ PASS
✓ Blacklist Integrity                    ✓ PASS
✓ Util Functions                         ✓ PASS
✓ Required Packages                      ✓ PASS

Results: 7/7 tests passed
✓ All tests PASSED!
```

**Checklist:**
- [ ] Saída contém "7/7 tests passed"
- [ ] Nenhum erro ou traceback
- [ ] Mensagens "Next steps" aparecem
- [ ] Leva menos de 5 segundos

## 🎮 Teste 2: Asset Extraction (Com Core Keeper)

**Pré-requisitos:**
- [ ] AssetRipper instalado
- [ ] Core Keeper instalado
- [ ] Assets exportados para `./dump/`

**Comando:**
```bash
cd scripts
python3 items.py
```

**Resultado Esperado:**
- [ ] Script executa sem erros
- [ ] Arquivo `out/item/item-data.json` criado (150-200 KB)
- [ ] Arquivo `out/item/item-spritesheet.png` criado (350-450 KB)
- [ ] Arquivo `out/item/extraction_report.txt` criado
- [ ] Leva 2-5 minutos para completar

**Verificações do Relatório:**
```bash
cat out/item/extraction_report.txt
```

Verificar:
- [ ] Seção "EXTRACTION STATISTICS" mostra números válidos
- [ ] Total de items > 1000
- [ ] Total de items processados >= 80% dos encontrados
- [ ] Seção "SKIPPED ITEMS BREAKDOWN" explica items pulados
- [ ] Nenhum erro crítico na seção "ERRORS"
- [ ] Timestamp correto no final

**Exemplo de Estatísticas Esperadas:**
```
Total Objects Found:               ~2000
Total Items Successfully Processed: ~1200
No Translation:                    ~50
No Image Found:                    ~100
Duplicates Skipped:                ~20
Blacklisted Items:                 ~150
Wrong Object Type:                 ~400
Invalid Icon:                      ~80
```

## ✔️ Teste 3: Data Validation

**Comando:**
```bash
cd scripts
python3 test_items.py
```

**Resultado Esperado:**
- [ ] Script executa sem erros
- [ ] Arquivo `out/item/validation_report.txt` criado
- [ ] Todos os testes retornam "✓ PASS"

**Checklist de Testes:**
```
✓ JSON Loading                           ✓ PASS
✓ JSON Structure                         ✓ PASS
✓ Items Validation                       ✓ PASS
✓ Set Bonuses Validation                 ✓ PASS
✓ Icon Indices Validation                ✓ PASS
✓ Special Properties                     ✓ PASS
✓ Spritesheet Validation                 ✓ PASS
```

- [ ] Todos os 7 testes passam
- [ ] Status final é "✓ PASSED"
- [ ] Nenhum erro na seção ERRORS

**Verificações de Estatísticas:**
```bash
cat out/item/validation_report.txt
```

Verificar:
- [ ] Total Items: >= 1000
- [ ] Total Set Bonuses: >= 10
- [ ] Items by Rarity:
  - [ ] Rarity 0 (Common): >= 600
  - [ ] Rarity 1 (Uncommon): >= 300
  - [ ] Rarity 2 (Rare): >= 150
  - [ ] Rarity 3+ (Epic/Legendary): >= 50
- [ ] Items with special properties > 0 (exceto talvez ingredients)

## 📦 Teste 4: Deployment

**Comando:**
```bash
./scripts/deploy.py
```

**Resultado Esperado:**
- [ ] Arquivo `src/assets/item-data.json` atualizado
- [ ] Arquivo `src/assets/item-spritesheet.png` atualizado
- [ ] Script completa sem erros

**Verificações Manuais:**
```bash
# Verificar se arquivos foram copiados
ls -lh src/assets/item-*.{json,png}

# Comparar timestamps
ls -lt src/assets/item-* out/item/item-*
```

- [ ] Timestamps do `src/assets/` são recentes
- [ ] Tamanhos de arquivo são similares ao `out/item/`

## 🎨 Teste 5: Angular App (Visual)

**Pré-requisitos:**
- [ ] Deployment completado
- [ ] Angular app compilado (`ng build`)
- [ ] App rodando (`ng serve`)

**Teste 5.1: Carregamento de Items**
- [ ] Abrir browser em http://localhost:4200
- [ ] Esperar carregamento da página
- [ ] Verificar se não há console errors sobre item-data.json

**Teste 5.2: Item Browser**
- [ ] Navegar para aba de Inventory
- [ ] Verificar se items aparecem com ícones
- [ ] Ícones devem estar nítidos e coloridos
- [ ] Scroll deve funcionar suavemente

**Teste 5.3: Drag and Drop**
- [ ] Selecionar um item do browser
- [ ] Arrastar para inventário
- [ ] Item deve aparecer na posição correta
- [ ] Quantidade deve ser editável

**Teste 5.4: Pesquisa**
- [ ] Digitar nome de item na busca
- [ ] Resultados devem aparecer
- [ ] Ícones devem ser exibidos
- [ ] Pesquisa é case-insensitive

**Teste 5.5: Set Bonuses**
- [ ] Se houver items com set bonus
- [ ] Verificar se set bonus é exibido corretamente
- [ ] Descrição de bonus deve aparecer

**Checklist Visual:**
- [ ] Nenhum item com ícone quebrado ou genérico
- [ ] Layout responsivo
- [ ] Performance aceitável (sem lag ao scroll)
- [ ] Cores vibrantes dos ícones
- [ ] Texturas bem definidas

## 📊 Teste 6: Data Integrity

**Verificar Duplicatas:**
```bash
python3 -c "import json; data=json.load(open('out/item/item-data.json')); print(f'Total: {len(data[\"items\"])}, Unique IDs: {len(set(int(k) for k in data[\"items\"].keys()))}')"
```
- [ ] Total deve ser igual a Unique IDs (sem duplicatas)

**Verificar Índices Sequenciais:**
```bash
python3 -c "import json; data=json.load(open('out/item/item-data.json')); indices=set(item['iconIndex'] for item in data['items'].values()); expected=set(range(max(indices)+1)); missing=expected-indices; print(f'Missing indices: {missing if missing else \"None\"}')"
```
- [ ] Nenhum índice faltante

**Verificar Campos Obrigatórios:**
```bash
python3 << 'EOF'
import json
data = json.load(open('out/item/item-data.json'))
required = ['objectID', 'name', 'description', 'initialAmount', 'objectType', 'rarity', 'isStackable', 'iconIndex']
missing = []
for item_id, item in data['items'].items():
    for field in required:
        if field not in item:
            missing.append((item_id, field))
print(f'Missing fields: {len(missing)}')
for item_id, field in missing[:5]:
    print(f'  Item {item_id} missing {field}')
EOF
```
- [ ] Saída: "Missing fields: 0"

## 🔍 Teste 7: Performance

**Mediar Tempo de Extração:**
```bash
time python3 scripts/items.py
```
- [ ] Real time: 2-5 minutos
- [ ] Sem timeouts

**Mediar Tempo de Validação:**
```bash
time python3 scripts/test_items.py
```
- [ ] Real time: < 30 segundos
- [ ] Sem timeouts

**Tamanho de Arquivos:**
```bash
ls -lh out/item/*
```
- [ ] item-data.json: 150-200 KB
- [ ] item-spritesheet.png: 350-450 KB
- [ ] extraction_report.txt: 5-10 KB
- [ ] validation_report.txt: 5-10 KB

## 🐛 Teste 8: Error Handling

**Teste 8.1: Missing Files**
```bash
rm out/item/item-data.json
python3 scripts/test_items.py
```
- [ ] Script detecta arquivo faltante
- [ ] Mensagem de erro clara
- [ ] Sem traceback desagradável

**Teste 8.2: Corrupted JSON**
```bash
echo '{broken json}' > out/item/item-data.json
python3 scripts/test_items.py
```
- [ ] Script detecta JSON inválido
- [ ] Mensagem de erro clara
- [ ] Sem crash

**Teste 8.3: Missing Dump**
```bash
rm -rf dump/
python3 scripts/items.py 2>&1 | head -20
```
- [ ] Script falha gracefully
- [ ] Mensagem de erro útil
- [ ] Sugestão de como resolver

## 📝 Teste 9: Documentation

- [ ] `ITEM_DATABASE_UPDATE_GUIDE.adoc` existe
- [ ] `CHANGELOG_ITEMS_DATABASE.md` existe
- [ ] `TESTING_CHECKLIST.md` existe (este arquivo)
- [ ] Todos os scripts têm docstrings
- [ ] README.adoc foi atualizado

## ✨ Teste 10: Git Integration

**Status da Branch:**
```bash
git status
git log --oneline -5
```
- [ ] Branch é `update/complete-items-database`
- [ ] Commits estão presentes
- [ ] Sem conflitos

**Diferenças:**
```bash
git diff main -- scripts/items.py | head -50
git diff main -- scripts/ | grep '^diff' | wc -l
```
- [ ] Alterações são significativas
- [ ] Múltiplos arquivos alterados

## 📋 Sign-Off

### Desenvolvedor
- [ ] Todos os testes locais passaram
- [ ] Código foi revisado
- [ ] Documentação está atualizada
- [ ] Não há console warnings/errors

### Testador
- [ ] Quick tests passaram
- [ ] Extraction funciona
- [ ] Validation funciona
- [ ] Angular app funciona
- [ ] Nenhum bug encontrado

### Aprovador
- [ ] Código review completo
- [ ] Testes satisfatórios
- [ ] Documentação adequada
- [ ] Ready for merge

## 📞 Troubleshooting Rápido

| Problema | Solução |
|----------|----------|
| `ModuleNotFoundError: unityparser` | `pip install -r scripts/requirements.txt` |
| `FileNotFoundError: dump/...` | Exportar Core Keeper com AssetRipper |
| Items faltando | Verificar `extraction_report.txt` |
| JSON inválido | Executar `test_items.py` para diagnóstico |
| Spritesheet vazio | Verificar se há texturas em dump/ |
| Quick test falha | Verificar Python version >= 3.8 |

## 🎉 Conclusão

Quando todos os testes forem concluídos com sucesso:
1. [ ] Todos os checkboxes estão marcados
2. [ ] Nenhum blocker encontrado
3. [ ] Ready para merge na main
4. [ ] Deploy em produção pode prosseguir

**Data de Conclusão:** _______________

**Assinatura:** _______________
