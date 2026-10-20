import os
import re
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright

EMAIL_ADRESSE = os.environ.get("EMAIL_ADRESSE")
EMAIL_MDP = os.environ.get("EMAIL_MDP")

URL_FC27 = "https://www.allkeyshop.com/blog/buy-ea-sports-fc-27-steam-account-compare-prices/"
URL_MW4 = "https://www.allkeyshop.com/blog/buy-call-of-duty-modern-warfare-4-steam-account-compare-prices/"

def envoyer_email(prix_fc27, prix_mw4):
    if not EMAIL_ADRESSE or not EMAIL_MDP:
        print("⚠️ Erreur : EMAIL_ADRESSE ou EMAIL_MDP manquant dans Settings > Secrets.")
        return

    str_fc27 = f"{prix_fc27:.2f} €" if prix_fc27 else "N/A"
    str_mw4 = f"{prix_mw4:.2f} €" if prix_mw4 else "N/A"

    msg = EmailMessage()
    msg["Subject"] = f"github - eafc 27 : {str_fc27} / MW4 : {str_mw4}"
    msg["From"] = EMAIL_ADRESSE.strip()
    msg["To"] = EMAIL_ADRESSE.strip()
    msg.set_content(
        f"Bonjour,\n\n"
        f"Voici les meilleurs prix actuels relevés :\n\n"
        f"⚽ EA SPORTS FC 27 (Compte Steam) : {str_fc27}\n"
        f"Lien : {URL_FC27}\n\n"
        f"🎮 Call of Duty Modern Warfare 4 (Compte Steam) : {str_mw4}\n"
        f"Lien : {URL_MW4}"
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADRESSE.strip(), EMAIL_MDP.replace(" ", "").strip())
        smtp.send_message(msg)
    print(f"📧 E-mail envoyé avec succès à {EMAIL_ADRESSE} !")

def analyser_page(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(6000)
    
    html = page.content()
    texte = page.inner_text("body")

    if "MERCHANT" in texte:
        texte = texte.split("MERCHANT", 1)[1]
    for fin in ["Show all offers", "Historical Lowest Prices", "TOP 50"]:
        if fin in texte:
            texte = texte.split(fin, 1)[0]

    prix_trouves = []
    for ligne in texte.split("\n"):
        ligne = ligne.strip()
        if not ligne.startswith("+"):
            m = re.search(r'^(\d+[\.,]\d{2})\s*(?:€|\$|EUR|USD)?$', ligne)
            if m:
                val = float(m.group(1).replace(",", "."))
                if 12.0 <= val <= 150.0:
                    prix_trouves.append(val)

    if not prix_trouves:
        for m in re.finditer(r'(\d{2}[\.,]\d{2})\s*€', html):
            val = float(m.group(1).replace(",", "."))
            if 12.0 <= val <= 150.0:
                prix_trouves.append(val)

    return min(prix_trouves) if prix_trouves else None

def extraire_tous_les_prix():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            locale="fr-FR"
        )
        page = context.new_page()
        
        prix_fc27 = analyser_page(page, URL_FC27)
        prix_mw4 = analyser_page(page, URL_MW4)
        
        browser.close()
        
    return prix_fc27, prix_mw4

if __name__ == "__main__":
    prix_fc27, prix_mw4 = extraire_tous_les_prix()
    if prix_fc27 or prix_mw4:
        print(f"✅ Prix relevés -> FC 27 : {prix_fc27} € | MW4 : {prix_mw4} €")
        envoyer_email(prix_fc27, prix_mw4)
    else:
        print("⚠️ Aucun prix détecté sur les pages.")
