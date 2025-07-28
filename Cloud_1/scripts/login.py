from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.settings import settings
from utils.helpers import CSS


def run(driver):
    """
    Realiza o login no portal, reutilizando sessão se possível.

    Parâmetros:
      driver: instância de Selenium WebDriver (Chrome)

    Fluxo:
      1) driver.get(settings.portal_url)
      2) tenta botão “Continuar” (ID="trauth-continue-signin-btn")
      3) verifica campo de pesquisa (CSS["pesquisa"])
         • se existe: já está logado → return
      4) tenta preencher diretamente senha (ID="password")
         • se não, preenche usuário (NAME="username"), envia e aguarda campo de senha
      5) envia senha e clica no botão de submit
      6) trata possível segundo clique em “Entrar” (mesmo ID do passo 2)
      7) aguarda campo de pesquisa, garantindo que a página principal carregou
    """
    print("[login] Iniciando fluxo de login")
    driver.get(settings.portal_url)
    print("[login] Página carregada:", settings.portal_url)

    # 1) botão “Continuar” após reautenticação (pode não existir)
    try:
        print("[login] Tentando clicar em 'Continuar'")
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "trauth-continue-signin-btn"))
        ).click()
        print("[login] Botão 'Continuar' clicado")
    except TimeoutException:
        # Não apareceu → possivelmente já na tela de login ou mesmo logado
        pass

    # 2) verifica se já está logado, olhando campo de pesquisa do grid
    try:
        print("[login] Verificando se já está logado (campo pesquisa)...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CSS["pesquisa"]))
        )
        print("[login] Já está logado, encerrando login")
        return
    except TimeoutException:
        print("[login] Não está logado — preenchendo usuário e senha")
        pass

    # 3) fluxo de autenticação: email → senha
    senha_input = None
    try:
        # Se o campo de senha já estiver visível, pula etapa de usuário
        senha_input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "password"))
        )
        print("[login] Campo de senha já está visível, pulando etapa do usuário.")
    except TimeoutException:
        # Preenche usuário e avança para tela de senha
        print("[login] Digitando usuário:", settings.onvio_user)
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.NAME, "username"))
        ).send_keys(settings.onvio_user)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        print("[login] Usuário enviado — aguardando campo de senha")
        senha_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "password"))
        )

    # 4) preenche e envia senha
    print("[login] Digitando senha")
    senha_input.send_keys(settings.onvio_pass)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], button._button-login-password').click()
    print("[login] Senha enviada — aguardando confirmação de login ou botão 'Entrar' extra")

    # 5) lida com possível botão “Entrar” adicional
    try:
        print("[login] Verificando se precisa clicar em 'Entrar' novamente...")
        btn_entrar = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "trauth-continue-signin-btn"))
        )
        btn_entrar.click()
        print("[login] Botão 'Entrar' clicado após senha")
    except TimeoutException:
        print("[login] Botão 'Entrar' extra não apareceu — seguindo")

    # 6) garante que a página principal carregou (campo de pesquisa)
    if not driver.current_url.endswith("/service-requesting/general"):
        driver.get(settings.portal_url)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CSS["pesquisa"]))
    )
    print("[login] Login concluído com sucesso")
