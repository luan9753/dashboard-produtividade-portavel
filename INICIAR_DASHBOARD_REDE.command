#!/bin/bash
cd "$(dirname "$0")"
PORT=8080

IP=$(ipconfig getifaddr en0 2>/dev/null)
if [ -z "$IP" ]; then
  IP=$(ipconfig getifaddr en1 2>/dev/null)
fi
if [ -z "$IP" ]; then
  IP="127.0.0.1"
fi

echo
echo "Dashboard de produtividade disponivel na rede local:"
echo
echo "  http://${IP}:${PORT}/dashboard_produtividade_completo.html"
echo
echo "Mantenha esta janela aberta enquanto quiser acessar pelo celular, tablet ou notebook."
echo "Para parar, pressione Ctrl+C."
echo

python3 -m http.server "$PORT" --bind 0.0.0.0
