import re
import bs4
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from bs4 import BeautifulSoup

class BitPost:
    def __init__(self):
        self.base_url = 'https://bitpost.app'
        self.data = pd.DataFrame(columns=['author', 'title', 'nw', 'noi'])
        self.color_list = list(mcolors.CSS4_COLORS.items())
        self.users = self._read_user_file('users.txt')

    def _read_user_file(self, filename):
        f = open(filename, 'r')
        users = f.read().split('\n')
        users = [item.replace('\'', '').replace(',', '') for item in users[1:]]
        return users

    def _get_user_rss(self, user_name):
        print(f'------------------Making a request for the rss page of {user_name}------------------')
        user_rss_url = f'{self.base_url}/u/{user_name}/rss'
        rss_response = requests.get(user_rss_url)
        
        soup = BeautifulSoup(rss_response.content, features='html.parser')

        # Loop through each individual article
        for article in soup.findAll('item'):
            # Skip posts that are not articles
            if article.description is None:
                continue

            # Get the content form the article
            content = article.description.findAll(text=True)
            nw = 0
            noi = 0
            for item in content:
                if isinstance(item, bs4.element.NavigableString):
                    paragraphs = BeautifulSoup(item, features='html.parser').findAll('p')
                    for paragraph in paragraphs:                        
                        # Clean the contents of the paragraph and count the total number of words
                        for item in paragraph:
                            if isinstance(item, bs4.element.NavigableString):
                                words = re.findall(r'(\w+)', item)
                                nw += len(words)

                        # Get the number of images in the paragraph
                        imgs = paragraph.findAll('img')
                        if imgs is not None:
                            noi += len(imgs)

            self.data = self.data.append(
                { 
                    'author' : user_name, 
                    'title' : article.title.contents[0], 
                    'nw' : nw,
                    'noi' : noi
                }, 
                ignore_index=True
            )
    
    def _get_all_user_rss(self):
        # Make sure there are not duplicate users
        assert len(self.users) == len(set(self.users))

        self.colors = {}
        for index, user in enumerate(self.users):
            self.colors.update({ user : self.color_list[index % len(self.color_list)][0]})
            self._get_user_rss(user)

    def _run_statistics_on_all_users(self):
        users = set(self.data['author'].tolist())
        avg_nw = []
        tot_noi = []
        for item in users:
            user_nw_list = self.data[self.data['author'] == item]['nw'].tolist()
            user_noi_list = self.data[self.data['author'] == item]['noi'].tolist()

            user_avg_nw = int(sum(user_nw_list) / len(user_nw_list))
            user_tot_noi = sum(user_noi_list)

            avg_nw.append(user_avg_nw)
            tot_noi.append(user_tot_noi)
        return avg_nw, tot_noi


    def _plot_data(self, x, y, x_label, y_label):
        plt.scatter(
            x, y, c = set(self.data['author'].map(self.colors).tolist())
        )
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.show()

    def run(self):
        self._get_all_user_rss()
        avg_nw, tot_noi = self._run_statistics_on_all_users()
        self._plot_data(range(len(avg_nw)), avg_nw, 'User', 'Average number of words per article')
        self._plot_data(range(len(tot_noi)), tot_noi, 'User', 'Total number of images in all articles')
        self._plot_data(tot_noi, avg_nw, 'Total number of images in all articles', 'Average number of words per article')
        

if __name__ == "__main__":
    bp = BitPost()
    bp.run()