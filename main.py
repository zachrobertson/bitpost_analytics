import time
import json
import random
import requests
import datetime
import pyfiglet
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from bs4 import BeautifulSoup

class BitPost:
    def __init__(self):
        custom_fig = pyfiglet.Figlet(font='graffiti')
        ascii_banner = custom_fig.renderText('BitPost Analytics')
        print(ascii_banner)

        self.base_url = 'https://bitpost.app'
        self.data = pd.DataFrame(columns=['author', 'title', 'nw', 'noi'])
        self.users = self._read_user_file('users.txt')

        color_list = list(mcolors.TABLEAU_COLORS.items())
        self.colors = [color_list[i % len(color_list)][0] for i in range(len(self.users))]

        sep_start = datetime.date(2021, 9, 1)
        self.start_unix_time = time.mktime(sep_start.timetuple())

    def _read_user_file(self, filename):
        f = open(filename, 'r')
        users = f.read().split('\n')
        users = [item for item in users[1:]]
        return users

    def _query_profie_page(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, features='html.parser')
        for link in soup.findAll(class_='link dark-gray hover-hot-pink'):
            print(link.attrs)
        next_page = soup.findAll(class_='db w2 h2 link mid-gray br3 pointer | pagination-link')
        if len(next_page) > 0:
            print(next_page)
            link = next_page[0].attrs['href']
            self._query_profie_page(link)

    def _get_post_data_from_tx(self, tx):
        response = requests.get(f'{self.base_url}/tx/{tx}')
        soup = BeautifulSoup(response.content, features='html.parser')

        author = soup.findAll(class_='link fw6 mid-gray hover-hot-pink')
        assert len(author) == 1
        author = author[0].text

        title = soup.findAll(class_='flex-auto mv0 pr3 f1 lh-title')
        assert len(title) == 1
        title = title[0].text

        content = soup.findAll(class_='content-wrap')
        
        if len(content) != 1:
            return author, title, 0, 0

        nw = 0
        for child in content[0].findChildren():
            if child.name == 'p':
                nw += len(child.text.split())
        
        noi = self._get_noi_from_soup(content[0])

        return author, title, nw, noi

    def _get_all_data_for_user(self, user):
        print(
            f'Getting data for {user}'
        )
        url = f'{self.base_url}/u/{user}/bitfeed'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, features='html.parser')
        data = json.loads(soup.text)

        titles = []
        for item in data['tx']:
            if item['timestamp'] < self.start_unix_time:
                break
            tx = item['id']
            author, title, nw, noi = self._get_post_data_from_tx(tx)
            if title not in titles:
                print(
                    f'Saving data for {title} by {user}'
                )
                titles.append(title)
                self.data = self.data.append(
                    {
                        'author' : author,
                        'title' : title,
                        'nw' : nw,
                        'noi' : noi
                    }, ignore_index=True)

    def _get_noi_from_soup(self, soup):
        return len(soup.findAll('img'))

    def _get_all_data(self):
        # Make sure there are not duplicate users
        assert len(self.users) == len(set(self.users))

        for _, user in enumerate(self.users):
            self._get_all_data_for_user(user)

    def _save_data(self):
        print(
            'Saving dataframe to data.csv'
        )
        self.data.to_csv('data.csv', index=False)

    def _run_statistics_on_all_users(self):
        users = list(set(self.data['author'].tolist()))
        avg_nw = []
        avg_noi = []
        tot_nw = []
        tot_noi = []
        for item in users:
            user_nw_list = self.data[self.data['author'] == item]['nw'].tolist()
            user_noi_list = self.data[self.data['author'] == item]['noi'].tolist()

            user_avg_nw = int(sum(user_nw_list) / len(user_nw_list))
            user_tot_nw = sum(user_nw_list)
            
            user_tot_noi = sum(user_noi_list)
            user_avg_noi = (user_tot_noi / len(user_noi_list))

            avg_nw.append(user_avg_nw)
            avg_noi.append(user_avg_noi)
            tot_nw.append(user_tot_nw)
            tot_noi.append(user_tot_noi)
        return users, avg_nw, avg_noi, tot_nw, tot_noi

    def _bar_plot(self, x, y, x_label, y_label):
        plt.bar(
            x, y, color = self.colors
        )
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.xticks(rotation=90)
        plt.subplots_adjust(bottom=0.25)
        plt.grid()
        plt.show()


    def _plot_data(self, x, y, x_label, y_label, annotate=None):
        plt.scatter(
            x, y, c = self.colors
        )
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.xticks(rotation=90)
        plt.subplots_adjust(bottom=0.25)
        plt.grid()
        if annotate is not None:
            for i, user in enumerate(annotate):
                plt.annotate(user, (x[i], y[i]))
        plt.show()

    def run(self, from_csv=False):
        if not from_csv:
            self._get_all_data()
            self._save_data()
        else:
            self.data = pd.read_csv('./data.csv', header=0)
        users, avg_nw, avg_noi, tot_nw, tot_noi = self._run_statistics_on_all_users()
        self._bar_plot(users, avg_nw, 'User', 'Average number of words per article')
        self._bar_plot(users, avg_noi, 'Users', 'Average number of images in each article')
        self._bar_plot(users, tot_nw, 'User', 'Total number of words in all articles')
        self._bar_plot(users, tot_noi, 'User', 'Total number of images in all articles')
        self._plot_data(tot_nw, tot_noi, 'Total number of words', 'Total number of images', annotate=users)

if __name__ == "__main__":
    bp = BitPost()
    bp.run()