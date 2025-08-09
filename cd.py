import os
import time
import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.oauth2.service_account import Credentials
from webdriver_manager.chrome import ChromeDriverManager
from gspread.exceptions import WorksheetNotFound

# --- Config via variáveis de ambiente ---
ZABBIX_BASE_URL = os.environ.get("ZABBIX_BASE_URL", "https://SEU-ZABBIX/zabbix")
URL_LOGIN = f"{ZABBIX_BASE_URL}/index.php"
URL_INCIDENTES = f"{ZABBIX_BASE_URL}/zabbix.php?action=dashboard.view"

ZABBIX_USER = os.environ.get("ZABBIX_USER", "")
ZABBIX_PASSWORD = os.environ.get("ZABBIX_PASSWORD", "")
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json")
ID_PLANILHA = os.environ.get("GOOGLE_SHEET_ID", "")

SIGLAS_ANATEL = sorted([
    "ANP", "ARO", "ARO-3PT", "ANG", "ARD", "BRE-SP2", "BRE-SP4", "BFE", "BTV", "CMAL", "CAS",
    "CLT", "CQO", "CEG", "CNH", "COA", "CVT", "FAC", "GEI", "HORT", "IEO", "IGA", "IYR", "ITU",
    "JUMR", "JAI", "LJP", "LRA", "LIA", "MST", "PSO", "PCP", "PDA", "PEY", "PLL", "PAA", "PON",
    "RRC", "RPO", "RCO", "RDP", "SALN", "SLO", "SPR", "SPB", "SAP", "SRE", "SRP", "SNG", "SOC",
    "SUM", "TTI", "TIE", "VIN", "OUTROS"
])

def autenticar():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(ID_PLANILHA)

def identificar_sigla(host: str) -> str:
    for sigla in SIGLAS_ANATEL:
        if sigla != "OUTROS" and sigla in host:
            return sigla
    return "OUTROS"

def extrair_rogue_onu_com_selenium():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(URL_LOGIN)

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "name"))).send_keys(ZABBIX_USER)
        driver.find_element(By.NAME, "password").send_keys(ZABBIX_PASSWORD)
        driver.find_element(By.ID, "enter").click()

        driver.get(URL_INCIDENTES)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".dashbrd-grid-container")))
        time.sleep(2)

        incidentes = driver.find_elements(By.CSS_SELECTOR, "a.link-action[aria-label*='Rogue ONU']")
        hosts = driver.find_elements(By.CSS_SELECTOR, "a.link-action[data-menu-popup*='host']")
        datas = driver.find_elements(By.CSS_SELECTOR, "a[href*='tr_events.php']")

        dados = []
        for incidente, host, data in zip(incidentes, hosts, datas):
            h = host.text.strip()
            i = incidente.text.strip()
            d = data.text.strip()
            if h and i and d:
                dados.append((h, i, d))

        return dados

    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        return []

    finally:
        driver.quit()

def atualizar_planilha():
    if not all([ZABBIX_USER, ZABBIX_PASSWORD, ID_PLANILHA]):
        print("Configuração ausente: verifique variáveis de ambiente ZABBIX_USER, ZABBIX_PASSWORD e GOOGLE_SHEET_ID.")
        return

    cliente = autenticar()
    alarmes = extrair_rogue_onu_com_selenium()
    if not alarmes:
        print("Nenhum dado novo para atualizar.")
        return

    planilhas_usadas = {}

    # Garante que as abas existam e tenham cabeçalho
    for host, incidente, data in alarmes:
        sigla = identificar_sigla(host)
        if sigla not in planilhas_usadas:
            try:
                aba = cliente.worksheet(sigla)
            except WorksheetNotFound:
                aba = cliente.add_worksheet(title=sigla, rows="100", cols="3")
                aba.append_row(["Host", "Incidente", "Data"])
            planilhas_usadas[sigla] = aba

    # Evita duplicados e adiciona novos registros
    for sigla, aba in planilhas_usadas.items():
        registros_existentes = aba.get_all_values()
        existentes = set(tuple(row) for row in registros_existentes[1:]) if len(registros_existentes) > 1 else set()

        novos = []
        for host, incidente, data in alarmes:
            if identificar_sigla(host) == sigla:
                linha = (host, incidente, data)
                if linha not in existentes:
                    novos.append(list(linha))

        if novos:
            aba.append_rows(novos, value_input_option="USER_ENTERED")
            print(f"{len(novos)} novos alarmes adicionados na aba '{sigla}'")
        else:
            print(f"Nenhum novo dado para a aba '{sigla}'")

def principal():
    atualizar_planilha()
    import schedule
    schedule.every(5).minutes.do(atualizar_planilha)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    principal()
