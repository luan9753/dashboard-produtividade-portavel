#!/bin/bash
cd "$(dirname "$0")"

echo
echo " Atualizando dashboard com dados do AuraVTC (ODBC)..."
python3 atualizar_dashboard.py
if [ $? -ne 0 ]; then
  echo
  echo " ERRO ao atualizar. Veja a mensagem acima."
  echo " Se o HTML estiver corrompido, o script tenta restaurar do WorkSpace."
  read -r -p "Pressione Enter para fechar..."
  exit 1
fi

echo
echo " Concluido. Abrindo dashboard..."
open dashboard_produtividade_completo.html
