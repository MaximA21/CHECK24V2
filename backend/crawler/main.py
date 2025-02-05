from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta


class KickerScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-notifications')
        self.driver = webdriver.Chrome(options=options)

    def standardize_url(self, url):
        base_url = '/'.join(url.split('/')[:-1])
        return f"{base_url}/spielinfo"

    def accept_cookies(self):
        try:
            time.sleep(5)
            btn2 = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div/div/div/div[3]/div[1]/div/a")
            btn2.click()
            time.sleep(2)  # Kurz warten bis Banner weg ist
        except Exception as e:
            print(e)

    def get_tv_info(self, url):
        self.driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        providers = set()

        # Finde zuerst die Tabelle die "Streaming" in der Überschrift hat
        headers = soup.find_all('th')
        for header in headers:
            if header.text.strip() == "Streaming":
                # Von der Überschrift zur Tabelle
                streaming_table = header.find_parent('table')
                if streaming_table:
                    # Finde alle Bilder in dieser Tabelle
                    images = streaming_table.find_all('img')
                    for img in images:
                        if img.get('alt'):
                            providers.add(img['alt'])

        return list(providers)

    def get_games(self, url):
        self.driver.get(url)
        self.accept_cookies()

        # HTML holen und mit BeautifulSoup parsen
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Debug: Schauen was wir tatsächlich finden
        print("Anzahl Game Lists:", len(soup.find_all(class_='kick__v100-gameList')))

        # Datum aus URL extrahieren
        url_parts = self.driver.current_url.split('/')
        if len(url_parts) >= 2:
            game_date = url_parts[-2]  # Vorletztes Element

        matches = []
        game_lists = soup.find_all(class_='kick__v100-gameList')

        for game_list in game_lists:
            # Liga-Name extrahieren
            league_header = game_list.find(class_='kick__v100-gameList__header')
            league = league_header.text.strip().replace(" ", "") if league_header else "Unbekannte Liga"
            if not any(element in league for element in ["Bundesliga", "SerieA", "LaLiga", "Ligue1", "England,PremierLeague"]):
                continue

            # Spiele in dieser Liga finden
            game_rows = game_list.find_all(class_='kick__v100-gameList__gameRow')

            for game_row in game_rows:
                try:
                    # Game Cell finden
                    game_cell = game_row.find(class_='kick__v100-gameCell')

                    if game_cell:
                        # Teams finden
                        teams = game_cell.find_all(class_='kick__v100-gameCell__team')
                        if len(teams) >= 2:
                            home_team = teams[0].find(class_='kick__v100-gameCell__team__name').text.strip()
                            away_team = teams[1].find(class_='kick__v100-gameCell__team__name').text.strip()

                            # Zeit finden - jetzt beide Teile
                            time_element = game_cell.find(class_='kick__v100-scoreBoard')
                            print(time_element)
                            if time_element:

                                time_parts = time_element.find_all(class_='kick__v100-scoreBoard__dateHolder')
                                if len(time_parts) >= 2:
                                    for time_part in time_parts:
                                        time_part = time_part.text.strip()
                                        if time_part[0].isdigit():
                                            game_time = time_part  # Uhrzeit

                            # Vorschau-Link finden
                            link_element = game_row.find(class_='kick__v100-gameList__gameRow__stateCell')
                            if link_element:
                                link = link_element.find('a')
                                if link and 'href' in link.attrs:
                                    detail_url = f"https://www.kicker.de{link['href']}"
                                    standardized_url = self.standardize_url(detail_url)

                                    matches.append({
                                        'league': league,
                                        'home': home_team,
                                        'away': away_team,
                                        'date': game_date,
                                        'time': game_time,
                                        'detail_url': standardized_url,
                                        'tv': self.get_tv_info(standardized_url)
                                    })

                except Exception as e:
                    print(f"Fehler beim Scrapen eines Spiels: {e}")
                    continue

        return matches

    def close(self):
        self.driver.quit()


# Test
if __name__ == "__main__":
    scraper = KickerScraper()
    try:
        # Heutiges Datum
        heute = datetime.now()
        # Liste für die nächsten 7 Tage
        datums_array = [(heute + timedelta(days=i)).strftime('%d-%m-%Y') for i in range(3)]

        games = []
        for datum in datums_array:
            games += scraper.get_games(f"https://www.kicker.de/fussball/heute-live/{datum}/6")
        for game in games:
            print(game)
    finally:
        scraper.close()
