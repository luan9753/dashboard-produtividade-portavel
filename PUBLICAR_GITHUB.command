#!/bin/bash
cd "$(dirname "$0")"

echo
echo " [1/4] Atualizando dashboard com dados do AuraVTC..."
python3 atualizar_dashboard.py
if [ $? -ne 0 ]; then
  echo
  echo " ERRO ao atualizar. Nada foi enviado ao GitHub."
  read -r -p "Pressione Enter para fechar..."
  exit 1
fi

echo
echo " [2/4] Preparando arquivos para o GitHub..."
git add \
  dashboard_produtividade_completo.html \
  index.html \
  equip-card-overrides.css \
  atualizar_dashboard.py \
  ATUALIZAR_DASHBOARD.command \
  ATUALIZAR_DASHBOARD.sh \
  ABRIR_DASHBOARD.command \
  INICIAR_DASHBOARD_REDE.command \
  INICIAR_DASHBOARD_REDE.sh \
  PUBLICAR_GITHUB.command \
  PUBLICAR_GITHUB.bat \
  gerar_analitico_syos_pendentes.py \
  gerar_analitico_outros_pendentes.py \
  gerar_analitico_syos_zerados.py \
  listar_sensor_web_pendentes.py \
  LEIA-ME_backup_dashboard.txt \
  .gitignore

if git diff --cached --quiet; then
  echo
  echo " Nenhuma alteracao detectada apos a atualizacao."
  echo " O GitHub ja esta com a mesma versao local."
  echo
  echo " Link: https://luan9753.github.io/dashboard-produtividade-portavel/"
  read -r -p "Pressione Enter para fechar..."
  exit 0
fi

echo
echo " [3/4] Criando commit..."
DATA=$(date "+%Y-%m-%d")
HORA=$(date "+%H:%M")
git commit -m "Atualiza dados do dashboard (${DATA} ${HORA})"
if [ $? -ne 0 ]; then
  echo " ERRO ao criar commit."
  read -r -p "Pressione Enter para fechar..."
  exit 1
fi

echo
echo " [4/4] Enviando para o GitHub..."
git push origin main
if [ $? -ne 0 ]; then
  echo
  echo " ERRO no push. Verifique internet, login no GitHub e branch main."
  read -r -p "Pressione Enter para fechar..."
  exit 1
fi

echo
echo " Publicado com sucesso!"
echo
echo " Aguarde 1-2 minutos e abra:"
echo " https://luan9753.github.io/dashboard-produtividade-portavel/"
echo
read -r -p "Pressione Enter para fechar..."
