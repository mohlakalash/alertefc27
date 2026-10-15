import re
import requests
from bs4 import BeautifulSoup

# --- VOS 2 PARAMÈTRES À PERSONNALISER ---
PRIX_CIBLE = 30.00  # Laissez 30.00 pour le premier test (le jeu est à ~26€), vous recevrez l'alerte tout de suite !
SUJET_NTFY = "alertefc27"  # Mettez ici le nom exact créé dans l'appli ntfy à l'étape 1

URL_PRODUIT = "https://www.allkeyshop.com/blog/buy-ea-sports-fc-27-steam-account-compare-prices/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
}

def extraire_meilleure_offre(html):
    soup = BeautifulSoup(html, "html.parser")
    texte = soup.get_text(separator="\n")
    
    # Découpe uniquement le tableau des marchands (ignore le TOP 50 en bas de page)
    if "MERCHANT" in texte and "Show all offers" in texte:
        texte = texte.split("MERCHANT", 1)[1].split("Show all offers", 1)[0]

    blocs = re.split(r'\n(?=[A-Za-z0-9\s\.]+\n+(?:Standard|Ultimate)\s+ACCOUNT)', texte)
    offres = []
    for bloc in blocs:
        lignes = [l.strip() for l in bloc.split('\n') if l.strip()]
        if len(lignes) < 4:
            continue
        vendeur = lignes[0]
        prix_trouves = []
        for l in lignes:
            if not l.startswith('+'):
                m = re.search(r'^(\d+(?:[\.,]\d+)?)\s*€$', l)
                if m:
                    prix_trouves.append(float(m.group(1).replace(',', '.')))
        if prix_trouves:
            offres.append((prix_trouves[-1], vendeur))

    return min(offres, key=lambda x: x[0]) if offres else None

if __name__ == "__main__":
    print("Vérification de la page AllKeyShop en cours...")
    r = requests.get(URL_PRODUIT, headers=HEADERS, timeout=20)
    if r.status_code == 200:
        offre = extraire_meilleure_offre(r.text)
        if offre:
            prix, vendeur = offre
            print(f"Meilleur prix trouvé : {prix:.2f} € chez {vendeur} (Seuil fixé : {PRIX_CIBLE:.2f} €)")
            if prix <= PRIX_CIBLE:
                print("Seuil atteint ! Envoi de la notification...")
                requests.post(
                    f"https://ntfy.sh/{SUJET_NTFY}",
                    data=f"EA SPORTS FC 27 est à {prix:.2f} € chez {vendeur} !\n{URL_PRODUIT}".encode("utf-8"),
                    headers={
                        "Title": "ALERTE PRIX : EA SPORTS FC 27",
                        "Priority": "high",
                        "Tags": "rotating_light,video_game"
                    }
                )
        else:
            print("Impossible de trouver les offres sur la page.")
    else:
        print(f"Erreur d'accès à la page (Code HTTP {r.status_code})")
