# Automação Zabbix → Google Sheets (Rogue ONU)

Script em Python que autentica no **Zabbix (via Selenium)**, coleta alertas de **Rogue ONU** e atualiza uma **planilha do Google Sheets** automaticamente, criando abas por sigla (ANATEL) e evitando duplicidades. Inclui agendamento a cada 5 minutos.

---

## 📌 Visão geral

- Login no Zabbix (Selenium/Chrome headless).
- Leitura do dashboard e extração de alertas “**Rogue ONU**”.
- Classificação por **sigla** no nome do host.
- Criação automática de **abas** por sigla na planilha.
- **Append** somente de **novos** registros (sem duplicar).
- Agendamento de execução a cada **5 minutos**.

---

## 🚀 Recursos principais

- Zero credencial hardcoded: usa **variáveis de ambiente**.
- Criação de abas on-demand com cabeçalhos.
- Mapeamento flexível de siglas (lista editável).
- Logs simples no stdout.

---

## 📦 Pré-requisitos

- **Python 3.10+**
- Acesso ao **Zabbix** e a um dashboard com eventos/links de “Rogue ONU”.
- Uma planilha no **Google Sheets** (compartilhada com o service account).
- **Chrome** e **chromedriver** (instalado automaticamente via `webdriver-manager`).

---

## 🔧 Instalação

```bash
git clone <seu-repo>
cd <seu-repo>
python -m venv .venv
. .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
